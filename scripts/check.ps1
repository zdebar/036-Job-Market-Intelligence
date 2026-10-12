uv sync
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

uv run pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

uv run ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

uv run ruff format --check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "All checks passed."