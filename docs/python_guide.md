# Python Overview

This is a general introduction to Python for data, automation, and backend
projects. It explains the language, the most important programming concepts,
common project structures, and the practices that make Python code reliable.

It is intentionally language-focused. The project-specific implementation
details belong in the source code and the project README.

## 1. What Python is

Python is a high-level, general-purpose programming language. A Python program
is usually executed by an interpreter, which reads the source code and runs it
inside a Python runtime.

Python is popular for data work because it combines:

- readable syntax;
- a large standard library;
- a strong ecosystem for HTTP, databases, testing, and analytics;
- interactive development through a REPL and notebooks;
- support for both small scripts and large applications.

Python is dynamically typed: names do not have a fixed type, and type checks
usually happen while the program runs. Type hints can describe intended types
and allow static tools to detect many mistakes before execution, but annotations
do not automatically validate values at runtime.

## 2. The core mental model

### 2.1 Names refer to objects

Variables are names bound to objects. Assignment binds a name; it does not
copy the object automatically.

```python
numbers = [1, 2, 3]
other_numbers = numbers
other_numbers.append(4)

assert numbers == [1, 2, 3, 4]
```

This matters because mutable objects such as lists and dictionaries can change
through any reference to them. Immutable objects such as strings, integers,
tuples, and frozen dataclasses cannot be changed in place.

### 2.2 Expressions and statements

An expression produces a value:

```python
total = price * quantity
is_valid = total >= 0
```

A statement performs an action or controls execution:

```python
if is_valid:
    print(total)
```

Python uses indentation to define blocks. Consistent four-space indentation is
the standard convention.

### 2.3 Truth values and identity

Values such as `None`, `False`, `0`, empty strings, and empty collections are
false in a Boolean context. Most other values are true.

Use `is` for identity checks, especially for `None`:

```python
if value is None:
    return default_value
```

Use `==` for value equality. `is` should not be used to compare ordinary
strings or numbers.

## 3. Built-in data types

| Type | Typical use | Mutable? |
|---|---|---:|
| `str` | Text | No |
| `int`, `float`, `complex` | Numbers | No |
| `bool` | True/false values | No |
| `None` | Missing or absent value | No |
| `list` | Ordered collection that may change | Yes |
| `tuple` | Ordered fixed collection | No |
| `dict` | Key-value mapping | Yes |
| `set` | Unique values and membership checks | Yes |
| `bytes` | Raw binary data | No |

Choose a type according to the meaning of the data. A tuple can communicate
that a sequence is fixed; a set communicates that duplicates do not matter; a
dictionary communicates lookup by key.

### 3.1 Lists, tuples, sets, and dictionaries

```python
names = ["Ada", "Grace"]
coordinates = (50.08, 14.44)
unique_tags = {"python", "sql"}
person = {"name": "Ada", "active": True}

for name in names:
    print(name)

if "python" in unique_tags:
    print(person["name"])
```

Use `.get()` when a dictionary key is optional:

```python
department = person.get("department")
```

Do not use a mutable object as a default argument:

```python
# Avoid: the same list is reused between calls.
def add_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

# Prefer:
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    result = [] if items is None else list(items)
    result.append(item)
    return result
```

### 3.2 Strings and formatting

Use f-strings for readable interpolation:

```python
job_count = 12
message = f"Found {job_count} job postings"
```

Do not use string interpolation to build SQL commands or shell commands. Those
boundaries require parameterization and careful escaping.

### 3.3 Comprehensions

Comprehensions are concise transformations when the logic remains easy to
read:

```python
active_names = [name for name, active in records if active]
name_by_id = {record.id: record.name for record in records}
```

Use an ordinary loop when the comprehension would contain several conditions,
side effects, or complicated expressions.

## 4. Control flow

Python provides `if`/`elif`/`else`, `for`, `while`, `match`, `break`,
`continue`, and `return`.

```python
for record in records:
    if record.is_deleted:
        continue
    if record.status == "active":
        process(record)
```

Use `match` when matching a small number of known structural cases:

```python
match event:
    case {"type": "created", "id": record_id}:
        handle_created(record_id)
    case {"type": "deleted", "id": record_id}:
        handle_deleted(record_id)
    case _:
        handle_unknown(event)
```

Keep branching close to the business rule it represents. If a function needs
many nested branches, extract named functions or represent the cases as data.

## 5. Functions

A function should have a clear purpose, inputs, output, and side effects.

```python
def calculate_total(price: float, quantity: int) -> float:
    """Return the total price before tax."""
    if quantity < 0:
        raise ValueError("quantity cannot be negative")
    return price * quantity
```

Good function boundaries make code easier to test. A pure function depends only
on its arguments and does not modify external state:

