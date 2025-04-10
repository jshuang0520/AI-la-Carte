import os
import logging
from typing import Dict, Any, List, Optional

from src.db_helper import DBHelper
from src.translate_helper import TranslateHelper

import numpy as np
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
# from langchain_core.retrievers import VectorStoreRetriever
from langchain_core.messages import SystemMessage

_LOG = logging.getLogger(__name__)


# Globals.
PROMPT_TEMPLATE = """
You are a dietary-aware food assistance system. Follow these steps:

1. **Dietary Analysis**:
{trigger_analysis}

2. **Program Matching**:
{program_rules}

3. **SQL Construction**:
- Use exact column names from: {table_info}
- Include cultural population regex matches
- Prioritize active programs

4. **Response Format**:
- Begin with dietary match explanation
- List agencies with program types
- Highlight cultural competence
- Add accessibility notes

User Query: {input}
"""

class LangChainRAGHelper:
    DIETARY_RULES = {
        'produce_focused': {
            'triggers': {'diabetic', 'hypertension', 'low sodium', 'low sugar', 'fresh produce'},
            'programs': ['Markets'],
            'cultures': 'All Cultural Populations'
        },
        'halal': {
            'triggers': {'halal'},
            'programs': ['Markets', 'Shopping Partners'],
            'cultures': ['Middle Eastern/North African']
        }
    }

    def __init__(
        self,
        openai_api_key: str,
        *,
        model_name: Optional[str] = "gpt-4-mini",
        persist_directory: Optional[str] = "chroma_data",
        temperature: Optional[float] = 0.0,
    ):
        """
        Initialize the RAG helper with LangChain components. 
        """
        os.environ["OPENAI_API_KEY"] = openai_api_key
        # Initialize components.
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.embeddings = OpenAIEmbeddings()
        self.vector_store: Optional[Chroma] = None
        self.retriever: Optional[VectorStoreRetriever] = None
        self.qa_chain = None
        # Setup chain during initialization.
        self._initialize_vector_store(persist_directory)
        self._setup_qa_chain()

    def _initialize_vector_store(self, persist_directory: str):
        """
        Initialize or load a Chroma vector store.
        """
        try:
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
            self.retriever = self.vector_store.as_retriever(k=5)
            _LOG.info("Vector store initialized successfully")
        except Exception as e:
            _LOG.error(f"Error initializing vector store: {str(e)}")
            raise

    def _create_rag_prompt_template(self) -> ChatPromptTemplate:
        """
        Create a RAG prompt template for store recommendations.
        """
        system_template = """
        You are an assistant that recommends stores based on user preferences.
        Use the following context (store information) and user preferences to make recommendations.
        Be specific about why each store matches the user's needs.
        
        Context:
        {context}
        
        User Preferences:
        {preferences}
        """
        human_template = "Based on my preferences, which stores would you recommend and why?"
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    def _setup_qa_chain(self):
        """
        Set up the QA chain with retrieval and prompt templating.
        """
        try:
            prompt_template = self._create_rag_prompt_template()
            self.qa_chain = (
                {
                    "context": self.retriever,
                    "preferences": RunnablePassthrough()
                }
                | prompt_template
                | self.llm
                | StrOutputParser()
            )
            _LOG.info("QA chain setup complete")
        except Exception as e:
            _LOG.error(f"Error setting up QA chain: {str(e)}")
            raise

    def _format_preferences(self, preferences: Dict[str, Any]) -> str:
        """
        Convert user preferences dictionary to formatted string.
        """
        return "\n".join(f"{k}: {v}" for k, v in preferences.items())
    
    def _get_contact_details(self, names: List[str]) -> List[Dict]:
        """Query SQL database for specific partner/market contacts"""
        results = []
        with self.engine.connect() as conn:
            for name in names:
                try:
                    query = text("""
                        SELECT 
                            name, 
                            "Phone" as contact_phone,
                            "Shipping Address" as address,
                            "Hours of Operation" as hours,
                            "Eligibility Requirements" as requirements
                        FROM cafb_shopping_partners_hoo
                        WHERE name LIKE :name
                        UNION
                        SELECT
                            name,
                            "Contact Phone",
                            "Market Address",
                            "Operating Hours",
                            "Service Requirements"
                        FROM cafb_markets
                        WHERE name LIKE :name
                    """)
                    result = conn.execute(query, {"name": f"%{name}%"})
                    results.extend([dict(row) for row in result])
                except Exception as e:
                    _LOG.error(f"Query failed for {name}: {str(e)}")
        return results

    def _format_response(self, raw_data: List[Dict]) -> str:
        """
        Format raw SQL results into natural language.
        """
        # Convert raw data to a structured format.
        template = """
        Convert these database entries into friendly contact information:
        {data}
        
        Include:
        - Clear headings with organization name
        - Phone number formatting
        - Address formatting with line breaks
        - Hours in simple terms
        - Requirements as bullet points
        - Translation of any technical terms
        """
        response = self.llm.invoke(template.format(data=raw_data))
        return response.content

    def _analyze_dietary_needs(self, query: str) -> dict:
        """
        Match dietary restrictions to program rules.
        """
        query_lower = []
        matched_rules = []
        if query["health_dietary"]:
            query_lower.extend(query["health_dietary"])
        if query["religious_dietary"]:
            query_lower.extend(query["religious_dietary"])
        for rule_name, rule in self.DIETARY_RULES.items():
            if any(trigger in query_lower for trigger in rule['triggers']):
            # if any(trigger in query for trigger in rule['triggers']):
                matched_rules.append(rule)
        
        return matched_rules[0] if matched_rules else None

    def _build_sql_filter(self, rules: dict) -> str:
        """
        Convert rules to SQL WHERE clauses.
        """
        filters = []
        if rules:
            programs = ", ".join(f"'{p}'" for p in rules['programs'])
            filters.append(f"associated_program IN ({programs})")
            
            if rules['cultures'] != 'All Cultural Populations':
                cultures = "|".join(rules['cultures'])
                filters.append(f"cultural_populations_served REGEXP '{cultures}'")
        return " AND ".join(filters) if filters else "1=1"

    def run_inference(self, user_input: str) -> str:
        """
        Enhanced inference with dietary rule processing.
        """
        # Analyze dietary needs.
        diet_rules = self._analyze_dietary_needs(user_input)
        # Build SQL query.
        base_query = """
        SELECT 
            name,
            contact_phone,
            address,
            hours_of_operation,
            cultural_populations_served,
            associated_program
        FROM combined_services
        WHERE {filters}
        """
        sql_filters = self._build_sql_filter(diet_rules)
        final_query = base_query.format(filters=sql_filters)
        # Execute query.
        with self.engine.connect() as conn:
            result = conn.execute(text(final_query))
            results = [dict(row) for row in result]
        # Generate natural language response.
        return self._format_guided_response(results, diet_rules)

    def _format_guided_response(self, data: list, rules: dict) -> str:
        """Generate structured response with decision explanation"""
        prompt_template = """
        You are a food assistance counselor. Explain these results:
        
        Dietary Analysis: {diet_analysis}
        
        Matching Services:
        {services}
        
        Format as:
        1. **Dietary Match**: Explain rule activation
        2. **Recommended Services**: List with icons
        3. **Cultural Considerations**: Explain population matches
        4. **Next Steps**: Actionable instructions
        """
        diet_analysis = self._explain_rules(rules) if rules else "No specific dietary restrictions identified"
        services_str = "\n".join([f"- {s['name']} ({s['associated_program']})" for s in data])
        
        return self.llm.invoke(prompt_template.format(
            diet_analysis=diet_analysis,
            services=services_str
        )).content

    def _explain_rules(self, rules: dict) -> str:
        """
        Generate natural language explanation of active rules.
        """
        explanation = "Based on your dietary needs:\n"
        explanation += f"- Program Focus: {', '.join(rules['programs'])}\n"
        explanation += f"- Cultural Match: {', '.join(rules['cultures']) if isinstance(rules['cultures'], list) else rules['cultures']}"
        return explanation