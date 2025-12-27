import os
import fnmatch
import pathspec
from ..formatter.output_formatter import (
    print_operation,
    print_info,
    Icons,
    Colors,
    format_size,
)


def crawl_local_files(
    directory,
    include_patterns=None,
    exclude_patterns=None,
    max_file_size=None,
    use_relative_paths=True,
):
    """
    Crawl files in a local directory with similar interface as crawl_github_files.
    Args:
        directory (str): Path to local directory
        include_patterns (set): File patterns to include (e.g. {"*.py", "*.js"})
        exclude_patterns (set): File patterns to exclude (e.g. {"tests/*"})
        max_file_size (int): Maximum file size in bytes
        use_relative_paths (bool): Whether to use paths relative to directory

    Returns:
        dict: {"files": {filepath: content}}
    """
    if not os.path.isdir(directory):
        raise ValueError(f"Directory does not exist: {directory}")

    files_dict = {}

    # --- Load .gitignore ---
    gitignore_path = os.path.join(directory, ".gitignore")
    gitignore_spec = None
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8-sig") as f:
                gitignore_patterns = f.readlines()
            gitignore_spec = pathspec.PathSpec.from_lines(
                "gitwildmatch", gitignore_patterns
            )
            # Format the .gitignore path to be relative to directory for cleaner output
            gitignore_rel = (
                os.path.relpath(gitignore_path, directory)
                if use_relative_paths
                else gitignore_path
            )
            print_info(".gitignore", gitignore_rel)
        except (IOError, OSError, UnicodeDecodeError) as e:
            print(
                f"Warning: Could not read or parse .gitignore file {gitignore_path}: {e}"
            )

    all_files = []
    for root, dirs, files in os.walk(directory):
        # Filter directories using .gitignore and exclude_patterns early
        excluded_dirs = set()
        for d in dirs:
            dirpath_rel = os.path.relpath(os.path.join(root, d), directory)

            if gitignore_spec and gitignore_spec.match_file(dirpath_rel):
                excluded_dirs.add(d)
                continue

            if exclude_patterns:
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(dirpath_rel, pattern) or fnmatch.fnmatch(
                        d, pattern
                    ):
                        excluded_dirs.add(d)
                        break

        for d in dirs.copy():
            if d in excluded_dirs:
                dirs.remove(d)

        for filename in files:
            filepath = os.path.join(root, filename)
            all_files.append(filepath)

    for filepath in all_files:
        relpath = (
            os.path.relpath(filepath, directory) if use_relative_paths else filepath
        )

        # --- Exclusion check ---
        excluded = False
        if gitignore_spec and gitignore_spec.match_file(relpath):
            excluded = True

        if not excluded and exclude_patterns:
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(relpath, pattern):
                    excluded = True
                    break

        included = False
        if include_patterns:
            for pattern in include_patterns:
                if fnmatch.fnmatch(relpath, pattern):
                    included = True
                    break
        else:
            included = True

        if not included or excluded:
            print_operation(f"{relpath}", Icons.SKIP, indent=2)
            continue  # Skip to next file if not included or excluded

        if max_file_size and os.path.getsize(filepath) > max_file_size:
            print_operation(f"{relpath}", Icons.SKIP, indent=2)
            continue  # Skip large files

        # --- File is being processed ---
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
            files_dict[relpath] = content
            file_size = os.path.getsize(filepath)
            print_operation(
                f"{relpath} {Colors.DARK_GRAY}({format_size(file_size)})",
                Icons.DOWNLOAD,
                indent=2,
            )
        except (IOError, OSError, UnicodeDecodeError, PermissionError) as e:
            print_operation(f"{relpath}: {e}", Icons.ERROR, indent=2)

    return {"files": files_dict}


if __name__ == "__main__":
    print("--- Crawling parent directory ('..') ---")
    files_data = crawl_local_files(
        "..",
        exclude_patterns={
            "*.pyc",
            "__pycache__/*",
            ".venv/*",
            ".git/*",
            "docs/*",
            "output/*",
        },
    )
    print(f"Found {len(files_data['files'])} files:")
    for path in files_data["files"]:
        print(f"  {path}")
