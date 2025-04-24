# AI-la-Carte - food insecurity competition

> AI-la Carte is an AI-powered platform that makes claiming free food as effortless as ordering à la carte. It intelligently matches users to nearby assistance locations that fit their dietary needs, travel range, and language preferences. With seamless proximity filtering, clear display of hours, ID or appointment requirements, and multilingual, low-literacy-friendly prompts, AI-la Carte breaks down barriers and ensures everyone can quickly find—and get—exactly the food support they need.

## prerequisites:

- install the requirements
```
pip install -r requirements.txt
```

- build up the database
```bash
python src/db_helper/sql_helper.py
```

- set up the config file in configs/config.yaml

> add your openai_api_key

```yaml
llm_config:
  LangChainRAGHelper:
    openai_api_key: ""
```


## entrypoint
- under the root directory
```bash
streamlit run streamlit_app.py
```
