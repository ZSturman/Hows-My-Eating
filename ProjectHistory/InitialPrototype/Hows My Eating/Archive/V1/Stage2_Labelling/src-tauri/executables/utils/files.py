import os
from typing import Optional


def get_matching_file(
    dir_path: str, extension: str, match_prefix: Optional[str] = None
) -> Optional[str]:
    """
    Get the first file in a directory with a specific extension and optional prefix.

    Args:
        dir_path (str): Path to the directory.
        extension (str): File extension to match (e.g., ".mov").
        match_prefix (Optional[str]): Prefix to match (e.g., directory name). If None, matches all files with the extension.

    Returns:
        Optional[str]: The first matching file (if any), or None if no matches are found.
    """
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"The directory '{dir_path}' does not exist.")

    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"The path '{dir_path}' is not a directory.")

    # Get all files in the directory
    for file in os.listdir(dir_path):
        if file.endswith(extension) and (not match_prefix or file.startswith(match_prefix)):
            return os.path.join(dir_path, file)

    # No match found
    return None


def get_mov_from_dir(dir_path: str) -> Optional[str]:
    """
    Get the path to the first matching MOV file in the directory.

    Args:
        dir_path (str): Path to the directory.

    Returns:
        Optional[str]: The path to the matching MOV file (if any), or None if no matches are found.
    """
    dir_name = os.path.basename(dir_path)
    return get_matching_file(dir_path, ".mov", dir_name)


def get_json_from_dir(dir_path: str) -> Optional[str]:
    """
    Get the path to the first matching JSON file in the directory.

    Args:
        dir_path (str): Path to the directory.

    Returns:
        Optional[str]: The path to the matching JSON file (if any), or None if no matches are found.
    """
    dir_name = os.path.basename(dir_path)
    return get_matching_file(dir_path, ".json", dir_name)