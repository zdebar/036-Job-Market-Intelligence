# Settings

## Objective

Prepare a reproducible local environment for the first project phase described
in `00_planning`: Git, Python, uv, the basic structure, tests, and linting.

## Procedure

1. Initialize Git and create the basic files (`README.md`, `.gitignore`, and
   `.env.example`). Secrets belong only in the local `.env` file and must not
   be committed.
2. Select and document the supported Python version, initialize the project
   with `uv`, and create the virtual environment.
3. Create the basic `src/` and `tests/` structure together with the directories
   required for later phases.
4. Add `pytest` and `ruff` as development dependencies and configure them in
   `pyproject.toml`.
5. Add at least one smoke test and verify the environment with:

   ```text
   uv run ruff format --check .
   uv run ruff check .
   uv run pytest
   ```

6. Save the changes to Git only after successful verification. Address Docker,
   PostgreSQL, migrations, and cloud secrets in their respective later phases.

## Result

After a clean checkout, the project can be installed locally with `uv`, tested,
and checked for formatting and linting without manual configuration beyond the
documented local values.

## Language policy

- Repository documentation, decision notes, code comments, user-facing CLI
  messages, commit messages, and pull request descriptions are written in
  English.