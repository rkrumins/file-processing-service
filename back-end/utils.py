import argparse
import yaml
import os
import time


def parse_arguments():
    parser = argparse.ArgumentParser(description="FastAPI File Upload and Processing Service.")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration YAML file (default: config.yaml)"
    )
    args = parser.parse_args()
    return args


def load_config(path: str) -> dict:
    try:
        with open(path, 'r') as stream:
            return yaml.safe_load(stream)
    except FileNotFoundError:
        print(f"INFO: Configuration file '{path}' not found. Using default values from constants.py.")
        return {}
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}. Using default values from constants.py.")
        return {}


def get_timestamped_filepath(directory: str, original_filename: str) -> str:
    timestamp = int(time.time())
    base, extension = os.path.splitext(original_filename)
    timestamped_filename = f"{timestamp}_{base}{extension}"
    file_path = os.path.join(directory, timestamped_filename)
    counter = 1
    while os.path.exists(file_path):
        timestamped_filename = f"{timestamp}_{base}_{counter}{extension}"
        file_path = os.path.join(directory, timestamped_filename)
        counter += 1
    return file_path
