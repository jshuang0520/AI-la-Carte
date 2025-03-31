import os
import yaml
from dotenv import load_dotenv
from typing import Any

# If you have a Logger module in src/logger.py, ensure it is imported correctly.
# from src.logger import Logger

class ConfigParser:
    def __init__(self, config_file="config/config.yaml"):
        # config_file path is relative to the project root
        self.config_file = config_file
        load_dotenv()  # Load environment variables from .env file if present
        self.config = self._load_and_override_config()

    def _load_and_override_config(self) -> Any:
        # Load the base YAML config template
        with open(self.config_file, "r") as f:
            config = yaml.safe_load(f)
        
        # Recursively override config values with environment variables if present
        def override(cfg, prefix=""):
            for key, value in cfg.items():
                # Create the environment variable name (e.g., "db.path" -> "DB_PATH")
                env_key = f"{prefix}{key}".upper()
                if isinstance(value, dict):
                    cfg[key] = override(value, prefix=f"{env_key}_")
                else:
                    env_val = os.getenv(env_key)
                    if env_val is not None:
                        if isinstance(value, bool):
                            cfg[key] = env_val.lower() in ["true", "1", "yes"]
                        elif isinstance(value, int):
                            try:
                                cfg[key] = int(env_val)
                            except ValueError:
                                cfg[key] = env_val
                        elif isinstance(value, float):
                            try:
                                cfg[key] = float(env_val)
                            except ValueError:
                                cfg[key] = env_val
                        else:
                            cfg[key] = env_val
            return cfg

        return override(config)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value using dot notation (e.g., 'db.path')."""
        keys = key.split(".")
        cfg = self.config
        for k in keys:
            if isinstance(cfg, dict) and k in cfg:
                cfg = cfg[k]
            else:
                return default
        return cfg

    def as_dict(self) -> Any:
        return self.config

# For debugging or testing
if __name__ == "__main__":
    parser = ConfigParser()
    print(parser.as_dict())
