# Basic Ingestion

## Sources

| Source                       | URL                                                                               | Access                                                            | Status                   |
| ---------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------ |
| **Greenhouse Job Board API** | [docs.greenhouse.io](https://docs.greenhouse.io/job-board.html)                   | Public GET API, JSON, full job content                            | **First implementation** |
| Lever Postings API           | [github.com/lever/postings-api](https://github.com/lever/postings-api)            | Public job postings, JSON                                         | Later                    |
| Ashby job board/API          | [developers.ashbyhq.com](https://developers.ashbyhq.com/reference/jobpostinglist) | Public job boards; API access depends on endpoint and permissions | Later                    |
| Company-specific career API  | Individual company career site                                                    | Public API, JSON, RSS or feed where available                     | Case by case             |

Examples of companies with Czech or Prague technology roles on these systems include
Make, Second Foundation Tech, Capco, Ataccama, Pipedrive, SatoshiLabs/Trezor and
others.

# Raw Storage

## Layout

Each board and run has its own directory:

    data/01_bronze/<source_key>/<date>/<run_id>/
      response.json
      metadata.json

The run_id is explicit and unique. A repeated download is a new run and does
not overwrite an earlier response, even when the payload is identical.

## Initial implementation

The initial implementation uses the Greenhouse Job Board API, Lever Postings
API, and Ashby job-board API. A shared HTTP client, raw-storage helper, TOML
configuration loader, and ingestion runner are adapted from project 035.

Run a preview with:

```text
uv run job-market-ingest --dry-run
```

Run the configured downloads with:

```text
uv run job-market-ingest
```

Raw responses are not committed to Git. They are the input for later parsing
and normalization phases.
