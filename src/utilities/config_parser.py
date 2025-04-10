import yaml
import os

def load_config(config_file="configs/config.yaml"):
    config_file = os.path.join(os.path.dirname(__file__), "..", "..", config_file)
    with open(config_file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print("Error loading YAML:", exc)
            config = {}
    return config

if __name__ == "__main__":
    config = load_config()
    print(config)
