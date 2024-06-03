from pathlib import Path

from . import load_YAML
from ...data_models.config_model import ConfigModel

    
def load_config(base_path: Path, filename: str = "model_config.yaml") -> ConfigModel:
    """Loads the config file for the WattAdvisor service optimization model.

    Parameters
    ----------
    base_path : Path
        Base path of the whole service
    filename : str, optional
        Filename of the config file, by default "model_config.yaml"

    Returns
    -------
    ConfigModel
        Config File represented as a pydantic object

    Raises
    ------
    FileNotFoundError
        If file `filename` cannot be found under `base_path` 
    """
    try:
        target_path = base_path.joinpath(filename)
        config_dict = load_YAML.load_yaml(target_path)
    except:
        raise FileNotFoundError(f"Config file not found, looked for at '{target_path}'.")
    
    # create pydantic object representation of the config  
    config = ConfigModel(**config_dict)

    return config