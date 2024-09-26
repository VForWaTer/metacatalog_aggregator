import os
import sys
import warnings
import time

from json2args import get_parameter
from json2args.logger import logger

from utils import get_file_mapping
import ingestor
import gridding

# parse parameters
param = get_parameter(typed=True)

# TODO: the dataset path inside the container is hardcoded here. We might want to make this a parameter
datasets_path = os.getenv('DATASETS_PATH', '/in/datasets')

# check if a toolname was set in env
toolname = os.environ.get('TOOL_RUN', 'geocube').lower()

# check if the tool is valid
if toolname != 'geocube':
    logger.error(f"The entrypoint '{toolname}' is not supported. Check the tool.yml for valid endpoints.")
    sys.exit(1)

# run the main tool - start a timer
start = time.time()

# info that the GeoCube tool is starting
logger.info("##TOOL START - Geocube")
logger.debug(f"Parameters passed to the tool: params = {repr(param)}")

# create a file - mapping
with warnings.catch_warnings(record=True) as w:
    file_mapping = get_file_mapping(datasets_path, metadata_files='*.metadata.json')
    logger.debug(f"Found {len(file_mapping)} dataset folders with metadata.")

    # log the warnings if any
    for warn in w:
        logger.warning(warn.message)

# load all datasets
arrays = ingestor.load_files(file_mapping=file_mapping, params=param)
logger.debug(f"arrays = ingestor.loader_files(file_mapping={[{'data_path': m['data_path'], 'entry': 'Metadata(id=%d)' % m['entry'].id} for m in file_mapping]}, params=params)")

# create a common Grid
grid = gridding.create_grid(arrays=arrays, **param.model_dump())
logger.debug(f"grid = gridding.create_grid(arrays=arrays, **{param})")

# aggregate to the grid 
cube = ingestor.aggregate_xarray(arrays, grid, param.aggregates)
logger.debug(f"cube = ingestor.aggregate_xarray(arrays=arrays, grid=grid, aggregates=[{param.aggregates}])")

# save the cube
# TODO this has to be implemented in a more helpful way
# start saving
start_save = time.time()
cube.to_netcdf('/out/cube.nc', engine='h5netcdf')
end_save = time.time()
logger.debug("cube.to_netcdf('/out/cube.nc', engine='h5netcdf')")
logger.info(f"Saving the cube took {end_save - start_save:.2f} seconds")

# inform that the tool has finished
end = time.time()
logger.info(f"Total runtime: {end - start:.2f} seconds")
logger.info("##TOOL FINISH - Geocube")