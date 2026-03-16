import pytest

from .interns import make_enrollments, meets_program_criteria


@pytest.mark.parametrize(
    "input,expected",
    [
        # not an internship program
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Fake Program",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            [],
        ),
        # not 'in progress'
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "Suspended",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            [],
        ),
        # no email
        (
            {
                "CCA Email": None,
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            [],
        ),
        # domestic enrollment
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            [("a", "BARCH-INTRN", "Fall 2023")],
        ),
        # international enrollment
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Interior Design",
                "Is International Student": "Yes",
                "Latest Class Standing": "Third Year",
            },
            [("a", "INTER-INTRN", "Fall 2023"), ("a", "INTER-INTRN", "International")],
        ),
    ],
)
def test_make_enrollments(input, expected):
    assert make_enrollments(input, "Fall 2023") == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        # not in program
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            [],
        ),
        # in program
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Interior Design",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            [("a", "INTER-INTRN", "Fall 2023")],
        ),
    ],
)
def test_make_enrollment_program_filter(input, expected):
    assert make_enrollments(input, "Fall 2023", "Interior Design") == expected


@pytest.mark.parametrize(
    "student,program,expected",
    [
        # ARCHT first year, does not meet
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "First Year",
            },
            None,
            False,
        ),
        # ARCHT third year, meets
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            None,
            True,
        ),
        # MARCH 2nd year, also meets
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Graduate Architecture",
                "Is International Student": "Yes",
                "Latest Class Standing": "Second Year",
            },
            None,
            True,
        ),
        # Passing INTER to program filter
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Interior Design",
                "Is International Student": "Yes",
                "Latest Class Standing": "Third Year",
            },
            "Interior Design",
            True,
        ),
        # Passing INTER to program filter but student is 2nd year
        (
            {
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Interior Design",
                "Is International Student": "Yes",
                "Latest Class Standing": "Second Year",
            },
            "Interior Design",
            False,
        ),
    ],
)
def test_meets_program_criteria(student, program, expected):
    assert meets_program_criteria(student, program) == expected


# test list mode
@pytest.mark.parametrize(
    "input,expected",
    [
        # ARCHT first year, does not meet
        (
            {
                "Student": "fake name",
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "First Year",
            },
            [],
        ),
        # ARCHT third year, meets
        (
            {
                "Student": "fake name",
                "CCA Email": "a@cca.edu",
                "Primary Program of Study Record Status": "In Progress",
                "Primary Program of Study": "Architecture",
                "Is International Student": "",
                "Latest Class Standing": "Third Year",
            },
            ["fake name", "a@cca.edu"],
        ),
    ],
)
def test_make_enrollment_list_mode(input, expected):
    assert make_enrollments(input, "Fall 2023", list_mode=True) == expected
