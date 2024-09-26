from typing import List, Dict, Tuple, Optional
from pathlib import Path
import warnings

from metacatalog.models import Entry
from tqdm import tqdm
import rioxarray
from rioxarray.crs import CRS
import xarray as xr
import numpy as np
from json2args.logger import logger
from pydantic import BaseModel

from utils import FileMapping

# these are the parameters comming from json2args
class Params(BaseModel):
    precision: str
    resolution: int
    integration: str
    aggregates: List[str]


def load_files(file_mapping: List[FileMapping], params: Params | Dict) -> xr.Dataset:
    # handle the parameters
    if isinstance(params, dict):
        params = Params(**params)
    
    # create a container for the DataArrays
    arrays = []

    # iterate over the mapping and load every dataset as a xarray DataArray
    for mapping in tqdm(file_mapping):
        # unpack the mapping
        entry = mapping['entry']
        data_path = Path(mapping['data_path'])
        #logger.debug(f"Loading dataset <ID={entry.id}> from {data_path}")

        # check which loader to use
        if data_path.is_dir():
            # load all files in the directory
            #files = glob.glob(str(data_path / '**' / '*'), recursive=True)
            files = list(data_path.rglob('*'))
        else:
            files = [str(data_path)]
        
        # check if this is a nc
        if str(files[0]).lower().endswith('.nc'):
            arr = load_raster(files, entry, target_epsg=params.target_epsg)
        elif str(files[0]).lower().endswith('.tif') or files[0].lower().endswith('.tiff'):
            arr = load_raster(files, entry, target_epsg=params.target_epsg)
        else:
            logger.error(f"File typ of Dataset <ID={entry.id}> not yet supported: {files[0]}")
            continue
        
        # write a CRS if None is given and warn in that case
        if not arr.rio.crs:
            logger.warning(f"Dataset <ID={entry.id}> has no CRS. This might lead to unexpected results.")
            arr = arr.rio.write_crs(CRS.from_epsg(4326))

        # apped the array to the container
        arrays.append(arr)
    return arrays
    #     # next step is to aggregate to the target resolution and precision
    #     aggregates = aggregate_xarray(arr, entry, **params.model_dump())

    #     # add the arrays to the list
    #     for agg in aggregates:
    #         arrays.append(agg)

    # return arrays


def merge_arrays(arrays: List[xr.DataArray]) -> xr.Dataset:
    # check if all were mapped to the same suggested UTM CRS
    crs = set([arr.rio.crs for arr in arrays])
    if len(crs) > 1:
        logger.warning(f"The aggregated dataset chunks could not be reprojected into a common CRS and now use different CRS: [{crs}]. This might be caused by missing CRS information in the original datasets.")

    # now overwrite the CRS

    # merge all arrays
    merged = xr.merge(arrays, combine_attrs='drop_conflicts', join='outer', compat='no_conflicts')

    return merged


def _binned_spatial_index(arr: xr.DataArray, grid: xr.Dataset) -> Dict[str, Tuple[str, np.ndarray]]:
    # extract the original coordinates
    original_x = arr.x.values if 'x' in arr.indexes else []
    original_y = arr.y.values if 'y' in arr.indexes else []

    # digitize the corrdinates to the grid
    x_indices = np.digitize(original_x, grid.x.values) - 1 if 'x' in arr.indexes else []
    y_indices = np.digitize(original_y, grid.y.values) - 1 if 'y' in arr.indexes else []

    # create the binned coordinates
    binned_x = grid.x.values[x_indices]
    binned_y = grid.y.values[y_indices]

    # bin the array by the binned coords
    return {'y': ('y', binned_y), 'x': ('x', binned_x)}


def _binned_temporal_index(arr: xr.DataArray, grid: xr.Dataset) -> Dict[str, Tuple[str, np.ndarray]]:
    # extract the original coordinates
    original_t = arr.time.values.astype(int) if 'time' in arr.indexes else []

    # digitize the corrdinates to the grid
    t_indices = np.digitize(original_t, grid.time.values.astype(int)) - 1

    # create the binned coordinates
    binned_t = grid.time.values[t_indices]

    # bin the array by the binned coords
    return {'time': ('time', binned_t)}


