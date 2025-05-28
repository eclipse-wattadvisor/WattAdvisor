Installation
############

Requirements
************

An existing Python installation is required.
To install WattAdvisor, it is necessary to have Python v3.11 available. Use either conda to create a fresh environment with that version or install Python v3.11 directly.   

Installation of the Python package
**********************************
.. warning::

    It is highly recommended to install WattAdvisor into a new, clean and empty Python environment. 
    You can use *venv* or *conda* to create such an environment. 

Use *pip* to install the package into your Python environment:

.. code-block:: shell
    
    pip install https://github.com/eclipse-wattadvisor/WattAdvisor/archive/main.zip


Install or add a solver to the project
**************************************

An optimization problem solver is required to use WattAdvisor. The package installed via pip already contains the solver *HiGHS*.
Furthermore, *CBC* and *gurobi* solvers are currently supported directly, but need to be installed separately.


Add weather data
****************

WattAdvisor depends on weather data to estimate the power generation profile from renewable energy plants or 
to generate synthetical heat demand profiles from annual sums of heat demands.
Currently, it is possible to either

* use data from Copernicus Climate Change Service that you have to manually download 
* or use custom weather data from other sources provided as CSV file(s)

At the beginning, the easier way is to acquire weather data from Copernicus Climate Change Service.

Download weather data from Copernicus Climate Change Service
============================================================

To download weather data from Copernicus Climate Change Service, you have to `create an account <https://cds.climate.copernicus.eu/user/register>`_.
After creation, visit your `account page <https://cds.climate.copernicus.eu/user>`_ to collect your API key and UID which is needed to download weather data. 
You find the key and UID at the bottom of the page: 

.. image:: CDS_API_key.png

After that, copy the following code snippet to a new Python script:

.. literalinclude:: code_snippet_cdsapi.py
  :language: python

Paste your Climate Data Store UID and API key at the corresponding position and run the script from the WattAdvisor Python environment. 
If everything is configured correctly, you will get a similar output like:

.. code-block:: text

    2024-06-07 13:44:26,667 INFO Welcome to the CDS
    2024-06-07 13:44:26,667 INFO Sending request to https://cds.climate.copernicus.eu/api/v2/resources/reanalysis-era5-single-levels
    2024-06-07 13:44:26,776 INFO Request is queued
    2024-06-07 13:44:27,865 INFO Request is running
    2024-06-07 13:46:20,994 INFO Request is completed
    2024-06-07 13:46:20,994 INFO Downloading https://download-0015-clone.copernicus-climate.eu/cache-compute-0015/cache/data5/adaptor.mars.internal-1717760725.....nc to weather.nc (1.4G)  


After the download has completed, move the downloaded *weather.nc*-file to your working directory.