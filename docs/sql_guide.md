# SQL Overview

This is a general introduction to SQL for relational databases and analytical
work. It explains how tables relate to one another, how queries are evaluated,
how to write safe and readable SQL, and how to reason about correctness and
performance.

The examples use broadly portable SQL. PostgreSQL-specific examples are marked
where they matter. SQL dialects differ in functions, data types, date syntax,
upsert syntax, and procedural features, so always check the target database.

## 1. What SQL is

SQL, or Structured Query Language, is a declarative language for working with
relational data. You describe the result you want; the database optimizer
chooses an execution plan.

SQL is used for several kinds of work:

| Area | Purpose |
|---|---|
| DDL | Define tables, views, indexes, and constraints |
| DML | Insert, update, and delete rows |
| DQL | Read and transform data with queries |
| TCL | Control transactions such as commit and rollback |
| DCL | Manage permissions and access |

SQL is not the same as a programming language. It is optimized for sets of
rows and relationships. Procedural loops are sometimes available, but a clear
set-based query is normally easier to optimize and maintain.

## 2. The relational model

A table represents a relation. Each row represents an occurrence of something,
and each column represents an attribute of that occurrence.

```text
customers
customer_id | name          | country
------------+---------------+--------
1           | Ada Lovelace  | UK
2           | Grace Hopper  | US
```

The database should know how rows are identified and how tables relate. A
primary key identifies one row. A foreign key points to a row in another table.

Do not confuse a physical table with the meaning of its rows. Always state the
grain:

```text
One row in customer_orders represents one order placed by one customer.
One row in order_items represents one product line within one order.
```

If a query joins these two tables, it can return multiple rows per order. That
is correct at the order-item grain and incorrect if the intended result is one
row per order.

## 3. SQL query structure

A basic query has this form:

```sql
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id
WHERE c.country = 'UK'
GROUP BY
    c.customer_id,
    c.name
HAVING COUNT(o.order_id) > 0
ORDER BY order_count DESC;
```

The logical processing order is approximately:

```text
FROM and JOIN
    -> WHERE
    -> GROUP BY
    -> HAVING
    -> SELECT
    -> DISTINCT
    -> ORDER BY
    -> LIMIT/OFFSET
```

This explains why a `SELECT` alias is usually unavailable in `WHERE`, and why
an aggregate cannot normally be used in `WHERE`: those clauses are evaluated at
different logical stages.

## 4. Selecting and filtering

Select the columns that consumers need. Avoid `SELECT *` in durable views,
models, exports, and application code because upstream schema changes can alter
the result unexpectedly.

```sql
SELECT
    job_id,
    title,
    published_at
FROM job_postings
WHERE status = 'active'
  AND published_at >= DATE '2025-01-01';
```

Use parentheses when mixing `AND` and `OR`:

```sql
WHERE status = 'active'
  AND (work_mode = 'remote' OR work_mode = 'hybrid')
```

Use `IN` for a small known set, `BETWEEN` for an inclusive range, and `LIKE`
or a dialect-specific regular expression operator for text patterns. Be aware
that a leading wildcard such as `LIKE '%engineer'` often prevents a normal
B-tree index from being useful.

## 5. NULL and three-valued logic

`NULL` means unknown, missing, or not applicable. It is not equal to zero, an
empty string, or another `NULL`.

```sql
WHERE published_at IS NULL
WHERE published_at IS NOT NULL
```

This does not work as many people first expect:

```sql
-- Wrong for missing values
WHERE published_at = NULL
```

Comparisons involving `NULL` evaluate to `UNKNOWN`. A `WHERE` clause keeps only
rows where the condition is `TRUE`.

Use `COALESCE` when a default is meaningful:

```sql
SELECT COALESCE(country, 'Unknown') AS country
FROM customers;
```

Do not use `COALESCE` to hide a data-quality problem unless the default has a
clear business meaning.

## 6. Joins and cardinality

Joins combine rows according to a relationship.

| Join | Keeps |
|---|---|
| `INNER JOIN` | Rows matching on both sides |
| `LEFT JOIN` | Every left row, plus matching right rows |
| `RIGHT JOIN` | Every right row, plus matching left rows |
| `FULL OUTER JOIN` | Rows from either side |
| `CROSS JOIN` | Every combination of both sets |
| `EXISTS` | Left rows for which a matching row exists |

The most common error is unexpected row multiplication. If one customer has
three orders and each order has four items, joining customers to orders and
items can produce twelve rows for that customer.

Before every join, state its expected relationship:

```text
customers 1 -> many orders
orders     1 -> many order_items
```

Then decide the intended output grain. Aggregate or deduplicate before joining
when the downstream result should remain at a higher grain.

### 6.1 Filter placement

These queries are not equivalent:

