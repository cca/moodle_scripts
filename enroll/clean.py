import os
from pathlib import Path

# Find project root by looking for pyproject.toml
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
while not (project_root / "pyproject.toml").exists() and project_root != project_root.parent:
    project_root = project_root.parent

for f in [
    project_root / "enrollments.csv",
    project_root / "nso.csv",
    project_root / "data" / "Students_for_Internship_Review.xlsx",
]:
    try:
        os.remove(f)
        print(f"Deleted {f}")
    except FileNotFoundError:
        print(f"Couldn't find {f} to delete")
