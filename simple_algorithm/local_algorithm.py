"""Script for executing model training on local data."""
from pathlib import Path
from typing import Dict, List

import numpy as np
from feltlabs.config import OceanConfig, TrainingConfig, parse_training_args
from feltlabs.core.cryptography import encrypt_nacl
from numpy.typing import NDArray


def get_datasets(config: OceanConfig) -> Dict[str, List[Path]]:
    """Get all dataset paths provided in Ocean's compute job environment.

    Args:
        config: FELT config object containing input folder path

    Returns:
        dictionary mapping dataset DID to list of file paths
    """
    datasets = {}
    for path in config.input_folder.iterdir():
        if path.is_dir():
            # path.name corresponds to DID of dataset
            datasets[path.name] = [p for p in path.glob("**/*") if p.is_file()]

    return datasets


def load_data(config: OceanConfig) -> NDArray:
    """Load data and return them as single numpy array.

    Args:
        config: FELT config object containing input folder path

    Returns:
        numpy array containing data from all files
    """
    datasets = get_datasets(config)

    # Here we assume that datasets are CSV format:
    data = []
    for did, files in datasets.items():
        for file in files:
            data.append(np.genfromtxt(file, delimiter=","))

    # We concatenate all numpy arrays into one
    data = np.concatenate(data, axis=0)
    return data


def main(config: TrainingConfig) -> None:
    """Main function executing the data loading, training and saving outputs

    Args:
        config: training config object provided by FELT containing all paths
    """
    # Load data as numpy array
    data = load_data(config)

    # Create model and train it
    # In this case we assume simplest situation calculating mean over last row
    # without any encryption of local results
    trained_value = np.mean(data[-1])

    # We convert trained_value (numpy.float type) to bytes
    # It can be later loaded using np.frombuffer(model_bytes)
    model_bytes = trained_value.tobytes()

    # Encrypt model using public key of aggregation (so only aggregation can decrypt it)
    # We are libsodium encryption box: https://github.com/pyca/pynacl/
    encrypted_model = encrypt_nacl(config.aggregation_key, model_bytes)

    # Save models into output folder. You have to name output file as "model"
    with open(config.output_folder / "model", "wb+") as f:
        f.write(encrypted_model)

    print("Training finished.")


if __name__ == "__main__":
    # Get config - we recommend using config parser provided by FELT Labs
    # It automatically provides all input and output paths and other settings
    config = parse_training_args()
    main(config)
