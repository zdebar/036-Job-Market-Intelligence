# Dashboard scope

- Power BI: interactive report
- Primary grain: one active canonical job
- Source postings: internal dbt input only
- Inactive jobs: excluded
- General skills: excluded
- Technical skills: included

## Filters

- Location
- Role
- Seniority
- Company

## Outputs

- Position count by role
- Technical skill count
- Technical skill percentage
- Salary coverage
- Average salary in CZK/month
- Canonical job detail

## Implementation

1. Define KPI measures
2. Classify technical skills
3. Create canonical skill mart
4. Add dbt tests
5. Build Power BI model and slicers
6. Validate filtered results
7. Configure refresh