```sql
-- Keeps customers even when they have no recent order.
SELECT c.customer_id, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id
   AND o.created_at >= DATE '2025-01-01';

-- Removes customers without a recent order because WHERE rejects NULLs.
SELECT c.customer_id, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id
WHERE o.created_at >= DATE '2025-01-01';
```

Put a filter in `ON` when it defines which right-side rows may match while
preserving unmatched left rows. Put it in `WHERE` when unmatched rows should
be removed.

## 7. Aggregation

Aggregation changes the grain. `GROUP BY` creates one output row per distinct
combination of its grouping columns.

```sql
SELECT
    department_id,
    COUNT(*) AS posting_count,
    AVG(salary_min) AS average_min_salary,
    MAX(published_at) AS latest_published_at
FROM job_postings
GROUP BY department_id;
```

Every selected expression must either be grouped or aggregated. Use `HAVING`
for a condition on an aggregate:

```sql
HAVING COUNT(*) >= 10
```

Conditional aggregation is useful for several measures at the same grain:

```sql
SELECT
    company_id,
    COUNT(*) AS all_postings,
    COUNT(*) FILTER (WHERE status = 'active') AS active_postings,
    COUNT(*) FILTER (WHERE work_mode = 'remote') AS remote_postings
FROM job_postings
GROUP BY company_id;
```

The `FILTER` syntax is PostgreSQL and supported by several other databases. A
portable alternative is `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.

## 8. CTEs and subqueries

A common table expression (`WITH`) gives a name to an intermediate result:

```sql
WITH active_postings AS (
    SELECT job_id, company_id, published_at
    FROM job_postings
    WHERE status = 'active'
), company_counts AS (
    SELECT company_id, COUNT(*) AS posting_count
    FROM active_postings
    GROUP BY company_id
)
SELECT *
FROM company_counts
WHERE posting_count >= 5;
```

Use CTEs to make stages visible and to avoid repeating logic. A CTE is not
automatically a performance optimization; the database may inline it or
materialize it depending on the dialect and query.

Subqueries are useful when a value or set is needed for a surrounding query.
Prefer `EXISTS` when only existence matters:

```sql
SELECT c.customer_id, c.name
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.created_at >= CURRENT_DATE - INTERVAL '30 days'
);
```

`EXISTS` avoids creating duplicate customer rows when a customer has several
matching orders.

## 9. Window functions

Window functions calculate across related rows without collapsing them. They
are useful for ranking, running totals, comparisons, and deduplication.

```sql
SELECT
    job_id,
    company_id,
    published_at,
    ROW_NUMBER() OVER (
        PARTITION BY company_id
        ORDER BY published_at DESC, job_id
    ) AS company_recency_rank
FROM job_postings;
```

Common functions include `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`,
`FIRST_VALUE`, and cumulative `SUM` or `AVG`.

To keep only the first row per group, calculate the rank in a subquery or CTE
and filter outside it:

```sql
WITH ranked AS (
    SELECT
        p.*,
        ROW_NUMBER() OVER (
            PARTITION BY company_id
            ORDER BY published_at DESC, job_id
        ) AS row_number
    FROM job_postings AS p
)
SELECT *
FROM ranked
WHERE row_number = 1;
```

Always include a deterministic tie-breaker. Without one, the selected row may
change between executions.

## 10. Dates and time

Use a type that matches the meaning:

| Type | Meaning |
|---|---|
| `DATE` | Calendar date without a time |
| `TIME` | Time of day |
| `TIMESTAMP` | Date and time without timezone semantics |
| `TIMESTAMP WITH TIME ZONE` | An instant represented with timezone handling |
| `INTERVAL` | A duration |

Store instants consistently, commonly in UTC, and convert for presentation at
the edge of the system. Be explicit about inclusivity of time ranges:

```sql
WHERE occurred_at >= TIMESTAMP '2025-01-01 00:00:00'
  AND occurred_at <  TIMESTAMP '2025-02-01 00:00:00'
```

The half-open interval avoids double-counting events at a boundary.

## 11. Data types and expressions

Choose types based on domain meaning and expected operations:

- use integer or numeric types for quantities;
- use exact numeric/decimal types for money rather than floating point;
- use text types for labels and descriptions;
- use boolean for true/false state;
- use JSON only when the structure is genuinely variable or needs to be
  preserved as source detail;
- use arrays cautiously because a normalized child table is often easier to
  query and constrain.

Explicit casts make intent visible:

```sql
SELECT salary_min::numeric / NULLIF(salary_max, 0)
FROM job_postings;
```

`NULLIF` prevents division by zero. Do not silently convert invalid data to a
plausible value.

## 12. Constraints and keys

Constraints turn assumptions into database-enforced rules.

```sql
CREATE TABLE departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name TEXT NOT NULL,
    department_code TEXT NOT NULL UNIQUE
);

