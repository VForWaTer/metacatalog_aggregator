# Metacatalog aggregator


This tool is designed to be used together with the V-FOR-WaTer [Metacatalog data loader](https://github.com/VForWaTer/tool_vforwater_loader).
It uses a number of data source files along with either a metacatalog entry or JSON dumps of the metadata. The data is aggregated to a target precision (temporal) and spatial resolution and then ingested into a geocube that is stored as a netCDF file.

This tool is based on the [Python template](https://github.com/vforwater/tool_template_python) for a generic containerized Python tool following the [Tool Specification](https://vforwater.github.io/tool-specs/) for reusable research software using Docker.


## Structure

```
/
|- in/
|  |- input.json
|- out/
|  |- ...
|- src/
|  |- tool.yml
|  |- run.py
|  |- CITATON.cff
```

* `input.json` are parameters. Whichever framework runs the container, this is how parameters are passed.
* `tool.yml` is the tool specification. It contains metadata about the scope of the tool, the number of endpoints (functions) and their parameters
* `run.py` is the tool itself
* `CITATION.cff` is a citation file that describes the tool and its authors. It is used by the

## How to build the image?

You can build the image from within the root of this repo by
```
docker build -t metacatalog_geocube .
```

## How to run?

This template installs the json2args python package to parse the parameters in the `/in/input.json`. This assumes that
the files are not renamed and not moved and there is actually only one tool in the container. For any other case, the environment variables `PARAM_FILE` can be used to specify a new location for the `parameters.json` and `TOOL_RUN` can be used to specify the tool to be executed.
The `run.py` has to take care of that.

To invoke the docker container directly run something similar to:
```
docker run --rm -it -v /path/to/local/in:/in -v /path/to/local/out:/out -e TOOL_RUN=geocube metacatalog_geocube
```

Then, the output will be in your local out and based on your local input folder. Stdout and Stderr are also connected to the host.



