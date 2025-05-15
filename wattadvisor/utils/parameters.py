"""Contains a class definition which is used to load
parameters of energy components from a YAML file into
a model definition.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pathlib import Path
from .load_YAML import load_yaml

class Parameters:
    _all_parameters = {}

    @classmethod
    def load_parameter_file(cls, filepath: str | Path):
        """Loads the parameter YAML file and stores its content as dict
        under the class variable ``_all_parameters`` 

        Parameters
        ----------
        filepath : str | Path
            path under which the YAML parameter file can be found
        """        


        if isinstance(filepath, str):
            filepath = Path(filepath)

        cls._all_parameters = load_yaml(filepath.resolve().as_posix())

    @classmethod
    def get_parameters(cls, component_class_name: str) -> dict:
        """Returns all parameters of a given component class name from the 
        dict in the class variable ``_all_parameters`` containing the loaded parameters. 
        If the dict has no key given by ``component_class_name``, an empty dictionary is returned.

        Parameters
        ----------
        component_class_name : str
            Name of the component class for which parameters should be gathered and returned.

        Returns
        -------
        dict
            parameters of the component class
        """        
        
        if component_class_name in cls._all_parameters:
            return cls._all_parameters[component_class_name]
        else:
            return dict()