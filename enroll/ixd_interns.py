# this expects a CSV with an email and international status column
# then exports the IXD intern enrollment CSV
import csv
import re
from pathlib import Path

import click

COURSE: str = "IXDSN-INTRN"
EMAIL_COLUMN: str = "email"
INTL_COLUMN: str = "international"


def make_rows(row: dict[str, str], semester: str) -> list[list[str]]:
    username: str = row[EMAIL_COLUMN].strip().replace("@cca.edu", "")
    rows: list[list[str]] = [[username, COURSE, semester]]
    if row[INTL_COLUMN].strip().lower() == "yes":
        rows.append([username, COURSE, "International"])
    return rows


def semester_validator(ctx, param, value):
    """validate semester string for click"""
    if re.match(r"(Spring|Fall|Summer) \d{4}", value):
        return value
    raise click.BadParameter(
        f"Semester must be in the format of 'Season YYYY' like 'Fall 2023', not '{value}'"
    )


@click.command(
    help="Generate IXD intern enrollments from a CSV with email and international columns."
)
@click.help_option("-h", "--help")
@click.option(
    "-i",
    "--infile",
    required=True,
    help="Input CSV file with 'email' and 'international' columns",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-s",
    "--semester",
    callback=semester_validator,
    help='Semester group (like "Fall 2025")',
    required=True,
)
@click.option(
    "-o",
    "--outfile",
    default="enrollments.csv",
    help="Output CSV file (default: enrollments.csv)",
    type=click.Path(path_type=Path),
)
def main(infile, semester, outfile):
    """Generate IXD intern enrollment CSV."""
    with open(infile) as fh:
        reader = csv.DictReader(fh)
        with open(outfile, "w") as out:
            writer = csv.writer(out)
            # header
            writer.writerow(["username", "course1", "group1"])
            for row in reader:
                enrollments = make_rows(row, semester)
                for e in enrollments:
                    writer.writerow(e)

    click.echo(f"Created {outfile}")
    click.echo("Upload Users: https://moodle.cca.edu/admin/tool/uploaduser/")


if __name__ == "__main__":
    main()