def bin_coordinate_axes(arr: xr.DataArray, grid: xr.Dataset) -> xr.DataArray:
    coords_def = {}
    
    # get the time index if there is a time axis in the grid
    if 'time' in grid.indexes:
        coords_def.update(_binned_temporal_index(arr, grid))
    
    # get the spatial indices if the grid has spatial axes
    if 'y' in grid.indexes:
        coords_def.update(_binned_spatial_index(arr, grid))
    
    # replace the DataArray coordinates with the binned version
    arr_binned = arr.assign_coords(coords_def)

    return arr_binned
                                   

def aggregate_xarray(arrays: List[xr.DataArray], grid: xr.Dataset, aggregates: List[str]) -> xr.Dataset:
    # make a deep copy of grid 
    cube = grid.copy(deep=True)

    for arr in tqdm(arrays):
        arr_binned = bin_coordinate_axes(arr, grid)

        # groupby each of the passed aggregates
        for aggregate in aggregates:
            # groupby this aggregate over all axes

            # use only the axes that are in the binned array AND in the grid
            axes = [ax for ax in grid.indexes if ax in arr_binned.indexes]

            agg = arr_binned.to_dataframe()[[v for v in arr_binned.data_vars]].groupby(axes).aggregate(aggregate).to_xarray()
            #agg = agg.groupby('y').reduce(getattr(np, aggregate)).groupby('x').reduce(getattr(np, aggregate))
            #agg = arr_binned[[v for v in arr_binned.data_vars]].groupby(**{ax: xr.groupers.UniqueGrouper() for ax in axes}).reduce(getattr(np, aggregate))
            # add all data_variables to the cube
            for data_name in agg.data_vars:
                cube[f"{data_name}_{aggregate}"] = agg[data_name]
    
    # return 
    return cube

def load_raster(files: List[str], entry: Entry, target_epsg: Optional[int] = None) -> xr.DataArray:
    # load the variable name
    var_names = entry.datasource.variable_names

    # load the data
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        if str(files[0]).lower().endswith('.tif') or str(files[0]).lower().endswith('.tiff'):
            xarr = xr.open_mfdataset(files, decode_coords='all')[var_names]
        else:
            xarr = xr.open_mfdataset(files, decode_coords='all', engine='h5netcdf')[var_names]
    
    # check that each chunk as a CRS
    crs = xarr.rio.crs
    if crs is None:
        # TODO: in the future we can either remove the dataset here or just assume its WGS84
        logger.warning(f"Dataset <ID={entry.id}> has no CRS. This might lead to unexpected results.")
        crs = CRS.from_epsg(4326)

    # load the used indexes
    indices = [i for i in xarr.indexes]
    to_squeeze = []
    for idx in indices:
        if idx not in ['time', 'x', 'y']:
            logger.warning(f"Dataset <ID={entry.id}> in file <{files[0]}> has an index <{idx}> that is not in ['time', 'x', 'y']. This might lead to unexpected results, as we will drop it.")
            to_squeeze.append(idx)
    if len(to_squeeze) > 0:
        xarr = xarr.squeeze(to_squeeze, drop=True)

    # drop all that is not an indexed coordinate and not a variable
    names_set = set([*[c for c in xarr.coords], *[c for c in xarr.dims]])
    xarr = xarr.drop_vars([c for c in names_set if c not in ['time', 'x', 'y', *var_names]])

    # write back the CRS
    xarr = xarr.rio.write_crs(crs)
    
    # handle the target CRS system
    if target_epsg is None:
        try:
            target_crs = xarr.rio.estimate_utm_crs()
        except RuntimeError as e:
            logger.error(f"No CRS found for dataset <ID={entry.id}> in file <{files[0]}>. An UTM CRS could not be inferred. Error: {str(e)}")
    else:
        target_crs = CRS.from_epsg(target_epsg)
    
    # reproject and copy
    xarr = xarr.rio.reproject(target_crs)
    out = xarr.copy()
    xarr.close()
    
    return out


def load_parquet(files: List[str], entry: Entry) -> xr.DataArray:
    raise NotImplementedError("Parquet files are not yet supported.")
