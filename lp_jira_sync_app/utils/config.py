import logging
import os
import yaml
import base64
import copy
from typing import Any, Optional

# Allow overriding the config path via environment in docker-compose file
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")

def define_logger():
    """Define logger to output to the file and to STDOUT."""
    log = logging.getLogger("lp-jira-sync-bot")
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s (%(levelname)s) %(message)s", datefmt="%d.%m.%Y %H:%M:%S"
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    return log


def load_config(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Config file not found at \"{path}\".")
        return {}
    except Exception as e:
        print(f"Failed to read config file \"{path}\": {e}")
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

def merge_project_config(yaml_param: Optional[str]) -> Optional[dict]:
    base = copy.deepcopy(global_config.get("project") or {})
    if yaml_param:
        try:
            yaml_data = decode_base64_yaml(yaml_param)
            if isinstance(yaml_data, dict) and isinstance(yaml_data.get("project"), dict):
                base.update(yaml_data["project"])
        except Exception as e:
                raise ValueError(f"Invalid base64 YAML in \"yaml\" query parameter: {e}")

    return base

# Load configuration
global_config = load_config(CONFIG_PATH)
logger = define_logger()