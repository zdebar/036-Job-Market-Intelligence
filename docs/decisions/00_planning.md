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

## Postup hlavních fází

| Fáze | Stav | Název                          | Výsledek                                             |
| ---- | ---- | ------------------------------ | ---------------------------------------------------- |
| 0    | [x]  | Planning                       | Cíle, pojmy, rozsah a rozhodnutí                     |
| 1    | [x]  | Project foundation             | Git, Python, uv, testy, linting a základní struktura |
| 2    | [ ]  | Database foundation            | PostgreSQL, Docker, migrace a seed data              |
| 3    | [ ]  | Basic ingestion                | Stažení dat, Raw Storage                             |
| 4    | [ ]  | Extraction and normalization   | Převod zdrojových dat na společný formát             |
| 5    | [ ]  | SQL analytics a data modellig  | První užitečné dotazy a reporty                      |
| 6    | [ ]  | Data modelling / dbt           | Staging, facts, dimensions, bridges a Gold views     |
| 7    | [ ]  | Dashboard                      | Power BI dashboard nad analytickou vrstvou           |
| 8    | [ ]  | Cloud foundation               | Azure Storage, Azure PostgreSQL a secrets            |
| 9    | [ ]  | Cloud orchestration            | Automatické běhy, retry, logování a monitoring       |
| 10   | [ ]  | AI extraction                  | LLM extrakce a validace strukturovaných údajů        |

## Postup volitelných fází
| Fáze | Stav | Název                          | Výsledek                                             |
| ---- | ---- | ------------------------------ | ---------------------------------------------------- |
| 11   | [ ]  | Optional technologies          | Databricks, PySpark, embeddings a semantic search    |


## Principy

- Začínáme lokálně a funkční části později přesouváme do Azure.
- Raw data se nemění a lze je znovu zpracovat.
- Každá fáze má nejdříve jasný výsledek a test.
- Nové technologie přidáváme pouze tehdy, když mají pro projekt smysl.
- `035` používáme pouze jako referenci; kód přebíráme postupně podle potřeby.
- AI, Databricks a semantic search jsou rozšíření, ne podmínka základní platformy.
