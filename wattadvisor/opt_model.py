"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging
import time
from pathlib import Path

import pyomo.environ as pyoe
from pyomo.opt import SolverFactory, TerminationCondition

from .data_models.enums import SupportedSolver, OptimizationStatus
from .data_models.optimization_results_model import OptimizationResults
from .model_composition import compose
from .components.component import Component
from .utils.results_composition import generate_results_object, write_detailed_results


logging.basicConfig(
    level=logging.INFO,  # at least INFO-Level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format with time stamp
)
logger = logging.getLogger()


class OptModel:
    def __init__(self, input_components: list[Component]):
        """Creates the basic template to calculate an optimization model.

        Parameters
        ----------
        input_components : list[Component]
            Input data request containing parametarization values of the optimization model
        """

        self.input_components = input_components
        self.pyomo_model = None
        self.t = None
        self.components_list = None

    def run_calculation(
        self,
        export_detailed_results: bool = False,
        export_detailed_results_path: None | Path = None,
        use_solver: SupportedSolver = SupportedSolver.HIGHS,
        solver_executable: str | None = None,
    ) -> OptimizationResults:
        """Starts the calculation of an optimization model including
        building of the pyomo model, solution by calling solver and building result output.

        Parameters
        ----------
        export_detailed_results : bool, optional
            Whether detailed result time series should be exported to an Excel file, by default False
        export_detailed_results_path : None | Path, optional
            Path of the Excel file to write detailed results with time series to, by default None
        use_solver : SupportedSolver, optional
            Solver to be used for the optimization, by default SupportedSolver.HIGHS
        solver_executable : str | None, optional
            Path of the solver's executable, by default None

        Returns
        -------
        OptimizationResults
            Results object which is returned by the service as response
        """

        # initialize model
        self._build()

        # Transfer to optimization
        status, calculation_time = self._optimize(
            solver=use_solver, solver_executable=solver_executable
        )

        if status == OptimizationStatus.SUCCESS and export_detailed_results:
            write_detailed_results(
                self.pyomo_model,
                self.input_components,
                calculation_time,
                filename=export_detailed_results_path,
            )

        logger.info("Write optimization results")
        results = generate_results_object(
            self,
            self.input_components,
            status,
            use_solver,
            solver_executable=solver_executable,
        )

        logger.info("Optimization results written")

        return results

    def _optimize(
        self,
        solver: SupportedSolver = SupportedSolver.HIGHS,
        solver_executable: str | None = None,
        solver_timeout: float = 3600,
    ) -> tuple[OptimizationStatus, float]:
        """Hands the built pyomo optimization model to the solver and calls the solver to solve the optmization model.

        Parameters
        ----------
        solver : SupportedSolver, optional
            Solver to be used by the optimization, by default SupportedSolver.HIGHS
        solver_executable : str | None, optional
            Path of the solver's executable, by default None
        solver_timeout : float, optional
            Time in seconds after which the optimization should be aborted if no result was found before, by default 3600

        Returns
        -------
        tuple[OptimizationStatus, float]
            Status of the completed solve process and time in seconds the solver took to solve the model
        """        

        logger.info("Optimizing model")
        logger.debug(f"Using {solver.value} solver")

        ################### Define Solver ##########################################################
        if solver == SupportedSolver.HIGHS:

            slv = SolverFactory("appsi_highs")
            slv.config.stream_solver = True

            start = time.process_time()
            results = slv.solve(self.pyomo_model)
            calculation_time = time.process_time() - start

        elif solver == SupportedSolver.CBC:
            ################### CBC-Solver #############################################################

            # try to call CBC solver by specifying the path to the executable (useful under Windows)
            slv = SolverFactory(solver.value, executable=solver_executable)

            if isinstance(slv, pyoe.UnknownSolver):
                # try to call CBC solver by its path saved in an environment variable (useful under Linux or Mac OS)
                slv = SolverFactory(solver.value)

            # slv.options['allowableGap'] = 0.01
            slv.options["threads"] = 8
            slv.options["seconds"] = solver_timeout  # 1 Stunde Timeout
            slv.options["ratio"] = 1e-2
            slv.options["maxIterations"] = 99999999

            start = time.process_time()
            ################### Start Solver ###########################################################
            results = slv.solve(self.pyomo_model, tee=True)
            calculation_time = time.process_time() - start

        elif solver == SupportedSolver.GUROBI:
            slv = SolverFactory(solver.value, executable=solver_executable)

            if isinstance(slv, pyoe.UnknownSolver):
                # try to call CBC solver by its path saved in an environment variable (useful under Linux or Mac OS)
                slv = SolverFactory(solver.value)

            start = time.process_time()
            ################### Start Solver ###########################################################
            results = slv.solve(self.pyomo_model, tee=True)
            calculation_time = time.process_time() - start

        if results.solver.termination_condition in [
            TerminationCondition.infeasible,
            TerminationCondition.invalidProblem,
            TerminationCondition.solverFailure,
            TerminationCondition.internalSolverError,
            TerminationCondition.error,
            TerminationCondition.userInterrupt,
            TerminationCondition.resourceInterrupt,
            TerminationCondition.infeasibleOrUnbounded,
        ]:
            logger.error("Solver raises Error")
            logger.debug(results.solver.termination_condition)
            status = OptimizationStatus.ERROR
            return status, calculation_time

        elif results.solver.termination_condition == TerminationCondition.unbounded:
            logger.error("Problem is unbounded")
            logger.debug(results.solver.termination_condition)
            status = OptimizationStatus.UNBOUNDED
            return status, calculation_time

        else:
            status = OptimizationStatus.SUCCESS
            logger.info("Optimization successfully completed")
            return status, calculation_time

    def _build(self) -> None:
        """Builds the pyomo model by creating a blank ``pyomo.Concretemodel``, the time set `self.t` and by calling `model_composition.compose` function."""

        logger.info("Create model instance")

        self.pyomo_model = pyoe.ConcreteModel()
        self.t = pyoe.RangeSet(24 * 365)

        self.pyomo_model = compose(self.input_components, self.pyomo_model, self.t)
