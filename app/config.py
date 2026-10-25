"""Application configuration settings.

Reads configuration parameters from environment variables with safe defaults.
"""

from pathlib import Path
import os

# Base directory of the repository (parent of the 'app' directory)
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Database configuration
# Defaults to data/students.db inside the project directory
DATABASE_PATH_ENV: str = os.getenv("DATABASE_PATH", "data/students.db")


def get_database_path() -> Path:
    """Return the absolute Path to the SQLite database file.

    If DATABASE_PATH is relative, it is resolved against the project root.
    """
    db_env_path = os.getenv("DATABASE_PATH", "data/students.db")
    path_obj = Path(db_env_path)
    if path_obj.is_absolute():
        return path_obj
    return (BASE_DIR / path_obj).resolve()


# Pagination limits
DEFAULT_LIMIT: int = 20
MAX_LIMIT: int = 100
MIN_LIMIT: int = 1
MIN_OFFSET: int = 0
