import csv
import os
import re
from datetime import date
from html import unescape
from pathlib import Path
from typing import Any

import click
from dotenv import dotenv_values
from requests import HTTPError, Response, get

# a tripartite set of API calls:
# 1. get all courses in the Internships category (may need to weed out demo/template courses)
# wsfunction: core_course_get_courses_by_field
# 2. get all Feedback activities from courses (1 request, no need for iteration)
# wsfunction: mod_feedback_get_feedbacks_by_courses
# 3. iterate over feedbacks, get all their analyses
# wsfunction: mod_feedback_get_analysis

# Find project root (where .env file is) by looking for pyproject.toml
current_dir: Path = Path(__file__).resolve().parent
project_root: Path = current_dir.parent
while not (project_root / "pyproject.toml").exists() and project_root != project_root.parent:
    project_root = project_root.parent

conf: dict[str, Any] = {
    **dotenv_values(project_root / ".env"),  # load private env from project root
    **os.environ,  # override loaded values with environment variables
}
conf["URL"] = conf.get("DOMAIN", "") + "/webservice/rest/server.php"


def debug(s: str) -> None:
    """print message only if DEBUG env var is True

    Args:
        s (str): message to print
    """
    # can't just .get() because the string "False" is truthy
    if conf.get("DEBUG") and bool(conf["DEBUG"]):
        print(s)


def http_error(resp: Response) -> None:
    """print HTTP error details

    Args:
        resp (Response): HTTP response object from requests library
    """
    print(f"HTTP Error {resp.status_code}")
    print(resp.headers)
    print(resp.text)


# 1 get courses
def get_courses() -> list[dict]:
    """get all courses in the Internships category

    Returns:
        list[dict]: list of course dicts
    """
    service: str = "core_course_get_courses_by_field"
    format: str = "json"
    params: dict[str, str] = {
        # see https://moodle.cca.edu/admin/settings.php?section=webservicetokens
        "wstoken": conf["TOKEN"],
        "wsfunction": service,
        "moodlewsrestformat": format,
        "field": "category",
        "value": conf["CATEGORY"],
    }

    response: Response = get(conf["URL"], params=params)
    try:
        response.raise_for_status()
    except HTTPError:
        http_error(response)

    data = response.json()
    debug(
        f"Found {len(data['courses'])} courses in category {conf['DOMAIN']}/course/management.php?categoryid={conf['CATEGORY']}"
    )
    return data["courses"]


