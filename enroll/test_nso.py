import os

import pytest
from click.testing import CliRunner

from .nso import main


def test_normal_nso():
    runner = CliRunner()
    result = runner.invoke(main, ["enroll/fixtures/nso.csv", "-c", "NSO-{type}-2024FA"])
    assert result.exit_code == 0

    with open("nso.csv") as f:
        lines = f.readlines()
        # "notaccaemail@gmail.com" student is skipped
        assert lines == [
            "username,course1,group1\n",
            "frosh,NSO-FRESH-2024FA,First Year\n",
            "intlgrad,NSO-GRAD-2024FA,Graduate\n",
            "intlgrad,NSO-GRAD-2024FA,International\n",
            "intltransfer,NSO-TRSFR-2024FA,Transfer\n",
            "intltransfer,NSO-TRSFR-2024FA,International\n",
            "seconddegree,NSO-TRSFR-2024FA,Second Degree\n",
        ]


def test_student_type_error():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["enroll/fixtures/error.csv", "-c", "NSO-{type}-2024FA", "-t", "Type"],
    )
    assert result.exit_code == 2
    assert result.exception is not None


# runs before & after each test but we do nothing before yielding the fixture
@pytest.fixture(autouse=True)
def delete_nso_csv():
    yield
    if os.path.exists("nso.csv"):
        os.remove("nso.csv")
