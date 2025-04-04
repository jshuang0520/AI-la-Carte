import yaml


def load_config(config_file="config/config.yaml"):
    with open(config_file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print("Error loading YAML:", exc)
            config = {}
    return config

# For debugging or quick testing:
if __name__ == "__main__":
    config = load_config()
    print(config.get("languages", {}).get("supported"))
