"""Get Moodle category data from its REST API.
Returns JSON data of the named category and all its children.
"""

import json
import sys
from pathlib import Path

import click
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

# https://moodle.cca.edu/webservice/rest/server.php?wstoken=...&wsfunction=core_course_get_categories&moodlewsrestformat=json&criteria[0][key]=name&criteria[0][value]=2019SP


def get_mdl_categories(filter: dict[str, str]):
    """obtain a list of JSON representations of Moodle course categories

    returns an array of category dicts (see their fields below)

    `filter` is a dict like {"name": "2019SP"} which is used to retrieve only
    categories where the given field matches the value. So, for instance, we can
    find the term-level category by filtering on name and then find the children
    of that term by filter on {"parent": {{id of term}} }. You may specify
    multiple keys to filter upon.

    fields are: id, name, parent, coursecount, visible, timemodified, depth, path*

    * `path` looks like /{{parent ID}}/{{category ID}} so it's an effective way
    to find where a category lies in the hierarchy. The list above is only the
    useful fields. To see the full set, look at a returned value. A few fields
    are empty or unused like "idnumber" and "description".
    """
    # constants
    url = config.url
    service = "core_course_get_categories"
    format = "json"
    params = {
        # see https://moodle.cca.edu/admin/settings.php?section=webservicetokens
        "wstoken": config.token,
        "wsfunction": service,
        "moodlewsrestformat": format,
    }

    # construct criteria in PHP array query string format
    # because it wouldn't be Moodle without a weird, antiquated nuance
    for index, (key, value) in enumerate(filter.items()):
        params[f"criteria[{index}][key]"] = key
        params[f"criteria[{index}][value]"] = value

    response = requests.get(url, params=params)
    data = response.json()

    if data is not None:
        if isinstance(data, list) and len(data) == 0:
            # not an error but didn't get any categories
            print("No matching categories were found; check your query filter.")
            return data

        elif isinstance(data, dict):
            if data.get("exception") or data.get("moodle_exception"):
                """
                Moodle sends HTTP 200 responses with error information in JSON, example:
                { 'errorcode': 'criteriaerror', 'debuginfo':
                'You can not search on this criteria: shortname', 'exception':
                'moodle_exception', 'message': 'Missing permissions to search on
                a criterion. (You can not search on this criteria: shortname)' }
                """
                return "Error: {}".format(data["message"])

    return data


@click.command(help="Get Moodle category data by name.")
@click.help_option("-h", "--help")
@click.argument("name", type=str)
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
def main(name, token, domain):
    """Get category data by name (e.g., '2022SP')."""
    global config
    if token:
        config.token = token
    if domain:
        config.url = domain + "/webservice/rest/server.php"

    result = get_mdl_categories({"name": name})
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