```python
def normalize_name(value: str) -> str:
    return " ".join(value.split()).casefold()
```

Side-effecting functions should make the side effect visible in their purpose
or documentation. Examples include reading a file, making an HTTP request,
writing to a database, or sending a message.

### 5.1 Arguments and return values

Prefer explicit arguments over hidden global state. Keyword-only arguments are
useful for options:

```python
def fetch_records(
    endpoint: str,
    *,
    timeout_seconds: float = 10.0,
    retry_count: int = 2,
) -> list[dict[str, object]]:
    ...
```

Return structured values when several outputs belong together. A dataclass is
often clearer than a tuple whose positions must be remembered.

### 5.2 Scope and closures

Names are resolved through local, enclosing, global, and built-in scopes. Keep
important dependencies explicit instead of relying on mutable globals.

Closures can be useful for small factories, but a class or a dataclass is often
clearer when state has several fields or operations.

## 6. Exceptions and error handling

Exceptions represent abnormal conditions or a value that violates a function's
contract. Raise a specific exception with useful context:

```python
def parse_count(value: str) -> int:
    try:
        count = int(value)
    except ValueError as error:
        raise ValueError(f"Invalid count: {value!r}") from error
    if count < 0:
        raise ValueError("count cannot be negative")
    return count
```

Catch exceptions where the program can recover, add context, or convert them
to a user-facing result. Do not catch `Exception` broadly just to hide a
failure:

```python
# Avoid
try:
    run_job()
except Exception:
    pass
```

Use `finally` for cleanup that must happen regardless of success. Prefer a
context manager when one is available.

## 7. Modules, packages, and imports

A module is a `.py` file. A package is a directory of related modules. Keep
modules cohesive: one module should have a recognizable responsibility.

```text
src/
  application/
    __init__.py
    config.py
    domain.py
    service.py
    adapters/
      __init__.py
      database.py
tests/
  test_service.py
```

Prefer absolute package imports:

```python
from application.domain import Job
```

Avoid running an internal file directly if that makes its imports depend on the
current working directory. Expose a console entry point or run the module with
`python -m package.module`.

Keep imports at the top of the file. Import cycles usually indicate that
responsibilities or dependency direction need to be reorganized.

## 8. Classes, dataclasses, and protocols

Use a class when an object owns state and behavior or represents a stable
capability.

```python
class RateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.used = 0

    def allow(self) -> bool:
        if self.used >= self.limit:
            return False
        self.used += 1
        return True
```

Use a dataclass for data with named fields:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class JobPosting:
    source_id: str
    title: str
    location: str | None = None
```

`frozen=True` is useful for value objects that should not change after
validation. It does not make nested mutable fields deeply immutable.

Use a `Protocol` when a function needs behavior rather than a particular class:

```python
from typing import Protocol

class Clock(Protocol):
    def now(self) -> float: ...

def create_run(clock: Clock) -> float:
    return clock.now()
```

This makes dependencies easy to replace in tests without forcing inheritance.

## 9. Type hints

Type hints document interfaces and enable tools such as type checkers and IDEs.
Use modern syntax for new Python versions:

```python
from collections.abc import Iterable, Mapping

def active_ids(records: Iterable[Mapping[str, object]]) -> list[str]:
    return [str(record["id"]) for record in records if record.get("active")]
```

Useful conventions:

| Annotation | Meaning |
|---|---|
| `str | None` | A string may be absent |
| `list[str]` | A mutable list of strings |
| `Sequence[str]` | Read-only sequence behavior is sufficient |
| `Mapping[str, object]` | Mapping is read, not mutated |
| `Callable[[str], int]` | A function-like dependency |
| `TypeVar` / generic | A type relationship should be preserved |
| `Any` | Type information is intentionally unavailable |

Type hints are not validation. Validate untrusted JSON, configuration, and
database results at the boundary before converting them to typed domain values.

## 10. Iterators, generators, and context managers

An iterable can produce values. A generator produces them lazily, which is
useful for large files or streams:

```python
from collections.abc import Iterator

def read_nonempty_lines(path: str) -> Iterator[str]:
    with open(path, encoding="utf-8") as file:
        for line in file:
            value = line.strip()
            if value:
                yield value
```

A context manager owns setup and cleanup:

```python
with open("records.json", encoding="utf-8") as file:
    payload = file.read()
