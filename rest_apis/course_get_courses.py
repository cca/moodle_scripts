import json
import sys
from pathlib import Path

import click
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

# https://moodle.cca.edu/webservice/rest/server.php?wstoken=...&wsfunction=core_course_get_courses&moodlewsrestformat=json


def get_mdl_courses():
    """return the complete list of courses in Moodle

    returns: a list of course objects
    """
    url: str = config.url
    params: dict[str, str] = {
        # found at https://moodle.cca.edu/admin/settings.php?section=webservicetokens
        "wstoken": config.token,
        "wsfunction": "core_course_get_courses",
        "moodlewsrestformat": "json",
    }

    response: requests.Response = requests.get(url, params=params)
    data = response.json()

    if data and isinstance(data, list):
        for c in data:
            print(c["shortname"])
        print(f"Found {len(data)} total courses")
        return data
    """
    Moodle sends an HTTP 200 response back on errors with details in the JSON.
    Below are just a few examples I've run into.

    If it doesn't recognize the structure of the criteria parameter in the URL,
    you get this error message:
    { exception: "invalid_parameter_exception", errorcode: "invalidparameter",
    message: "Invalid parameter value detected" }

    If the web service being specified doesn't exist, you get:
    { exception: "dml_missing_record_exception", errorcode: "invalidrecord",
    message: "Can not find data record in database table external_functions."}

    If the token you're using is related to a Service that doesn't have the
    necessary permissions you get:
    { exception: "webservice_access_exception", errorcode: "accessexception",
    message: "Access control exception" }
    """
    return f"Error: {data}"


@click.command(help="Get the complete list of courses in Moodle.")
@click.help_option("-h", "--help")
@click.option(
    "--json-output",
    is_flag=True,
    help="Output as formatted JSON",
)
@click.option(
    "--token",
    "-t",
    help="Moodle web service token (overrides .env)",
)
@click.option(
    "--domain",
    "-d",
    help="Moodle domain URL (overrides .env)",
)
def main(json_output, token, domain):
    """Get all courses from Moodle."""
    if token:
        config.token = token
    if domain:
        config.url = domain + "/webservice/rest/server.php"

    result = get_mdl_courses()
    if json_output and isinstance(result, list):
        click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
