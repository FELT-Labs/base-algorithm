"""Script for aggregating results from local trainings."""
import json
from pathlib import Path
from typing import Any, List

import numpy as np
import requests
from feltlabs.config import AggregationConfig, parse_aggregation_args
from feltlabs.core.cryptography import decrypt_nacl


def load_local_models(config: AggregationConfig) -> List[bytes]:
    """Load results from local algorithm (models) for aggregation.
    The model URLs are provided in custom algorithm data file. This will usually be
    URLs to models from local trainings. For testing purposes this can be local paths.

    Args:
        config: config object containing path to custom data and private key

    Returns:
        list of bytes - local results loaded as bytes
    """
    with config.custom_data_path.open("r") as f:
        conf = json.load(f)

    data_array = []
    for url in conf["model_urls"]:
        if config.download_models:
            res = requests.get(url)
            data_array.append(res.content)
        else:
            data_array.append(Path(url).read_bytes())

    return [decrypt_nacl(config.private_key, val) for val in data_array]


def main(config: AggregationConfig):
    """Main function executing the local result loading, aggregation and saving outputs.

    Args:
        config: training config object provided by FELT containing all paths
    """
    # Load data as numpy array
    local_models = load_local_models(config)

    # Run the aggregation algorithm
    models = [np.frombuffer(m) for m in local_models]
    final_value = np.mean(models)

    # Get final output values
    model_bytes = bytes(str(final_value), "utf-8")

    # Save models into output folder. You have to name output file as "model"
    with open(config.output_folder / "model", "wb+") as f:
        f.write(model_bytes)

    print("Training finished.")


if __name__ == "__main__":
    # Get config - we recommend using config parser provided by FELT Labs
    # It automatically provides all input and output paths
    config = parse_aggregation_args()
    main(config)
