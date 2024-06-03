""" Collection of functions to start the optization process

"""

from pathlib import Path

from ..data_models.input_model import InputModel
from ..data_models.optimization_results_model import OptimizationResultsModel
from ..optimization_model import opt_model
from ..optimization_model.utils import config_loader
from ..data_models.config_model import ConfigModel


def _get_config(base_path: str = "wattadvisor/optimization_model") -> ConfigModel:
    """Loads the optimization model config from a given base path.

    Parameters
    ----------
    base_path : str, optional
        path to look for the config file, by default "wattadvisor/optimization_model"

    Returns
    -------
    ConfigModel
        pydantic object representation of the config file
    """
    config = config_loader.load_config(Path().absolute().joinpath(base_path))
    return config

def _run(config: ConfigModel, inputdata: InputModel, export: bool = False) -> OptimizationResultsModel:
    """Starts an optimization.

    Parameters
    ----------
    config : ConfigModel
        optimization model config object
    inputdata : InputModel
        input data to build the optimization model
    export : bool, optional
        whether to export detailed result time series to separate excel file, by default False

    Returns
    -------
    OptimizationResultsModel
        pydantic object representing optimization results
    """
    
    optimization = opt_model.OptModel(inputdata, config)

    #Start the optimization 
    results = optimization.run_calculation(export=export)

    return results

def run_direct(inputdata: InputModel, export: bool = False) -> OptimizationResultsModel:
    """Starts the optimization by using static input data from memory. 

    Parameters
    ----------
    inputdata : InputModel
        input data to build the optimization model
    export : bool, optional
        whether to export detailed result time series to separate excel file, by default False

    Returns
    -------
    OptimizationResultsModel
        pydantic object representing optimization results
    """
    
    config = _get_config()
    results = _run(config, inputdata, export=export)

    return results