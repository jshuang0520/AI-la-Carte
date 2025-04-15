import json
import os
import sqlite3
import re

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from langchain.agents import AgentExecutor, create_structured_chat_agent, create_tool_calling_agent
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text
from langchain.agents import Tool  

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DietaryFilterGenerator:
    DIETARY_RULES = {
        'health_restrictions': {
            # Convert sets to lists for JSON serialization
            'triggers': ['diabetic', 'hypertension', 'low sodium', 'low sugar', 'fresh produce'],
            'agency_type': ['Markets'],
            'cultures_served': 'All Cultural Populations'
        },
        'religious_restrictions': {
            'triggers': ['halal'],
            'agency_type': ['Markets', 'Shopping Partners'],
            'cultures_served': 'Middle Eastern/North African'
        },
        "no_dietary_needs": {
            'triggers': [],
            'agency_type': [],
            'cultures_served': ''
        }
    }

    # DietaryFilterGenerator's SQL_GEN_TEMPLATE (updated example and instructions)
    SQL_GEN_TEMPLATE = """Analyze user preferences and dietary rules to create SQL WHERE clauses.
    DIETARY_RULES:
    {dietary_rules}

    USER PREFERENCES:
    {user_prefs}

    Instructions:
    1. Identify applicable dietary restrictions from preferences
    2. Map to corresponding rules using these column names:
    - agency_type (values: Markets, Shopping Partners)
    - 'Cultural Populations Served' (text field)
    3. For each matched rule, create conditions with:
    - agency_type IN (comma-separated quoted values)
    - 'Cultural Populations Served' LIKE '%rule_culture%'
    - If nothing is present, skip this where clause
    4. Combine conditions with AND between rules
    5. Generate only the conditions without WHERE keyword

    Example response for Halal:
    (agency_type IN ('Markets', 'Shopping Partners') 
    AND 'Cultural Populations Served' LIKE '%Middle Eastern/North African%')

    Now generate conditions for these preferences:"""


    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0
    ):
        self.sql_gen_prompt = PromptTemplate(
            input_variables=["dietary_rules", "user_prefs"],
            template=self.SQL_GEN_TEMPLATE
        )
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.llm = ChatOpenAI(
            model=model_name, 
            temperature=temperature
        )


    def generate_dietary_filters(self, user_prefs: Dict) -> str:
        try:
            chain = self.sql_gen_prompt | self.llm
            result = chain.invoke({
                "dietary_rules": json.dumps(self.DIETARY_RULES, indent=2),
                "user_prefs": json.dumps(user_prefs, indent=2)
            })
            
            # Extract only SQL code from response
            sql_match = re.search(r"```sql\n(.*?)\n```", result.content, re.DOTALL)
            if sql_match:
                return sql_match.group(1).strip()
            return ""  # Fallback to empty filter
            
        except Exception as e:
            logger.error(f"Error generating dietary filters: {str(e)}")
            return ""

class QueryBuilder:
    @staticmethod
    def build_query(arcgis_agencies: List[Dict], dietary_where: str) -> str:
        # Extract and sanitize agency IDs and agency names from the ArcGIS dataset.
        # Remove any single quotes from the data to avoid conflicts.
        agency_ids = [str(a.get("Agency ID", "")).replace("'", "") for a in arcgis_agencies]
        agency_names = [a.get("Agency Name", "").replace("'", "") for a in arcgis_agencies]

        # Build a comma-separated string of agency IDs, each enclosed in single quotes.
        if agency_ids:
            id_str = ','.join(f"'{agency_id}'" for agency_id in agency_ids)
            # If your database column name is exactly "Agency ID" (with a space), wrap it in double quotes:
            id_clause = f"\"Agency ID\" IN ({id_str})"
        else:
            id_clause = "1=0"

        # Similarly, build a clause for agency names.
        if agency_names:
            name_str = ','.join(f"'{name}'" for name in agency_names)
            name_clause = f"\"Agency Name\" IN ({name_str})"
        else:
            name_clause = "1=0"

        # Sanitize dietary_where clause, removing dangerous characters.
        sanitized_where = re.sub(
            r"[;'\"]|(--)|(/\*[\w\W]*?\*/)",
            "",
            dietary_where,
            flags=re.IGNORECASE
        ) if dietary_where else ""

        base_query = f"""
SELECT * 
FROM combined_data
WHERE (
    {id_clause} 
    OR {name_clause}
)"""
        if sanitized_where:
            base_query += f" AND ({sanitized_where})"
        return base_query + " LIMIT 50"


