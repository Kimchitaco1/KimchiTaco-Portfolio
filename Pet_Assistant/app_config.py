import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


FALLBACK_CONFIG = {
    "model_path": "vosk-es-sm",
    "logs_dir": "logs",
    "wake_words": ["gato"],
    "poll_interval_ms": 100,
    "talking_duration_ms": 2000,
    "speech": {"enabled": False},
    "ui": {"images": {}},
    "intents": {},
    "apps": {},
    "commands": {},
}


def load_config(config_path=DEFAULT_CONFIG_PATH):
    config = dict(FALLBACK_CONFIG)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = deep_update(config, json.load(config_file))

    config["model_path"] = resolve_path(config["model_path"])
    config["logs_dir"] = resolve_path(config["logs_dir"])

    for state, path in config.get("ui", {}).get("images", {}).items():
        config["ui"]["images"][state] = resolve_path(path)

    return config


def resolve_path(path):
    if not path or os.path.isabs(path):
        return path
    return os.path.join(BASE_DIR, path)


def deep_update(target, source):
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    return target
