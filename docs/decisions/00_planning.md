# Planning

## Cíl projektu

Vytvořit datovou platformu pro sběr, strukturování a analýzu pracovních
nabídek.

Projekt má sloužit jako:

- praktický Data/AI Engineering projekt,
- portfolio ukázka,
- nástroj pro analýzu pracovního trhu.

## Základní tok dat

```text
zdroje
→ ingestion
→ raw storage
→ extraction a normalization
→ PostgreSQL
→ data quality a SQL analytics
→ dbt Gold
→ Power BI
→ Azure
```

## Hlavní technologie

| Technologie             | Úloha                                  |
| ----------------------- | -------------------------------------- |
| Git a GitHub            | Verze kódu, spolupráce a CI/CD         |
| Python a uv             | Aplikace, parsování a správa prostředí |
| httpx                   | HTTP komunikace se zdroji              |
| Docker a Docker Compose | Lokální provoz služeb                  |
| PostgreSQL              | Provozní a analytická databáze         |
| SQL migrace             | Řízení změn databázového schématu      |
| pytest a Ruff           | Testy, linting a formátování           |
| dbt                     | Analytická transformační vrstva        |
| Power BI                | Dashboardy a prezentace analytiky      |
| Azure                   | Cloudové uložení, běh a monitoring     |
| LLM API                 | Pozdější AI extrakce                   |

## Postup fází

| Fáze | Stav | Název                        | Výsledek                                             |
| ---- | ---- | ---------------------------- | ---------------------------------------------------- |
| 0    | [x]  | Planning                     | Cíle, pojmy, rozsah a rozhodnutí                     |
| 1    | [x]  | Project foundation           | Git, Python, uv, testy, linting a základní struktura |
| 2    | [ ]  | Database foundation          | PostgreSQL, Docker, migrace a seed data              |
| 3    | [ ]  | Basic ingestion              | Stažení dat z prvního zdroje                         |
| 4    | [ ]  | Raw storage                  | Neměnná response data a metadata                     |
| 5    | [ ]  | Extraction and normalization | Převod zdrojových dat na společný formát             |
| 6    | [ ]  | Data quality                 | Kontroly validnosti, úplnosti a konzistence          |
| 7    | [ ]  | SQL analytics                | První užitečné dotazy a reporty                      |
| 8    | [ ]  | Data modelling / dbt         | Staging, facts, dimensions, bridges a Gold views     |
| 9    | [ ]  | Dashboard                    | Power BI dashboard nad analytickou vrstvou           |
| 10   | [ ]  | Cloud foundation             | Azure Storage, Azure PostgreSQL a secrets            |
| 11   | [ ]  | Cloud orchestration          | Automatické běhy, retry, logování a monitoring       |
| 12   | [ ]  | AI extraction                | LLM extrakce a validace strukturovaných údajů        |
| 13   | [ ]  | Optional technologies        | Databricks, PySpark, embeddings a semantic search    |
| 14   | [ ]  | Production hardening         | Bezpečnost, náklady, zálohy a provoz                 |

## Principy

- Začínáme lokálně a funkční části později přesouváme do Azure.
- Raw data se nemění a lze je znovu zpracovat.
- Každá fáze má nejdříve jasný výsledek a test.
- Nové technologie přidáváme pouze tehdy, když mají pro projekt smysl.
- `035` používáme pouze jako referenci; kód přebíráme postupně podle potřeby.
- AI, Databricks a semantic search jsou rozšíření, ne podmínka základní platformy.
