import streamlit as st
import yaml
import os
from datetime import datetime, timedelta

# Load configuration
def load_config():
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'configs', 'config.yaml')
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()
user_pref_cfg = config['user_preferences']
langs = config['languages']['supported']
def_lang = config['languages']['default']
time_cfg = config['time']

# Helpers for localized text and options

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

# Time slot generation

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
    if opts:
        if key in user_pref_cfg['order']['single_choice']:
            val = st.radio(
                label="",
                options=opts,
                key=f"{key}_radio"
            )
        else:
            val = st.multiselect(
                label="",
                options=opts,
                key=f"{key}_multiselect"
            )
    else:
        val = st.text_input(
            label="",
            key=f"{key}_text"
        )
    # Handle follow-ups for dict-options
    follow_data = {}
    if isinstance(val, list):
        for opt in val:
            # Find dict definition
            for item in get_opts(key, lang):
                if isinstance(item, dict) and item['option'] == opt and 'follow_up' in item:
                    prompt = item['follow_up'][0]
                    ans = st.text_input(
                        prompt,
                        key=f"{key}_{opt}_followup"
                    )
                    follow_data[opt] = ans
    elif isinstance(val, str):
        # check for single-choice dict
        for item in get_opts(key, lang):
            if isinstance(item, dict) and item['option'] == val and 'follow_up' in item:
                prompt = item['follow_up'][0]
                ans = st.text_input(
                    prompt,
                    key=f"{key}_{val}_followup"
                )
                follow_data[val] = ans
    # Save response
    responses[key] = val
    if follow_data:
        responses.setdefault('follow_ups', {})[key] = follow_data

# 3) Submit
if st.button("Submit", key='submit_button'):
    st.write("## Collected Preferences")
    st.json(responses)
    # Here you could call your main workflow, e.g.:  
    # from mains.poc_workflow import run_workflow  
    # results = run_workflow(responses)  
    # st.write(results)
