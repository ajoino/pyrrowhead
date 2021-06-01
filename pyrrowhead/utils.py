import os
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def switch_directory(path: Path):
    origin = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)