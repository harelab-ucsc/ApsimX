#!/bin/bash

source .venv/bin/activate
oasis config ~/ApsimX/tmp/test.csv

cd Tests/Simulation/ZMQ-Sync/MetompkinFarm/
Rscript ../../../../Tools/LocationGenerator/LocationGenerator.R

cd ~/ApsimX
dotnet run --framework net6.0 --project APSIM.Server/ZMQ+msgpack/ -- -P interactive -f Tests/Simulation/ZMQ-Sync/MetompkinFarm/MetompkinFarm.apsimx &
oasis client tmp/test.csv tmp/heatmap --output tmp/array.npy
pkill dotnet
oasis raster ~/ApsimX/tmp/array.npy tmp

cd tmp
oasis metompkin tmp/MetompkinFarm_WC_ST_SC_220719-231109.csv test

cd ..

