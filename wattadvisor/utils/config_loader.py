"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pathlib import Path

from . import load_YAML
from ..data_models.config_model import ConfigModel

    
def load_config(path: Path | None = None) -> ConfigModel:
    """Loads the config file for the WattAdvisor service optimization model.

    Parameters
    ----------
    path : None or Path, optional
        path where the config file is located, by default "./wattadvisor/optimization_model/model_config.yaml"

    Returns
    -------
    ConfigModel
        Config File represented as a pydantic object

    Raises
    ------
    FileNotFoundError
        If file cannot be found under `path` 
    """

    if path is None:
        path = Path().absolute().joinpath("wattadvisor/optimization_model/model_config.yaml")

    elif isinstance(path, str):
        path = Path(path)

    if path.suffix not in [".yaml", "yml"]:
        raise ValueError("Config file should be '.yaml' or '.yml' type.")

    config_dict = load_YAML.load_yaml(path)
    
    # create pydantic object representation of the config  
    config = ConfigModel(**config_dict)

    return config