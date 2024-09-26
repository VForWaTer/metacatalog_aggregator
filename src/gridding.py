from typing import List, Optional, Literal

import numpy as np
import pandas as pd
import xarray as xr
from rioxarray.crs import CRS

# define the possible integration types
INTEGRATIONS = Literal['spatiotemporal', 'spatial', 'temporal']


def create_grid(arrays: List[xr.DataArray], integration: INTEGRATIONS, resolution: int, precision: str, target_epsg: Optional[int] = None, buffer_edge: Optional[float] = 0.01, **kwargs) -> xr.Dataset:
    # switch the integration
    if integration == 'spatiotemporal':
        return create_spatiotemporal_grid(arrays, resolution, precision, target_epsg, buffer_edge, **kwargs)
    elif integration == 'spatial':
        return create_spatial_grid(arrays, resolution, target_epsg, buffer_edge, **kwargs)
    elif integration == 'temporal':
        return create_temporal_grid(arrays, precision, **kwargs)
    else:
        raise ValueError(f"Integration type {integration} not supported.")


def create_spatiotemporal_grid(arrays: List[xr.DataArray], resolution: int, precision: str, target_epsg: Optional[int] = None, buffer_edge: Optional[float] = 0.01, **kwargs) -> xr.Dataset:
    # figure out the bounding box of all coordinate axes
    try:
        minx = min([arr.x.values.min() for arr in arrays if 'x' in arr.indexes])
        maxx = max([arr.x.values.max() for arr in arrays if 'x' in arr.indexes])
        miny = min([arr.y.values.min() for arr in arrays if 'y' in arr.indexes])
        maxy = max([arr.y.values.max() for arr in arrays if 'y' in arr.indexes])
    except ValueError:
        raise ValueError("No x/y coordinates found in any of the input arrays")

    # also run time-axis
    try:
        mint = min([arr.time.values.min() for arr in arrays if 'time' in arr.indexes])
        maxt = max([arr.time.values.max() for arr in arrays if 'time' in arr.indexes])
    except ValueError:
        raise ValueError("No time coordinates found in any of the input arrays")

    # buffer the axes if needed, then the binning will span a bit wider than the actual extremes
    if buffer_edge is not None:
        minx = np.round(minx - buffer_edge * resolution)
        maxx = np.round(maxx + buffer_edge * resolution)
        miny = np.round(miny - buffer_edge * resolution)
        maxy = np.round(maxy + buffer_edge * resolution)
    
    # build the axes
    xaxis = np.arange(minx, maxx, resolution)
    yaxis = np.arange(miny, maxy, resolution)

    # if we have a time axis, we need to build a 3D grid
    taxis = pd.date_range(mint, maxt, freq=precision)
    coords = {'time': ('time', taxis), 'y': ('y', yaxis), 'x': ('x', xaxis)}

    # build a master grid
    grid = xr.Dataset(coords=coords)

    # set the CRS
    if target_epsg is None:
        crs = [a.rio.crs for a in arrays if a.rio.crs is not None][0]
    else:
        crs = CRS.from_epsg(target_epsg)
    
    # set the CRS
    grid.rio.write_crs(crs, inplace=True)

    return grid


def create_spatial_grid(arrays: List[xr.DataArray], resolution: int, target_epsg: Optional[int] = None, buffer_edge: Optional[float] = 0.01, **kwargs) -> xr.Dataset:
    # figure out the bounding box of all coordinate axes
    try:
        minx = min([arr.x.values.min() for arr in arrays if 'x' in arr.indexes])
        maxx = max([arr.x.values.max() for arr in arrays if 'x' in arr.indexes])
        miny = min([arr.y.values.min() for arr in arrays if 'y' in arr.indexes])
        maxy = max([arr.y.values.max() for arr in arrays if 'y' in arr.indexes])
    except ValueError:
        raise ValueError("No x/y coordinates found in any of the input arrays")

    # buffer the axes if needed, then the binning will span a bit wider than the actual extremes
    if buffer_edge is not None:
        minx = np.round(minx - buffer_edge * resolution)
        maxx = np.round(maxx + buffer_edge * resolution)
        miny = np.round(miny - buffer_edge * resolution)
        maxy = np.round(maxy + buffer_edge * resolution)
    
    # build the axes
    xaxis = np.arange(minx, maxx, resolution)
    yaxis = np.arange(miny, maxy, resolution)
    coords = {'y': ('y', yaxis), 'x': ('x', xaxis)}

    # build a master grid
    grid = xr.Dataset(coords=coords)

    # set the CRS
    if target_epsg is None:
        crs = [a.rio.crs for a in arrays if a.rio.crs is not None][0]
    else:
        crs = CRS.from_epsg(target_epsg)
    
    # set the CRS
    grid.rio.write_crs(crs, inplace=True)

    return grid


def create_temporal_grid(arrays: List[xr.DataArray], precision: str, **kwargs) -> xr.Dataset:
     # also run time-axis
    try:
        mint = min([arr.time.values.min() for arr in arrays if 'time' in arr.indexes])
        maxt = max([arr.time.values.max() for arr in arrays if 'time' in arr.indexes])
    except ValueError:
        raise ValueError("No time coordinates found in any of the input arrays")
    
    # build the time coordinates
    taxis = pd.date_range(mint, maxt, freq=precision)
    coords = {'time': ('time', taxis)}

    # build a master grid
    grid = xr.Dataset(coords=coords)

    return grid
