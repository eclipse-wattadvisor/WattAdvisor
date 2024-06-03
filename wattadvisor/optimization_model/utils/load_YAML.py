import yaml


def load_yaml(path: str) -> dict:
    """Function to load data from a YAML file into a python dictionary

    Parameters
    ----------
    path : str
        path to the YAML file

    Returns
    -------
    dict
        data from YAML file
    """

    with open(path, "r") as file:
        yaml_dict = yaml.safe_load(file)

    return yaml_dict