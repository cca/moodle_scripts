"""
Convert CSV data into Moodle enrollment CSV for use on Upload Users page
Be able to specify where the fields we're looking for exist in the CSV.
The main work of this script is creating multiple rows for International
students who need to be placed into multiple groups.
"""

import csv
import re

import click

email_regex: re.Pattern[str] = re.compile(r"@cca\.edu$")
student_type_map: dict[str, str] = {
    "First Year": "FRESH",
    "Graduate": "GRAD",
    "Second Degree": "TRSFR",
    "Transfer": "TRSFR",
}


def writerows(writer, row, field_map) -> None:
    # sometimes user hasn't created their CCA email yet, if so skip them
    email = row[field_map["email"]].strip()
    if not re.search(email_regex, email) or not (username := re.sub(email_regex, "", email)):
        return

    stype = row[field_map["type"]].strip().title()
    if stype not in student_type_map:
        raise ValueError(f"Unknown student type {stype} for student {username}")

    writer.writerow(
        {
            "username": username,
            "course1": field_map["course"].format(type=student_type_map[stype]),
            "group1": stype,
        }
    )
    # if international, write another row with the international group
    intl = row[field_map["intl"]]
    if intl:
        writer.writerow(
            {
                "username": username,
                "course1": field_map["course"].format(type=student_type_map[stype]),
                "group1": "International",
            }
        )


@click.command(help="Convert new students CSV into Moodle enrollment CSV.")
@click.help_option("-h", "--help")
@click.argument("input.csv", required=True, type=click.Path(exists=True))
@click.option(
    "--outfile",
    "-o",
    default="nso.csv",
    help="Output CSV file (default: nso.csv)",
    type=click.Path(writable=True),
)
@click.option(
    "--email",
    "-e",
    default="CCA email",
    help="Email column (default: CCA email)",
    type=str,
)
@click.option(
    "--intl",
    default="Is International Student",
    help="International column (default: Is International Student)",
    type=str,
)
@click.option(
    "--type",
    "-t",
    default="Applicant Type",
    help="Student type (First Year, Transfer, Graduate) column (default: Applicant Type)",
    type=str,
)
@click.option(
    "--course",
    "-c",
    help="Course shortname (e.g. NSO-2024SP). If {type} is present in the course name, it will be replaced with the student type (GRAD, TRSFR, FRESH).",
    required=True,
    type=str,
)
def main(**kwargs):
    field_map: dict[str, str] = {
        "email": kwargs["email"],
        "intl": kwargs["intl"],
        "course": kwargs["course"],
        "type": kwargs["type"],
    }
    with open(kwargs["input.csv"]) as csvfile:
        reader = csv.DictReader(csvfile)
        with open(kwargs["outfile"], "w") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=["username", "course1", "group1"])
            writer.writeheader()
            for row in reader:
                writerows(writer, row, field_map)


if __name__ == "__main__":
    main()
