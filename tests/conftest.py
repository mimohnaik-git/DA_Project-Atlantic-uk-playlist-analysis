from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_prep import run, load_raw, canonical_recordings
from artist_nationality import classify


@pytest.fixture(scope="session")
def project_root():
    return ROOT


@pytest.fixture(scope="session")
def dataset_path(project_root):
    return project_root / "data" / "Atlantic_United_Kingdom.csv"


@pytest.fixture(scope="session")
def prepared(dataset_path):
    clean, exploded, report = run(dataset_path)
    exploded = exploded.copy()
    exploded["nationality"] = exploded["artist_name"].apply(classify)
    recordings = canonical_recordings(clean)
    raw = load_raw(dataset_path)
    return raw, clean, exploded, recordings, report
