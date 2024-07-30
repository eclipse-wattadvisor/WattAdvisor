"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging
import logging.config
import sys
import time
from pathlib import Path

import pyomo.environ as pyoe
from pyomo.opt import SolverFactory, TerminationCondition

import wattadvisor.data_models.enums as enums
from ..data_models.config_model import ConfigModel
from ..data_models.input_model import InputModel
from ..data_models.optimization_results_model import OptimizationResultsModel
from .utils import load_YAML, logger_writer, config_loader
from .model_composition import compose
from .utils.results_composition import generate_results_object, write_detailed_results


class OptModel:
    def __init__(self, input_data: InputModel, config: ConfigModel):
        """Creates the basic template to calculate an optimization model. 

        Parameters
        ----------
        input_data : InputModel
            Input data request containing parametarization values of the optimization model
        config : ConfigModel
            Content of a configuration file

        Raises
        ------
        FileNotFoundError
            If parameter file not found under path set in `config.data_dependencies.parameters`
        """

        self.input_data = input_data
        self.pyomo_model = None
        self.t = None
        self.components_list = None

        self.config = config
        
        logging.config.dictConfig(self.config.logging.dict(exclude_none=True))
        self.logger = logging.getLogger("opt_model")

        try: 
            self.parameters = load_YAML.load_yaml(self.config.parameters_path)
        except:
            error_msg = "Parameter file not found."
            self.logger.critical(error_msg)
            raise FileNotFoundError(error_msg)
    
    def run_calculation(self, export_detailed_results: bool = False, export_detailed_results_path: None | Path = None) -> OptimizationResultsModel:
        """Starts the calculation of an optimization model including 
        building of the pyomo model, optimization by solver and building result output.

        Parameters
        ----------
        export_detailed_results : bool, optional
            Whether detailed result time series should be exported to an Excel file, by default False
        export_detailed_results_path : None or Path
            Path of the Excel file to write detailed results with time series to

        Returns
        -------
        OptimizationResultsModel
            Results object which is returned by the service as response
        """

        # initialize model
        self._build()

        # Transfer to optimization
        status, calculation_time = self._optimize()

        if status == enums.OptimizationStatus.SUCCESS and export_detailed_results:
            write_detailed_results(
                self.pyomo_model,
                self.components_list,
                calculation_time,
                filename=export_detailed_results_path)

        self.logger.info('Write optimization results')
        results = generate_results_object(self, self.input_data, self.components_list, status)

        self.logger.info('Optimization results written')

        return results

    def _optimize(self) -> tuple[enums.OptimizationStatus, float]:
        """Hands the built pyomo optimization model to the solver and calls the solver to solve the optmization model.

        Returns
        -------
        tuple[enums.OptimizationStatus, float]
            Status of the completed solve process and time in seconds the solver took to solve the model
        """

        solver = self.config.solver

        self.logger.info('Optimizing model')
        self.logger.debug(f'Using {solver.value} solver')

        ################### Define Solver ##########################################################
        if solver == enums.SupportedSolver.HIGHS:
            # sys.stdout = logger_writer.LoggerWriter(self.logger.debug)
            # sys.stderr = logger_writer.LoggerWriter(self.logger.error)

            slv = SolverFactory('appsi_highs')
            slv.config.stream_solver = True

            start = time.process_time()
            results = slv.solve(self.pyomo_model, tee=True)
            calculation_time = (time.process_time() - start)
        
        elif solver == enums.SupportedSolver.CBC:
            ################### CBC-Solver #############################################################
            # sys.stdout = logger_writer.LoggerWriter(self.logger.debug)
            # sys.stderr = logger_writer.LoggerWriter(self.logger.error)

            # try to call CBC solver by specifying the path to the executable (useful under Windows)
            slv = SolverFactory(solver.value, executable="cbc.exe")
            
            if isinstance(slv, pyoe.UnknownSolver):
                # try to call CBC solver by its path saved in an environment variable (useful under Linux or Mac OS)
                slv = SolverFactory(solver.value)

            #slv.options['allowableGap'] = 0.01
            slv.options['threads'] = 8
            slv.options['seconds'] = self.config.solver_timeout #1 Stunde Timeout
            slv.options['ratio'] = 1e-2
            slv.options['maxIterations'] = 99999999

            start = time.process_time()
            ################### Start Solver ###########################################################
            results = slv.solve(self.pyomo_model, tee=True)
            calculation_time = (time.process_time() - start)

        if results.solver.termination_condition in [
            TerminationCondition.infeasible,
            TerminationCondition.invalidProblem, TerminationCondition.solverFailure,
            TerminationCondition.internalSolverError, TerminationCondition.error,
            TerminationCondition.userInterrupt, TerminationCondition.resourceInterrupt]:
            self.logger.error('Solver raises Error')
            self.logger.debug(results.solver.termination_condition)
            status = enums.OptimizationStatus.ERROR
            return status, calculation_time
        
        elif results.solver.termination_condition == TerminationCondition.unbounded:
            self.logger.error('Problem is unbounded')
            self.logger.debug(results.solver.termination_condition)
            status = enums.OptimizationStatus.UNBOUNDED
            return status, calculation_time
        
        else:
            status = enums.OptimizationStatus.SUCCESS
            self.logger.info('Optimization successfully completed')
            return status, calculation_time


    def _build(self):
        """Builds the pyomo model by creating a blank ``pyomo.Concretemodel``, the time set `self.t` and by calling `model_composition.compose` function.
        """

        self.logger.info('Create model instance')

        self.pyomo_model = pyoe.ConcreteModel()
        self.t = pyoe.RangeSet(24 * 365)
        
        self.pyomo_model, self.components_list = compose(self.input_data, self.parameters, self.config, self.pyomo_model, self.t)