```

Use `contextlib.contextmanager` or a class implementing `__enter__` and
`__exit__` when creating a custom resource boundary.

## 11. I/O and integration boundaries

Separate pure business logic from external effects:

```text
input boundary -> validation/parsing -> domain logic -> output boundary
```

Typical boundaries include:

- HTTP APIs and retries;
- files and object storage;
- databases and transactions;
- environment variables and configuration files;
- queues, emails, and external services.

Keep these boundaries small and inject clients or repositories into the code
that uses them. This makes unit tests deterministic and prevents business logic
from depending on a live service.

### 11.1 HTTP

Set explicit timeouts, handle status codes, validate response shape, and avoid
logging credentials or personal data. Retries should be limited to failures
that are safe to retry and should use backoff.

### 11.2 Files

Use `pathlib.Path`, specify text encodings, and write files atomically when a
partial output would be harmful. Define whether a file is replaceable,
append-only, or an immutable input.

### 11.3 Databases

Use parameterized queries for values and explicit transaction boundaries:

```python
cursor.execute(
    "SELECT id, title FROM jobs WHERE status = %s",
    ("active",),
)
```

Never build SQL values with f-strings. Dynamic identifiers require a database
library's identifier-quoting mechanism and should come from a controlled list.

## 12. Configuration and secrets

Configuration should be loaded at the application boundary and passed into the
components that need it. Keep secrets outside source control.

```python
import os

database_url = os.environ["DATABASE_URL"]
```

Use a committed example file to document required variables. Distinguish:

- required settings, which should fail clearly when absent;
- defaults that are safe for local development;
- secrets, which should never have a committed default.

## 13. Concurrency and asynchronous code

Use synchronous code when work is CPU-bound or the program is simple. Use
`asyncio` when many tasks spend most of their time waiting for I/O and the
libraries involved support async operation.

```python
import asyncio

async def main() -> None:
    results = await asyncio.gather(fetch("a"), fetch("b"))
    print(results)

asyncio.run(main())
```

Do not call blocking file, database, or HTTP operations directly in an async
event loop without an appropriate async library or executor. Concurrency does
not make a CPU-heavy operation faster by itself; multiprocessing or a native
extension may be more appropriate.

## 14. Testing

Tests describe behavior that should remain true. A practical test portfolio
contains:

- unit tests for pure functions;
- integration tests for database and filesystem behavior;
- contract tests for external payloads;
- end-to-end tests for critical workflows.

Pytest example:

```python
def test_normalize_name_collapses_whitespace() -> None:
    assert normalize_name("  Data   Engineer ") == "data engineer"
```

Use Arrange, Act, Assert. Test edge cases such as empty input, missing values,
duplicates, invalid types, time boundaries, and repeated execution.

Mock a boundary when the test is about business logic. Use a real disposable
service when the test is specifically about integration behavior.

## 15. Packaging and tooling

A typical modern workflow is:

```powershell
uv init
uv add httpx
uv add --dev pytest ruff
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Use a virtual environment or a tool such as `uv` so dependencies are isolated
from the system Python. Commit the lock file when the project uses one.

The `pyproject.toml` file commonly contains project metadata, dependencies,
tool configuration, and console entry points. Keep build configuration,
runtime configuration, and secrets conceptually separate.

## 16. Idempotency and determinism

An operation is idempotent when executing it repeatedly has the same intended
result as executing it once. This is important for ingestion, jobs, migrations,
and scheduled pipelines.

Before implementing a write, define:

1. the natural or technical key;
2. what happens when the same input arrives twice;
3. how corrections are applied;
4. what happens when a child collection becomes empty;
5. which work belongs in one transaction.

Use stable ordering and explicit tie-breakers whenever the result must be
repeatable.

## 17. Common mistakes

- using a mutable default argument;
- catching broad exceptions and hiding failures;
- mixing parsing, business rules, and database writes in one function;
- relying on the current working directory for paths;
- hard-coding secrets;
- interpolating values into SQL or shell commands;
- using global mutable state instead of explicit dependencies;
- assuming a type annotation validates untrusted data;
- adding abstractions before the repeated behavior is understood;
- testing only the happy path.

## 18. Practical review checklist

Before considering a Python change complete, check:

- Is the responsibility of each function and module clear?
- Are external effects visible and isolated?
- Are inputs validated at the boundary?
- Are errors specific, contextual, and observable?
- Are database and shell values parameterized?
- Is the behavior deterministic and safe to repeat?
- Are type hints useful rather than decorative?
- Are tests focused on behavior and edge cases?
- Are dependencies and configuration reproducible?
- Is the code readable without reconstructing hidden global state?

## 19. Further reading

- [Python tutorial](https://docs.python.org/3/tutorial/)
- [Python language reference](https://docs.python.org/3/reference/)
- [Python standard library](https://docs.python.org/3/library/)
- [Packaging User Guide](https://packaging.python.org/)
- [pytest documentation](https://docs.pytest.org/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [uv documentation](https://docs.astral.sh/uv/)