CREATE TABLE job_postings (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id BIGINT NOT NULL
        REFERENCES departments (department_id),
    title TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('active', 'inactive'))
);
```

Use:

- primary keys for row identity;
- foreign keys for referential integrity;
- `NOT NULL` for required values;
- `UNIQUE` for alternate or natural keys;
- `CHECK` for local domain rules;
- exclusion or specialized constraints when the database supports them.

Constraints do not replace analytical tests. A database can enforce a foreign
key while a model can still have the wrong grain or an incorrect business
filter.

## 13. INSERT, UPDATE, DELETE, and upserts

Use explicit column lists:

```sql
INSERT INTO departments (department_code, department_name)
VALUES ('ENG', 'Engineering');
```

An update should have a precise predicate and should be previewed with a
`SELECT` when the target is important:

```sql
UPDATE job_postings
SET status = 'inactive'
WHERE source_job_id = 'abc-123';
```

An upsert expresses what should happen when a key already exists. Syntax is
dialect-specific; PostgreSQL uses `INSERT ... ON CONFLICT`. Define the key and
the update semantics explicitly. Do not use an upsert as a substitute for
understanding duplicate records.

## 14. Transactions

A transaction groups changes into an all-or-nothing unit.

```sql
BEGIN;

UPDATE account
SET balance = balance - 100
WHERE account_id = 1;

UPDATE account
SET balance = balance + 100
WHERE account_id = 2;

COMMIT;
```

Use `ROLLBACK` when validation fails. Keep transactions short enough to avoid
unnecessary locks, but large enough that related changes cannot be observed in
an inconsistent state.

Migration files should follow the transaction behavior of their migration
runner. Never add `COMMIT` inside a migration when the runner expects to manage
the transaction.

## 15. Views, tables, and materialization

- A table stores rows physically and is useful when data is reused or the query
  is expensive.
- A view stores a query definition and calculates results when read.
- A materialized view stores the result and must be refreshed.

Choose materialization according to freshness, query cost, storage, and update
frequency. In transformation tools such as dbt, this decision is usually
configured per model.

## 16. Indexes and performance

An index is an access path, not a guarantee of speed. Create indexes for actual
filter, join, ordering, and uniqueness requirements.

Consider:

- indexed foreign keys used in joins;
- columns frequently filtered by selective predicates;
- composite index column order;
- partial indexes for a stable subset;
- the cost of maintaining indexes during writes;
- whether the table is large enough for an index to matter.

Inspect the plan instead of guessing:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

`ANALYZE` executes the query, so do not use it casually against an expensive
or mutating statement. Compare execution time, rows estimated versus actual,
join strategy, scans, sorting, and memory use.

Avoid premature optimization. First make the grain, joins, and result correct;
then measure the slow operation and improve the bottleneck.

## 17. SQL safety

Application code must parameterize values:

```python
cursor.execute(
    "SELECT * FROM jobs WHERE status = %s",
    (status,),
)
```

Do not construct SQL with string interpolation. Parameters protect values, but
they do not usually represent table or column names. Dynamic identifiers need a
trusted allow-list and the database driver's identifier-quoting facility.

Restrict production permissions. A reporting user should not need permission
to drop tables, change migrations, or write operational data.

## 18. Readable SQL style

Useful conventions include:

- one selected expression per line;
- explicit column lists;
- short, meaningful table aliases;
- `AS` for column aliases;
- uppercase SQL keywords;
- lowercase `snake_case` identifiers unless the database standard differs;
- one logical transformation per CTE;
- comments that explain why, not what the syntax already says;
- deterministic `ORDER BY` clauses when output is consumed by humans or tests.

Do not rely on ordering unless the query has `ORDER BY`. A database may return
rows in a different order after an index, statistics, or execution-plan change.

## 19. Common mistakes

- forgetting that a join can multiply rows;
- using `WHERE column = NULL`;
- turning a `LEFT JOIN` into an inner join with a right-side `WHERE` filter;
- grouping at the wrong grain;
- using `DISTINCT` to hide an incorrect join;
- using `SELECT *` in stable interfaces;
- counting nullable columns with `COUNT(column)` when `COUNT(*)` was intended;
- treating a timestamp as a local date without a timezone decision;
- putting business logic in a report without documenting it;
- changing an applied migration instead of adding a new one;
- interpolating values into SQL;
- adding indexes without measuring the workload.

## 20. Query review checklist

Before shipping a query, ask:

- What is one row in the result?
- What is the expected cardinality of every join?
- Can any join multiply rows unexpectedly?
- How are `NULL` values handled?
- Are filters applied at the intended stage?
- Are aggregates and grouping columns correct?
- Is ordering deterministic where it matters?
- Are values parameterized?
- Does the query need an index or a different materialization?
- Are dialect-specific features documented?

## 21. Further reading

- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [PostgreSQL tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [SQL standard overview](https://www.iso.org/standard/76583.html)
- [Use The Index, Luke](https://use-the-index-luke.com/)
- [SQL style guide](https://www.sqlstyle.guide/)
