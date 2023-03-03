import json
from pathlib import Path

import numpy as np
from feltlabs.config import AggregationConfig, TrainingConfig
from nacl.public import PrivateKey
from simple_algorithm import aggregation_algorithm, local_algorithm

# TODO: Change these according to your data
# Each element in this array should be separate dataset
TEST_DATA = [
    np.array([[0, 0, 0], [0, 1, 2]]),
    np.array([[0, 0, 0], [1, 2, 3]]),
]
EXPECTED_OUTPUT = "1.5"

# Function for creating dataset file from provided data
# TODO: Change this function according to your data
def save_data_function(data, path):
    """Takes one element from TEST_DATA and saves it to file."""
    np.savetxt(path, data, delimiter=",")


def test_simple_algorithm(tmp_path: Path):
    aggregation_key = PrivateKey.generate()
    # Configure initial folders and files
    input_folder = tmp_path / "inputs"
    input_folder_data = input_folder / "fake_did"
    output_folder = tmp_path / "outputs"
    local_models = tmp_path / "models"

    for folder in [input_folder_data, output_folder, local_models]:
        folder.mkdir(parents=True)

    custom_data_path = input_folder / "algoCustomData.json"

    # Configure training
    config = TrainingConfig(
        input_folder=input_folder,
        output_folder=output_folder,
        custom_data_path=custom_data_path,
        aggregation_key=bytes(aggregation_key.public_key),
    )

    # Run training with different datasets
    local_paths = []
    for i, test in enumerate(TEST_DATA):
        save_data_function(test, input_folder_data / "0")
        local_algorithm.main(config)

        # Move local output to extra folder and store the path
        local_path = local_models / f"model_{i}"
        local_paths.append(str(local_path))
        (config.output_folder / "model").rename(local_path)

    # Configure aggregation
    config = AggregationConfig(
        input_folder=input_folder,
        output_folder=output_folder,
        custom_data_path=custom_data_path,
        private_key=bytes(aggregation_key),
    )

    # Write file with local model urls
    with custom_data_path.open("w+") as f:
        json.dump({"model_urls": local_paths}, f)

    # Run aggregation
    aggregation_algorithm.main(config)

    # Read output and compare it with expected value
    with open(config.output_folder / "model", "r") as f:
        output = f.read().strip()

    assert output == EXPECTED_OUTPUT
