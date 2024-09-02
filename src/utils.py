from typing import TypedDict, List
from pathlib import Path
import warnings

from metacatalog.models.entry import Entry
from metacatalog.models.combined import Metadata, from_file


class FileMapping(TypedDict):
    entry: Entry | Metadata
    data_path: str


def get_file_mapping(datasets_path: str, metadata_files: str = '*.metadata.json') -> List[FileMapping]:
    file_mapping: List[FileMapping] = []
    
    # iterate over all metadata files
    for meta_file in Path(datasets_path).rglob(metadata_files):
        # load the metadata
        meta = from_file(meta_file)

        # try to find a dataset folder
        folder_name = meta_file.name.replace(metadata_files.replace('*', ''), '')
        data_path = (meta_file.parent / folder_name).resolve()

        # check there are files with that stem
        if len(list(data_path.glob('*'))) > 0:
            file_mapping.append({
                'entry': meta,
                'data_path': str(data_path)
            })
        else:
            warnings.warn(f"Found metadata file {meta_file}, but no associated dataset folder: {data_path / '*'}")


    return file_mapping

