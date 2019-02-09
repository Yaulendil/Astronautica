"""
Module dedicated to handling paths and files
"""

from pathlib import Path


# Initialize the "root" as the current directory.
root = Path.cwd()


def get_path(*parts, rootless=False):
    """
    Return a path built from the given components. By default, relative to root.
    """
    # Build the path, and expand '~' to the home directory if needed.
    path = Path(*parts).expanduser()

    if not rootless:
        # Unless otherwise specified, prepend the program directory.
        # Note: This has no effect if the path was already absolute.
        path = root / path

    # Resolve and return.
    return path.resolve()


def get_file(path, mode="r"):
    # Given a path, open and return a file at that location. Read-only mode by default.
    if type(path) == str:
        # If a string was given, convert it into a path.
        path = get_path(path)
    return path.open(mode)


def chroot(new_root):
    # Change the location relative to which all paths are resolved.
    # Note that this is NOT the same as the filesystem root.
    global root
    root = get_path(new_root, rootless=True)
    if root.is_file():
        root = root.parent
