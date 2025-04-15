import src.rag_helper.temp as lc

rag_system = lc.FoodAssistanceRAG(
        openai_api_key="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",
        db_path="food_assistance.db",
        dietary_model="gpt-4o-mini",
        response_model="gpt-4o-mini"
    )
prefs = {"USER_PREFS": {
    'language': 'en', 'address': '3407 Tulne Dr, Hyasvile, MD 20783', 'pickup_day': 'today', 'pickup_time': ['Apr 12 morning', 'Apr 12 afternoon', 'Apr 12 evening', 'Apr 12 night'], 'transportation': 'yes', 'health_dietary_restrictions': 'None', 'religious_dietary_restrictions': ['Halal Meal', 'Other'], 'kitchen_access': 'Yes, so I can take raw food or tins', 'wraparound_services_requested': ['Housing', 'Government benefits', 'Financial assistance', 'Services for older adults'], 'proxy_pickup': 'yes', 'max_distance': '14', 'follow_ups': {'religious_dietary': {'Other': 'Nothing'}}
}, 
"Arcgis":[{
    "agency_ref_id": "1234567",
    "agency_name": "Food Pantry",
    "Distance": 10,
}],
}

response = rag_system.process_request(prefs)
print(response)


