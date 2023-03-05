"""Script for publishing algorithms."""
import os
from datetime import datetime
from typing import List, Optional, Union

import requests
from brownie.network import accounts
from brownie.network.account import LocalAccount
from dotenv import load_dotenv
from feltlabs.core.cryptography import PrivateKey
from ocean_lib.example_config import get_config_dict
from ocean_lib.models.dispenser import DispenserArguments
from ocean_lib.models.fixed_rate_exchange import ExchangeArguments
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.file_objects import UrlFile
from ocean_lib.web3_internal.utils import connect_to_network


# TODO: Add option for raw algo vs url algo
# TODO: Generate the Private/Publick key and add it to entrypoint and raw algo
def publish_algo(
    name: str,
    description: str,
    entrypoint: str,
    account: LocalAccount,
    ocean: Ocean,
    urls: List[str],
    pricing_schema_args: Optional[Union[DispenserArguments, ExchangeArguments]] = None,
):
    date_created = datetime.now().isoformat()
    metadata = {
        "created": date_created,
        "updated": date_created,
        "description": description,
        "name": name,
        "type": "algorithm",
        "author": account.address[:7],
        # "rawcode": "print('Hello world')", # sadly, rawcode won't be encrypted
        "license": "CC0: PublicDomain",
        "language": "python",
        "format": "docker-image",
        "version": "0.1",
        "container": {
            "entrypoint": entrypoint,
            "image": "feltlabs/feltlabs-py",
            "tag": "dev",
            # TODO: Add auto update of checksum for latest version
            "checksum": "sha256:83d6fbf795be251887e89e65363ecc04ed34cba05e0a883c8194a950d32d066a",
        },
    }

    files = [UrlFile(url) for url in urls]
    tx_dict = {"from": account}

    # This adds the access service by default
    return ocean.assets.create_bundled(
        metadata,
        files,
        tx_dict,
        wait_for_aqua=True,
        dt_template_index=2,
        pricing_schema_args=pricing_schema_args,
    )


if __name__ == "__main__":
    load_dotenv()
    connect_to_network("polygon-test")  # mumbai is "polygon-test"
    config = get_config_dict("polygon-test")
    ocean = Ocean(config)

    account = accounts.add(os.getenv("PRIVATE_KEY"))
    print(f"Using {account.address} with balance: ", account.balance())

    aggregation_key_url = os.getenv("AGGREGATION_KEY_FILE")
    result = requests.get(aggregation_key_url, allow_redirects=True)
    aggregation_key = PrivateKey(bytes.fromhex(result.text))

    # Publish local algo
    (ALGO_data_nft, ALGO_datatoken, local_algo_ddo) = publish_algo(
        "Basic - Local Algorithm",
        "Basic algorithm calculating mean.",
        "python $ALGO --aggregation_key {bytes(aggregation_key.public_key).hex()}",
        account,
        ocean,
        urls=[
            "https://raw.githubusercontent.com/FELT-Labs/base-algorithm/main/simple_algorithm/local_algorithm.py?token=GHSAT0AAAAAABVRYWRFPSSGMI3TV4HES7OUZAEXL6Q"
        ],
    )
    print(f"Local algorithm did = '{local_algo_ddo.did}'")

    # Publish aggregation algo
    (ALGO_data_nft, ALGO_datatoken, agg_algo_ddo) = publish_algo(
        "Basic - Aggregation Algorithm",
        "Basic algorithm calculating mean - aggregation.",
        (
            "export PRIVATE_KEY= $(cat /data/transformations/1); "
            + "python $ALGO --min_models 2 --download_models --private_key {bytes(aggregation_key).hex()}"
        ),
        account,
        ocean,
        # TODO: Change url to aggregation_algorihtm.py
        urls=[
            "https://raw.githubusercontent.com/FELT-Labs/base-algorithm/main/simple_algorithm/aggregation_algorithm.py?token=GHSAT0AAAAAABVRYWRFEE5XAIOGQS6A57HMZAEXK5A",
            aggregation_key_url,
        ],
    )
    print(f"Local algorithm did = '{agg_algo_ddo.did}'")
