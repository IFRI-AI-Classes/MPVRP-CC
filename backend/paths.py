"""Canonical filesystem locations used by the backend."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_INSTANCE_COUNT = 100
DATA_DIR = PROJECT_ROOT / "data"
INSTANCES_DIR = DATA_DIR / "instances"
WITH_CHANGEOVER_INSTANCES_DIR = INSTANCES_DIR / "with_changeover_costs"
WITHOUT_CHANGEOVER_INSTANCES_DIR = INSTANCES_DIR / "without_changeover_costs"
GENERATED_INSTANCES_DIR = DATA_DIR / "generated"
REEVALUATED_CHANGEOVER_SOLUTIONS_DIR = DATA_DIR / "reevaluated_solutions"
TEMP_DIR = PROJECT_ROOT / "temp"
