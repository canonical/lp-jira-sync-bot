import yaml
import base64
import copy
from typing import Any, Optional


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

def decode_base64_yaml(value: Optional[str]) -> Any:
    if value is None or value == "":
        return None

    try:
        raw = base64.b64decode(value.encode("utf-8"), validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64 input: {e}")

    try:
        text = raw.decode("utf-8", errors="strict")
    except Exception as e:
        raise ValueError(f"Invalid UTF-8 in decoded data: {e}")

    try:
        return yaml.safe_load(text)
    except Exception as e:
        raise ValueError(f"Invalid YAML content: {e}")

def merge_project_config(global_config: Optional[dict], yaml_param: Optional[str]) -> Optional[dict]:
    base = copy.deepcopy(global_config.get('sync') or {})
    if yaml_param:
        try:
            yaml_data = decode_base64_yaml(yaml_param)
            if isinstance(yaml_data, dict) and isinstance(yaml_data.get('sync'), dict):
                base.update(yaml_data['sync'])
        except Exception as e:
                raise ValueError(f"Invalid base64 YAML in 'yaml' query parameter: {e}")

    return base