def write_csv(feedbacks: list[dict], label: str, output_dir: Path) -> None:
    """write feedbacks to a CSV file

    Args:
        feedbacks (list[dict]): list of feedback dicts with responses stored in anonattempts property
        label (str): label to use in the filename
        output_dir (Path): directory to write the CSV file to
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename: Path = output_dir / f"{label}-responses.csv"
    # example attempts structure:
    #   "anonattempts": [
    #     {
    #       "id": 5817,
    #       "courseid": 0,
    #       "userid": 11,
    #       "timemodified": 1683236827,
    #       "fullname": "Rey .",
    #       "responses": [
    #         {
    #           "id": 10490,
    #           "name": "Your Phone Number",
    #           "printval": "323-123-9876",
    #           "rawval": "323-123-9876"
    #         },
    #   ...objects for each question, below is end of "attempts" array
    #   ],
    # extract columns from first response to first feedback
    columns: list[str] = []
    for r in feedbacks[0]["anonattempts"][0]["responses"]:
        # find (label) and extract it from parentheses
        label_matches = re.match(r"^\(.*\)", r["name"].strip())
        if label_matches:
            columns.append(label_matches[0][1:-1])
        else:
            raise Exception(
                f"No label for question '{r['name']}' in feedback {feedbacks[0]['id']} in course {feedbacks[0]['courseid']}"
            )

    # TODO use DictWriter instead? We want to be careful not to place the wrong values in a column
    with open(filename, mode="w") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for feedback in feedbacks:
            for attempt in feedback["anonattempts"]:
                # use the "printval" property for Connection question, rawval for others
                row: list[Any] = []
                for response in attempt["responses"]:
                    if re.match(r"\(connection\)", response["name"].lower()):
                        row.append(unescape(response["printval"]))
                    else:
                        row.append(unescape(response["rawval"]))
                writer.writerow(row)

    debug(f"Wrote {sum([len(f['anonattempts']) for f in feedbacks])} responses to {filename}")


def course_ids(courses) -> list[str]:
    """return list of course ids from list of courses, skip ignored courses

    Args:
        courses (list[dict]): list of course dicts with at least an "id" property

    Returns:
        list[str]: list of course ids as strings
    """
    ids: list[str] = [
        str(c["id"]) for c in courses if str(c["id"]) not in conf["IGNORED_COURSES"].split(",")
    ]
    return ids


# 2: get feedbacks
def get_feedbacks(courses) -> list[dict]:
    """given a list of courses, return the feedback activities within them

    Args:
        courses (list[dict]): list of course dicts containing at least an id property

    Returns:
        list[dict]: list of feedback activity dicts
    """
    ids: list[str] = course_ids(courses)

    service: str = "mod_feedback_get_feedbacks_by_courses"
    format: str = "json"
    params: dict[str, str] = {
        # see https://moodle.cca.edu/admin/settings.php?section=webservicetokens
        "wstoken": conf["TOKEN"],
        "wsfunction": service,
        "moodlewsrestformat": format,
        "courseids[]": ",".join(ids),
    }
    # each course id is its own URL parameter, weird PHP behavior
    # ! potential bug where large number of courses -> too long URL
    for idx, id in enumerate(ids):
        params[f"courseids[{idx}]"] = id

    response: Response = get(conf["URL"], params=params)
    try:
        response.raise_for_status()
    except HTTPError:
        http_error(response)

    data = response.json()
    feedbacks: list[dict[str, Any]] = data.get("feedbacks", [])
    # example feedback structure:
    # {
    #   "id": 1520,
    #   "course": 5204,
    #   "name": "Submit Employer and Intern Information",
    #   "intro": "",
    #   "introformat": 1,
    #   "anonymous": 2,
    #   "multiple_submit": false,
    #   "autonumbering": f  alse,
    #   "page_after_submitformat": 1,
    #   "publish_stats": false,
    #   "completionsubmit": true,
    #   "coursemodule": 239207,
    #   "introfiles": []
    # }
    debug(f"Found {len(feedbacks)} Feedback activities")
    return feedbacks


def feedback_type(feedback: dict[str, Any]) -> str | None:
    """classify feedback as either an internship information or evaluation activity, or neither
    the returned string must match the name of the list in get_responses that it's appended to

    Args:
        feedback (dict): feedback dict with name property

    Returns:
        str|None: either "internships", "evaluations", or None
    """
    # trim whitespace and lowercase for easier matching
    name = feedback["name"].lower().strip()
    if "submit employer and intern information" in name:
        return "internships"
    elif "evaluation" in name:
        return "evaluations"
    else:
        return None


# 3: get analyses
def get_responses(feedbacks) -> tuple[list[dict], list[dict]]:
    """given a list of feedback activities, return two lists of responses:
    1. internship information ("Employer and Intern Information" feedbacks)
    2. student evaluations ("Evaluation" feedbacks)

    Args:
        feedbacks (list[dict]): list of feeedback activity dicts

    Returns:
        list[dict], list[dict]: list of internship responses, list of evaluation responses
    """
    internships = []
    evaluations = []
    for fdbk in feedbacks:
        # skip feedbacks that aren't internships or evaluations
        type = feedback_type(fdbk)
        if type:
            # see note in readme about the difference between these 2 functions
            service: str = "mod_feedback_get_responses_analysis"
            # service = 'mod_feedback_get_analysis'
            format: str = "json"
            params: dict[str, str] = {
                "wstoken": conf["TOKEN"],
                "wsfunction": service,
                "moodlewsrestformat": format,
                "feedbackid": fdbk["id"],
            }
            response = get(conf["URL"], params=params)
            try:
                response.raise_for_status()
            except HTTPError:
                http_error(response)

            data = response.json()
            # TODO handle warnings array & check for its presence in other wsfunction data
            # example analysis structure:
            # {
            #   "attempts": []
            #   "totalattempts": 0,
            #   "anonattempts": [...],
            #   "totalanonattempts": 10,
            #   "warnings": []
            # }
            debug(
                f"{len(data['anonattempts'])} attempts on Feedback {fdbk['id']} {conf['DOMAIN'] + '/mod/feedback/show_entries.php?id=' + str(fdbk['coursemodule'])}"
            )

            if data["totalanonattempts"] > 0:
                locals()[type].append(data)

    return internships, evaluations


@click.command(help="Combine Moodle internship feedback responses into CSV files.")
@click.help_option("-h", "--help")
@click.option(
    "--output-dir",
    "-o",
    default="data",
    help="Directory to write CSV files to (default: data)",
    type=click.Path(path_type=Path),
)
@click.option(
    "--category",
    "-c",
    help="Moodle category ID to fetch courses from (overrides .env)",
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
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug output",
)
def main(output_dir, category, token, domain, debug):
    """Fetch and combine internship feedback from Moodle."""
    # Override config with CLI options if provided
    if category:
        conf["CATEGORY"] = category
    if token:
        conf["TOKEN"] = token
    if domain:
        conf["DOMAIN"] = domain
        conf["URL"] = domain + "/webservice/rest/server.php"
    if debug:
        conf["DEBUG"] = "true"

    # Validate required config
    if not conf.get("TOKEN") or not conf.get("DOMAIN") or not conf.get("CATEGORY"):
        click.echo(
            "Error: TOKEN, DOMAIN, and CATEGORY must be set in .env or via CLI options",
            err=True,
        )
        exit(1)

    courses = get_courses()
    feedbacks = get_feedbacks(courses)
    internships, evaluations = get_responses(feedbacks)
    today = date.today().isoformat()
    write_csv(internships, f"{today}-internships", output_dir)
    write_csv(evaluations, f"{today}-evaluations", output_dir)
    click.echo(f"Wrote CSV files to {output_dir}")


if __name__ == "__main__":
    main()
