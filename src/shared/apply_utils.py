import os

def apply_patch(directory: str, patch: list[tuple[str, str]]) -> list[str]:
    """
    Applies a patch represented as a list of (relative_path, new_content) tuples
    to a target directory.

    Args:
        directory: The base directory to apply the patch to.
        patch: A list of tuples, where each tuple contains the relative path
               of the file and its new content.

    Returns:
        A list of paths of the files that were changed (relative to the directory).
    """
    changed_files = []
    for relative_path, new_content in patch:
        abs_path = os.path.join(directory, relative_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(new_content)
        changed_files.append(relative_path)
    return changed_files

# TODO: Add a helper for applying unified diffs in the future if needed. 