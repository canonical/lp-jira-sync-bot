import yaml


def load_config(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Config file not found at '{path}'.")
        return {}
    except Exception as e:
        print(f"Failed to read config file '{path}': {e}")
        return {}
