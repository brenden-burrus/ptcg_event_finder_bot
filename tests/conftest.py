import pathlib
import sys

# bot/ uses flat imports (`from event_finder_class import ...`), so it has to be
# on the path as a directory rather than imported as a package.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "bot"))
