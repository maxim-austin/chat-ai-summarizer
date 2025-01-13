import json

def load_config(config_path):
    """Loads channel configuration from a JSON file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load config: {e}")
