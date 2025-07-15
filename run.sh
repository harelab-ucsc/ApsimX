#!/bin/bash

# source the virtual environment with the OASIS pyproject installed
source .venv/bin/activate

# call OASIS `config` executable with output arg set to the ApsimX `tmp/` directory
oasis config ~/ApsimX/tmp/test.csv

# call the R executable `LocationGenerator.R`, which prepares an *.apsimx file according to `test.csv`
cd Tests/Simulation/ZMQ-Sync/MetompkinFarm/
Rscript ../../../../Tools/LocationGenerator/LocationGenerator.R

# run the server-client pair, clean up
cd ~/ApsimX
dotnet run --framework net6.0 --project APSIM.Server/ZMQ+msgpack/ -- -P interactive -f Tests/Simulation/ZMQ-Sync/MetompkinFarm/MetompkinFarm.apsimx &
oasis client tmp/test.csv tmp/heatmap --output tmp/array.npy
pkill dotnet

# consume the raw output of the client, save preprocessing stage results to hard-coded targets
oasis raster ~/ApsimX/tmp/array.npy tmp

# call OASIS `metompkin` executable to format Metompkin farm data for ingestion by visualization script
cd tmp
oasis metompkin tmp/MetompkinFarm_WC_ST_SC_220719-231109.csv test

cd ..
# TODO: call visualization script (currently quail.py, to be renamed) 
#     or call vis. script independently
