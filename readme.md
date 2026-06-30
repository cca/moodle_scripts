# Moodle Scripts

_External_ scripts run outside Moodle to interact with its data, whether through REST APIs or other means. See also: CCA [moodle_cli](https://github.com/cca/moodle_cli) which is for internal scripts run on the Moodle server, such as our enrollment sync.

## Contents

These used to be separate repositories but the enroll scripts were converted into this one and the others were archived.

1. [combine_feedbacks](./combine_feedbacks/readme.md) - Combine multiple Moodle feedback activities into a single CSV file for easier analysis.
2. [enroll](./enroll/readme.md) - create bulk enrollment CSVs for internships and NSO courses.
3. [rest_apis](./rest_apis/readme.md) - examples of interacting with Moodle REST APIs.

## Setup

General prerequisites are `uv` and a modern python 3. Individual scripts may have additional data or authentication requirements; see their readme files.

```sh
uv sync
uv run pytest # only enroll has tests at this time
```

Scripts that interact with Moodle's REST API use an `.env` file in the project root for authentication and configuration. Create a `.env` file based on the provided `example.env`:

```sh
cp example.env .env
# Edit .env with your actual values
```

## Linting & Formatting

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```sh
uv run ruff check          # lint all Python files
uv run ruff format         # format all Python files
```

## LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)
