# Settings

## Cíl

Připravit opakovatelné lokální prostředí pro první fázi projektu podle
`00_planning`: Git, Python, uv, základní strukturu, testy a linting.

## Stručný postup

1. Inicializovat Git a vytvořit základní soubory (`README.md`, `.gitignore`,
   `.env.example`). Tajné hodnoty patří pouze do lokálního `.env` a nesmí se
   commitovat.
2. Zvolit a zapsat podporovanou verzi Pythonu, inicializovat projekt přes `uv`
   a vytvořit virtuální prostředí.
3. Založit základní strukturu `src/`, `tests/` a potřebné adresáře pro další
   fáze.
4. Přidat `pytest` a `ruff` jako vývojové závislosti a nastavit jejich
   konfiguraci v `pyproject.toml`.
5. Přidat alespoň jeden smoke test a ověřit prostředí příkazy:

   ```text
   uv run ruff format --check .
   uv run ruff check .
   uv run pytest
   ```

6. Teprve po úspěšném ověření uložit změny do Gitu. Docker, PostgreSQL,
   migrace a cloudové secrets řešit až v odpovídajících pozdějších fázích.

## Výsledek

Projekt lze po čistém checkoutu lokálně nainstalovat přes `uv`, spustit testy a
ověřit formátování i linting bez ruční konfigurace mimo dokumentované lokální
hodnoty.
