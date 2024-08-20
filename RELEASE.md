# Metacatalog aggregator


This tool is designed to be used together with the V-FOR-WaTer [Metacatalog data loader](https://github.com/VForWaTer/tool_vforwater_loader).
It uses a number of data source files along with either a metacatalog entry or JSON dumps of the metadata. The data is aggregated to a target precision (temporal) and spatial resolution and then ingested into a geocube that is stored as a netCDF file.

This tool is based on the [Python template](https://github.com/vforwater/tool_template_python) for a generic containerized Python tool following the [Tool Specification](https://vforwater.github.io/tool-specs/) for reusable research software using Docker.
