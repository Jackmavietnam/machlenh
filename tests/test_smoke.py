from pathlib import Path


def test_project_structure():
    root = Path(__file__).resolve().parents[1]
    assert (root / 'config' / 'universe.yaml').exists()
    assert (root / 'db' / 'schema.sql').exists()
    assert (root / 'run_daily.py').exists()
