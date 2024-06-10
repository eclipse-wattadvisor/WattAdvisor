# About Eclipse WattAdvisor

Eclipse WattAdvisor provides a Python library that consists of several functions and classes to build and solve a linear optimization model based on certain input data and parameters. The optimization model represents a local energy system composed of different energy components to produce, store, or transform energy.

## 1 Input data

Input data can contain information about the following aspects of the local energy system:

- geographical location
- annual energy demands per energy type
- Installed power and/or capacity per energy component already existing in the system
- Potential power per energy component that can be added to the system at maximum
- Custom cost parameters per energy component
- Prices of tariffs to purchase energy from external sources for the energy system

## 2 Methodological approach

With this input data, a predefined function to start the automatic processing of the model can be called. At first, it builds a generic optimization model formulated with the Python library Pyomo and parameterizes it according to the input data to create a specific optimization problem. Here, the target function to minimize equals the sum of the total cost of all components to be used for the component composition. The total cost per component consists of at most:

- Investment costs converted into annual costs by an annuity factor based on the expected lifespan of the component
- Annual operational cost
- Annual energy purchase cost

Investment and operational costs are calculated by applying specific cost factors of a component, while annual operational costs are determined using the expected amount of energy purchased by the component and energy tariff prices given as input. It should be mentioned that the total cost of each component is formed by an individual combination of the three possible cost factors, e.g., the total cost of an energy purchase component consists only of the annual energy purchase cost. 

The optimization problem is then passed to an open-source solver to create a solution. This leads to a solution that follows the fundamental target function to find the cost-minimal composition of energy components and remaining energy purchases to supply the parameterized demands.

After a valid solution is found, the relevant result data is exported either in machine-readable (JSON) or human-readable (Excel) format.

## 3 Energy system coverage

Energy balances are formulated in the model for these energy carriers:

- Electrical energy
- Thermal energy
- Natural gas

Currently, classes to implement the following component groups are predefined and available in the project:

- Combined heat and power plant
    - Transforming natural gas into electrical energy
- Electrical energy storage
    - Storing electrical energy
- Energy demand
    - Consuming energy for the system
    - Can be parameterized for all energy carriers
- Energy feed-in
    - Consuming energy from the system and generating income
    - Can be parameterized only for electrical energy
- Energy purchase
    - Producing energy for the system
    - Can be parameterized for all energy carriers
- Gas boiler
    - Transforming natural gas into thermal energy
- Heat pump
    - Transforming electrical energy into thermal energy
    - Efficiency estimation by the usage of historical air or ground temperature weather data
- Photovoltaic plant
    - Roof surface
    - Free field
    - Producing electrical energy for the system
    - Energy production estimation by the usage of historical solar radiation weather data
- Solar thermal energy plant
    - Producing thermal energy for the system
    - Energy production estimation by the usage of historical solar radiation weather data
- Thermal energy storage
    - Storing thermal energy
- Wind power plant
    - Producing electrical energy for the system
    - Energy production estimation by the usage of historical wind speed weather data

By adding new component groups, this list can be extended, which in turn contributes to extending the scope and applicability of the model.