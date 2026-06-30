"""Load Moodle API configuration from .env file in project root."""

import os
from pathlib import Path

from dotenv import dotenv_values

# Find project root (where .env file is) by looking for pyproject.toml
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
while not (project_root / "pyproject.toml").exists() and project_root != project_root.parent:
    project_root = project_root.parent

conf = {
    **dotenv_values(project_root / ".env"),  # load private env from project root
    **os.environ,  # override loaded values with environment variables
}

# backwards compatibility: expose token and url as module-level variables
token = conf.get("TOKEN", "")
url = conf.get("DOMAIN", "") + "/webservice/rest/server.php" if conf.get("DOMAIN") else ""
