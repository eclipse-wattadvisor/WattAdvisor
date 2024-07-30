""" Collection of functions to start the optization process
Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pathlib import Path

from ..data_models.input_model import InputModel
from ..data_models.optimization_results_model import OptimizationResultsModel
from . import opt_model
from .utils import config_loader
from ..data_models.config_model import ConfigModel

import pandas as pd


def _get_config(path: Path | None = None) -> ConfigModel:
    """Loads the optimization model config from a given base path.

    Parameters
    ----------
    path : None or Path, optional
        path where the config file is located, by default "config.yaml"

    Returns
    -------
    ConfigModel
        pydantic object representation of the config file
    """

    config = config_loader.load_config(path)
    return config

def run(input_model: InputModel,
        config_path: None | Path = None,
        export_detailed_results: bool = False,
        export_detailed_results_path: None | Path = None) -> OptimizationResultsModel:
    """Starts an optimization by using static input data from memory.

    Parameters
    ----------
    input_model : InputModel
    input data to build the optimization model
    config_path : None or Path
        path where the optimization model config file is located, by default "config.yaml"
    export_detailed_results : bool, optional
        whether to export detailed result time series to separate excel file, by default False
    export_detailed_results_path: None or Path, default None
        path where detailed result file should be placed

    Returns
    -------
    OptimizationResultsModel
        pydantic object representing optimization results
    """
    
    config = _get_config(config_path)

    optimization = opt_model.OptModel(input_model, config)

    #Start the optimization 
    results = optimization.run_calculation(
        export_detailed_results=export_detailed_results,
        export_detailed_results_path=export_detailed_results_path
    )

    return results