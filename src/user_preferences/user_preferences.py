from src.utilities.config_parser import load_config  # from src/utilities/__init__.py
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

config = load_config()
user_pref = config['user_preferences']
langs_cfg = config['languages']
time_cfg = config['time']

supported = langs_cfg['supported']
def_lang = langs_cfg['default']
order = user_pref['order']['order']
single_keys = set(user_pref['order']['single_choice'])
prompts = user_pref['prompt_texts']['enter_choice']
errors = user_pref['error_messages']

# Helpers for localized text
def get_text(key: str, lang: str) -> str:
    block = user_pref['questions'].get(key, {})
    return block.get(lang) or block.get(def_lang, '')

def get_opts(key: str, lang: str) -> List[Any]:
    opts = user_pref['valid_options'].get(key)
    if isinstance(opts, dict):
        return opts.get(lang) or opts.get(def_lang) or []
    return opts or []

# Generate dynamic time slots
def get_available_time_slots() -> List[str]:
    days_ahead = time_cfg.get('days_ahead', 7)
    periods = time_cfg.get('periods', [])
    date_fmt = time_cfg.get('format', {}).get('date', '%b %d')
    now = datetime.now()
    slots = []
    for d in range(days_ahead + 1):
        day = now + timedelta(days=d)
        day_str = day.strftime(date_fmt)
        for p in periods:
            slots.append(f"{day_str} {p}")
    return slots

def get_time_slots_for_day(day_key: str) -> List[str]:
    periods = time_cfg.get('periods', [])
    date_fmt = time_cfg.get('format', {}).get('date', '%b %d')
    now = datetime.now()
    if day_key == 'today':
        target = now
    elif day_key == 'tomorrow':
        target = now + timedelta(days=1)
    else:
        return get_available_time_slots()
    day_str = target.strftime(date_fmt)
    return [f"{day_str} {p}" for p in periods]

# Main prompt logic
def prompt_user() -> Dict[str, Any]:
    responses: Dict[str, Any] = {}

    # 1) Language
    print(get_text('language', def_lang))
    for idx, lng in enumerate(supported, start=1):
        print(f"{idx}. {lng}")
    while True:
        inp = input(prompts[def_lang]['single']).strip()
        if inp.isdigit() and 1 <= int(inp) <= len(supported):
            lang = supported[int(inp)-1]
            responses['language'] = lang
            break
        print(errors['invalid_selection'][def_lang])

    # 2) Remaining questions
    for key in order:
        if key == 'language':
            continue
        lang = responses['language']
        # Dynamic for pickup_time
        if key == 'pickup_time':
            # Map pickup_day to index
            pd_opts = get_opts('pickup_day', lang)
            pd = responses.get('pickup_day')
            if pd == pd_opts[0]:       # today
                opts = get_time_slots_for_day('today')
            elif pd == pd_opts[1]:     # tomorrow
                opts = get_time_slots_for_day('tomorrow')
            else:
                opts = get_available_time_slots()
            q_text = get_text(key, lang)
        else:
            q_text = get_text(key, lang)
            opts = get_opts(key, lang)

        print(f"\n{q_text}")
        if opts:
            for i, opt in enumerate(opts, start=1):
                label = opt.get('option') if isinstance(opt, dict) else opt
                print(f"{i}. {label}")
            while True:
                cfg = prompts[lang]
                prompt_str = cfg['single'] if key in single_keys else cfg['multiple']
                entry = input(prompt_str).strip()
                sels = [s.strip() for s in entry.split(',') if s.strip()]
                if key in single_keys and len(sels) > 1:
                    print(errors['single_only'][lang]); continue
                valid = True
                chosen, follow = [], {}
                for s in sels:
                    if not s.isdigit() or not (1 <= int(s) <= len(opts)):
                        valid = False; break
                    sel = opts[int(s)-1]
                    if isinstance(sel, dict):
                        chosen.append(sel['option'])
                        if 'follow_up' in sel:
                            ans = input(sel['follow_up'][0]).strip()
                            follow[sel['option']] = ans
                    else:
                        chosen.append(sel)
                if not valid:
                    print(errors['invalid_selection'][lang]); continue
                responses[key] = chosen[0] if key in single_keys else chosen
                if follow:
                    responses.setdefault('follow_ups', {})[key] = follow
                break
        else:
            responses[key] = input(q_text).strip()

    logger.info("Collected Preferences: %s", responses)
    return responses

if __name__ == '__main__':
    print(prompt_user())
