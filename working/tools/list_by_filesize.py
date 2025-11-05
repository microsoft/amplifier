#!/usr/bin/env python3
import os
import sys


def get_file_sizes(directory):
    """
    Recursively get all files in the directory tree and their sizes.
    Returns a list of tuples (file_path, size_in_bytes).
    """
    file_sizes = []

    # Walk through the directory tree
    for dirpath, _dirnames, filenames in os.walk(directory):
        for filename in filenames:
            # Get the full path of the file
            file_path = os.path.join(dirpath, filename)

            # Get the file size if it's a file (not a symbolic link)
            if os.path.isfile(file_path) and not os.path.islink(file_path):
                try:
                    size = os.path.getsize(file_path)
                    file_sizes.append((file_path, size))
                except (OSError, FileNotFoundError):
                    # Skip files that can't be accessed
                    pass

    return file_sizes


def format_size(size_bytes):
    """Format file size in a human-readable format"""
    # Define size units
    units = ["B", "KB", "MB", "GB", "TB", "PB"]

    # Convert to appropriate unit
    unit_index = 0
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1

    # Format with 2 decimal places if not bytes
    if unit_index == 0:
        return f"{size_bytes} {units[unit_index]}"
    return f"{size_bytes:.2f} {units[unit_index]}"


def main():
    # Use the provided directory or default to current directory
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."

    # Ensure the directory exists
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        sys.exit(1)

    # Get all files and their sizes
    file_sizes = get_file_sizes(directory)

    # Sort by size in descending order
    file_sizes.sort(key=lambda x: x[1], reverse=True)

    # Print the results
    print(f"Files in '{directory}' (sorted by size, largest first):")
    print("-" * 80)
    print(f"{'Size':<10} {'Path':<70}")
    print("-" * 80)

    for file_path, size in file_sizes:
        # Convert the size to a human-readable format
        size_str = format_size(size)
        print(f"{size_str:<10} {file_path}")


if __name__ == "__main__":
    main()
