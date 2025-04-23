import streamlit as st
import yaml
import os
from datetime import datetime, timedelta
import logging


from src.geo_helper.geo_helper import GeoHelper
import src.rag_helper.langchain as lc


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ########################################################################
# # POC Workflow 
# ########################################################################


def filter_by_distance(
        user_prefs, 
        config,
        limit=100
    ):
    max_distance = float(user_prefs.get('max_distance'))
    logger.info("Filtering by distance using max_distance: %s", max_distance)
    geo_helper = GeoHelper()
    distance_data = geo_helper.find_nearby_food_assistance(
        user_prefs["address"], 
        radius_miles=max(max_distance, config["distance"]["max_threshold"]),
        limit=limit
    )
    logger.info(
        "First three rows of distance data retrieved: %s", 
        distance_data[:3]
    )
    return distance_data


def rag_search(user_prefs, distance_data, config):
    logger.info("Performing RAG search/comparison with user preferences...")
    logger.info("Running inference...")
    INPUT_INFO = {"USER_PREFS": user_prefs, "Arcgis": distance_data}
    rag_system = lc.FoodAssistanceRAG(
        openai_api_key=config["llm_config"]["LangChainRAGHelper"]["openai_api_key"], 
        db_path="data/cafb.db",
        dietary_model="gpt-4o-mini",
        response_model="gpt-4o-mini"
    )
    response = rag_system.process_request(INPUT_INFO)
    return response


# ########################################################################
# Helpers for localized text and options
# ########################################################################


def get_q(key, lang):
    qblock = user_pref_cfg['questions'].get(key, {})
    return qblock.get(lang, qblock.get(def_lang, ''))

def get_opts(key, lang):
    opts = user_pref_cfg['valid_options'].get(key)
    if isinstance(opts, dict):
        # Return list, default to empty list if None
        return opts.get(lang) or opts.get(def_lang) or []
    # For non-dict (list or None)
    return opts or []


# ########################################################################
# Time slot generation
# ########################################################################


def get_available_time_slots():
    days = time_cfg.get('days_ahead', 7)
    periods = time_cfg.get('periods', [])
    date_fmt = time_cfg.get('format', {}).get('date', '%b %d')
    now = datetime.now()
    slots = []
    for d in range(days + 1):
        day = now + timedelta(days=d)
        ds = day.strftime(date_fmt)
        for p in periods:
            slots.append(f"{ds} {p}")
    return slots


def get_time_slots_for_day(day_key):
    periods = time_cfg.get('periods', [])
    date_fmt = time_cfg.get('format', {}).get('date', '%b %d')
    now = datetime.now()
    if day_key == 'today':
        target = now
    elif day_key == 'tomorrow':
        target = now + timedelta(days=1)
    else:
        return get_available_time_slots()
    ds = target.strftime(date_fmt)
    return [f"{ds} {p}" for p in periods]


# ########################################################################
# Load configuration
# ########################################################################


def load_config():
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'configs', 'config.yaml')
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_user_preferences(responses):
    for key in responses:
        if isinstance(responses[key], dict):
            responses[key] = [k for k, v in responses[key].items() if v]
    return responses

# Load configuration
config = load_config()
user_pref_cfg = config['user_preferences']
langs = config['languages']['supported']
def_lang = config['languages']['default']
time_cfg = config['time']


# Streamlit App
st.title("AI‑la‑Carte: Food Assistance Preferences (Streamlit)")

# 1) Language selection
lang = st.radio(
    get_q('language', def_lang),
    options=langs,
    index=langs.index(def_lang),
    key='language_radio'
)
responses = {'language': lang}

# 2) Iterate questions
for key in user_pref_cfg['order']['order']:
    if key == 'language':
        continue
    st.markdown(f"### {get_q(key, lang)}")
    # Determine options
    if key == 'pickup_time':
        pd = responses.get('pickup_day')
        pd_opts = get_opts('pickup_day', lang)
        if pd == pd_opts[0]:            # today
            opts = get_time_slots_for_day('today')
        elif pd == pd_opts[1]:         # tomorrow
            opts = get_time_slots_for_day('tomorrow')
        else:
            opts = get_available_time_slots()
    else:
        opts = get_opts(key, lang)
    # Render appropriate widget
    key_data = {}       # For saving responses
    if opts:
        if key in user_pref_cfg['order']['single_choice']:
            val = st.radio(
                label="",
                options=opts,
                key=f"{key}_radio"
            )
            key_data = val      # For single-choice, save the selected option directly
        else:
            non_dict_options = [opt for opt in opts if not isinstance(opt, dict)]
            dict_options = [opt for opt in opts if isinstance(opt, dict)]
            for opt in non_dict_options:
                val = st.checkbox(
                    label=opt,
                    key=f"{key}_{opt}_select"
                    )
                key_data[opt] = val     # Save true or false for each option
            for opt in dict_options:
                val = st.checkbox(
                    label=opt["option"],
                    key=f"{key}_{opt['option']}_checkbox"
                )
                key_data[opt['option']] = val   # Save true or false for each option
                if val:
                    # Handle dict options with follow-ups
                    if 'follow_up' in opt:
                        prompt = opt['follow_up'][0]
                        ans = st.text_input(
                            prompt,
                            key=f"{key}_{opt['option']}_followup"
                        )
                        # Save response with follow-up
                        responses.setdefault('follow_ups', {}).setdefault(key, {})[opt['option']] = ans
    else:
        val = st.text_input(
            label="",
            key=f"{key}_text"
        )
        key_data = val

    responses[key] = key_data

# 3) Submit
if st.button("Submit", key='submit_button'):
    # st.write("## Collected Preferences")
    # st.json(responses)
    with st.spinner("Processing..."):
        try:
            # preparation
            # workflow
            user_prefs = get_user_preferences(responses)
            # st.write("## User Preferences")
            # st.json(user_prefs)
            distance_data = filter_by_distance(
                user_prefs, 
                config=config,
                limit=100,
            )
            results = rag_search(user_prefs, distance_data, config=config)
            logger.info("Final Results: %s", results)
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}")
            raise
        st.write(results)
    # Here you could call your main workflow, e.g.:  
    # from mains.poc_workflow import run_workflow  
    # results = run_workflow(responses)  
    # st.write(results)