class ResponseGenerator:
    RESPONSE_TEMPLATE = """You are a food assistance coordinator. Available tools: {tools} [{tool_names}]
    
    Generate responses in {language} using this structure:
    {response_structure}"""

    RESPONSE_STRUCTURE = """For each agency in {query_results}:
    **Option [number]:**
    - Agency Name: [exact value]
    - Address: [Shipping Address]
    - Distance: [convert Distance to miles if number, else 'Unknown']
    - Operating Hours: [Day or Week] [Starting Time]-[Ending Time]
    - Frequency: [Frequency]
    - Food Format: [Food Format or 'Not specified']
    - Choice Options: [Choice Options or 'Not specified']
    - Distribution Models: [Distribution Models or 'Not specified']
    - Phone: [Phone or 'Not available']
    - URL: [URL or 'Not available']
    - Appointment Only: [By Appointment Only]
    - Additional Notes: [Additional Note on Hours of Operations or 'None']
    - Wraparound Services: [Wraparound Service]
    - Note: Compare {user_services} with agency services. List missing as "Missing requested services: [services]"
    
    Requirements:
    1. Maintain original agency ordering
    2. Use markdown bold for section headers
    3. Never hallucinate fields - use 'Not available' for missing data
    4. Convert times to HH:MM format
    5. List EXACTLY these fields in order"""

    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4",
        temperature: float = 0.1
    ):
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        self.tools = []

        # self.tools = [
        #     Tool(
        #         name="Result Formatter",
        #         func=self.format_sql_results_tool,
        #         description="Formats SQL results into structured data"
        #     )
        # ]

    def create_response_agent(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.RESPONSE_TEMPLATE),
            ("human", "User preferences:\n{user_prefs}\n\nAgency data:\n{query_results}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        return AgentExecutor(
            agent=create_tool_calling_agent(
                self.llm,
                tools=self.tools,
                prompt=prompt
            ),
            tools=self.tools,
            verbose=True
        )


    def generate_final_response(self, query_results: List[Dict], user_prefs: Dict) -> str:
        response_structure = self.RESPONSE_STRUCTURE
        try:
            response_agent = self.create_response_agent()
            return response_agent.invoke({
                # "tool_names": "Result Formatter",
                # "tools": self.tools,
                "response_structure": response_structure,
                "language": user_prefs.get("language", "English"),
                "query_results": query_results,
                "user_services": user_prefs.get("services", []),
                "user_prefs": json.dumps(user_prefs, indent=2)
            })["output"]
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return "Could not generate response due to an internal error."

    @staticmethod
    def format_sql_results_tool(query_results: List[Dict]) -> List[Dict]:
        """Converts raw SQL results to structured JSON with consistent fields"""
        formatted = []
        for row in query_results:
            formatted.append({
                "Agency Name": row.get("Agency_Name", ""),
                "Shipping Address": row.get("Shipping_Address", ""),
                "Distance": f"{row['Distance']} miles" if isinstance(row.get("Distance"), (int, float)) else "Unknown",
                "Day or Week": row.get("Day_or_Week", ""),
                "Starting Time": ResponseGenerator.format_time(row.get("Starting_Time")),
                "Ending Time": ResponseGenerator.format_time(row.get("Ending_Time")),
                "Frequency": row.get("Frequency", "Not specified"),
                "Food Format": row.get("Food_Format", "Not specified"),
                "Choice Options": row.get("Choice_Options", "Not specified"),
                "Distribution Models": row.get("Distribution_Models", "Not specified"),
                "Phone": row.get("Phone", "Not available"),
                "URL": row.get("URL", "Not available"),
                "By Appointment Only": "Yes" if row.get("By_Appointment_Only") else "No",
                "Additional Note on Hours of Operations": row.get("Additional_Note_on_Hours_of_Operations", "None"),
                "Wraparound Service": ResponseGenerator.parse_services(row.get("Wraparound_Service"))
            })
        return formatted

    @staticmethod
    def parse_services(service_str: Optional[str]) -> List[str]:
        return [s.strip() for s in service_str.split(";")] if service_str else []

    @staticmethod
    def format_time(time_str: Optional[str]) -> str:
        try:
            return datetime.strptime(time_str, "%H:%M:%S").strftime("%H:%M")
        except (ValueError, TypeError):
            return time_str or "Unknown"

class FoodAssistanceRAG:
    def __init__(
        self,
        openai_api_key: str,
        db_path: str = "combined_data.db",
        dietary_model: str = "gpt-4o-mini",
        response_model: str = "gpt-4o-mini",
        dietary_temperature: float = 0.0,
        response_temperature: float = 0.1
    ):
        db_path = os.path.expanduser(db_path)
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.filter_gen = DietaryFilterGenerator(
            openai_api_key=openai_api_key,
            model_name=dietary_model,
            temperature=dietary_temperature
        )
        self.response_gen = ResponseGenerator(
            openai_api_key=openai_api_key,
            model_name=response_model,
            temperature=response_temperature
        )
        self.query_builder = QueryBuilder()

    def process_request(self, input_info: Dict) -> str:
        try:
            # Generate dietary filters
            dietary_where = self.filter_gen.generate_dietary_filters(
                input_info["USER_PREFS"]
            )
            
            # Build complete query
            full_query = self.query_builder.build_query(
                input_info["Arcgis"],
                dietary_where
            )
            logger.info(f"Executing query: {full_query}")
            
            # Execute query
            query_results = self.execute_query(full_query)
            
            # Generate final response
            return self.response_gen.generate_final_response(
                query_results=query_results,
                user_prefs=input_info["USER_PREFS"]
            )
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return "An error occurred while processing your request."

    def execute_query(self, query: str) -> List[Dict]:
        try:
            # Remove any remaining markdown
            clean_query = re.sub(r"```sql|```", "", query)
            
            with self.engine.connect() as connection:
                if not connection.dialect.has_table(connection, "combined_data"):
                    raise ValueError("combined_data table does not exist")
                result = connection.execute(text(clean_query))
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return []
