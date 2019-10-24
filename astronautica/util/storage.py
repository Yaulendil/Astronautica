"""Storage Module: For the persistent storage of data.

Adapted from Recipe: https://code.activestate.com/recipes/576642/ (MIT Licensed)

This Module therefore is licensed under the MIT License, NOT the GPLv3 License
    used by the rest of this program. https://opensource.org/licenses/MIT
"""

import csv
import json
import os
from pathlib import Path
import pickle
import shutil
from typing import Union


class PersistentDict(dict):
    """Persistent dictionary with an API compatible with shelve and anydbm.

    The dict is kept in memory, so the dictionary operations run as fast as a
        regular dictionary.

    Write to disk is delayed until close or sync (similar to gdbm's fast mode).
        Input file format is automatically discovered. Output file format is
        selectable between pickle, json, and csv. All three serialization
        formats are backed by fast C implementations.
    """

    def __init__(
        self,
        filepath: Union[Path, str],
        flag: str = "c",
        mode: int = None,
        fmt: str = "pickle",
        *a,
        **kw,
    ):
        self.flag = flag  # r=readonly, c=create, or n=new
        self.mode = mode  # None or an octal triple like 0644 (As Int: 0o0644)
        self.format = fmt  # 'csv', 'json', or 'pickle'
        self.path = Path(filepath)

        if flag != "n" and os.access(str(filepath), os.R_OK):
            with self.path.open("rb" if fmt == "pickle" else "r") as fd:
                self.load(fd)

        dict.__init__(self, *a, **kw)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def sync(self):
        """Write Dict to disk."""
        if self.flag != "r":
            tmp = self.path.with_suffix(".tmp")

            try:
                with tmp.open("wb" if self.format == "pickle" else "w") as fd:
                    self.dump(fd)
            except:
                tmp.unlink()
                raise

            shutil.move(tmp, self.path)  # atomic commit

            if self.mode is not None:
                self.path.chmod(self.mode)

    def close(self):
        self.sync()

    def dump(self, fd):
        if self.format == "csv":
            csv.writer(fd).writerows(self.items())
        elif self.format == "json":
            json.dump(self, fd, separators=(",", ":"))
        elif self.format == "pickle":
            pickle.dump(dict(self), fd, 2)
        else:
            raise NotImplementedError(f"Unknown format: {self.format!r}")

    def load(self, fd):
        # Try formats from most restrictive to least restrictive.
        for loader in (pickle.load, json.load, csv.reader):
            fd.seek(0)
            try:
                return self.update(loader(fd))
            except:
                continue
        raise ValueError("File not in a supported format")
