import pytest
import os
import yaml
import time
from unittest.mock import patch, mock_open

# Adjust import path based on your project structure
# This assumes 'utils.py' is in the parent directory of 'tests/'
import utils


# --- Tests for parse_arguments ---

def test_parse_arguments_default():
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(config="config.yaml")
        args = utils.parse_arguments()
        assert args.config == "config.yaml"


def test_parse_arguments_custom_config():
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(config="custom_path.yaml")
        # Simulate command line arguments
        with patch('sys.argv', ['script_name', '--config', 'custom_path.yaml']):
            args = utils.parse_arguments()
            # The mock directly returns the namespace, so we check that.
            # To test the parser's behavior more deeply, you'd inspect mock_parse_args.call_args
            assert args.config == "custom_path.yaml"

# --- Tests for load_config ---

def test_load_config_success(tmp_path):
    config_content = {"key": "value", "nested": {"num": 123}}
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_content, f)

    loaded_config = utils.load_config(str(config_file))
    assert loaded_config == config_content


def test_load_config_file_not_found(capsys):
    # capsys fixture captures stdout/stderr
    config_path = "non_existent_config.yaml"
    loaded_config = utils.load_config(config_path)
    assert loaded_config == {}
    captured = capsys.readouterr()
    assert f"INFO: Configuration file '{config_path}' not found." in captured.out


def test_load_config_yaml_error(tmp_path, capsys):
    invalid_yaml_content = "key: value\n  nested: - value1" # Invalid YAML
    config_file = tmp_path / "invalid_config.yaml"
    with open(config_file, 'w') as f:
        f.write(invalid_yaml_content)

    loaded_config = utils.load_config(str(config_file))
    assert loaded_config == {}
    captured = capsys.readouterr()
    assert "Error parsing YAML file:" in captured.out


# --- Tests for get_timestamped_filepath ---

@patch('os.path.exists')
@patch('time.time')
def test_get_timestamped_filepath_no_collision(mock_time, mock_exists, tmp_path):
    mock_time.return_value = 1678886400 # Example timestamp: 2023-03-15 12:00:00 UTC
    mock_exists.return_value = False # Simulate no file exists initially

    directory = str(tmp_path)
    original_filename = "myfile.txt"
    expected_filename = "1678886400_myfile.txt"
    expected_path = os.path.join(directory, expected_filename)

    result_path = utils.get_timestamped_filepath(directory, original_filename)
    assert result_path == expected_path
    mock_exists.assert_called_once_with(expected_path)


@patch('os.path.exists')
@patch('time.time')
def test_get_timestamped_filepath_with_collision(mock_time, mock_exists, tmp_path):
    mock_time.return_value = 1678886400
    directory = str(tmp_path)
    original_filename = "report.docx"

    base_expected_filename = "1678886400_report.docx"
    first_expected_path = os.path.join(directory, base_expected_filename)

    colliding_filename_1 = "1678886400_report_1.docx"
    second_expected_path = os.path.join(directory, colliding_filename_1)

    # Simulate first path exists, second does not
    mock_exists.side_effect = [True, False]

    result_path = utils.get_timestamped_filepath(directory, original_filename)
    assert result_path == second_expected_path

    # Check os.path.exists was called for both paths
    assert mock_exists.call_count == 2
    mock_exists.assert_any_call(first_expected_path)
    mock_exists.assert_any_call(second_expected_path)


@patch('os.path.exists')
@patch('time.time')
def test_get_timestamped_filepath_multiple_collisions(mock_time, mock_exists, tmp_path):
    mock_time.return_value = 1678886400
    directory = str(tmp_path)
    original_filename = "data.csv"

    paths_to_check = [
        os.path.join(directory, f"{mock_time.return_value}_data.csv"),
        os.path.join(directory, f"{mock_time.return_value}_data_1.csv"),
        os.path.join(directory, f"{mock_time.return_value}_data_2.csv"), # This one should not exist
    ]
    # Simulate first two paths exist, third does not
    mock_exists.side_effect = [True, True, False]

    expected_path = paths_to_check[2]
    result_path = utils.get_timestamped_filepath(directory, original_filename)
    assert result_path == expected_path

    assert mock_exists.call_count == 3
    for p in paths_to_check:
        mock_exists.assert_any_call(p)

# Need to import argparse for the mock_parse_args.return_value
import argparse