from pathlib import Path

from sqlmodel import select

from app.db import create_db_and_tables, get_session
from app.models import Discipline
from scripts.xlsx_utils import iter_xlsx_rows


SOURCE_PATH = Path(__file__).resolve().parents[1] / "source" / "1503_discipline.xlsx"


def iter_discipline_rows():
    rows = iter_xlsx_rows(SOURCE_PATH)
    next(rows)

    for row in rows:
        if not row or row[0] is None:
            continue
        yield {
            "discipline_id": int(row[0]),
            "discipline": str(row[1]).strip(),
        }


def upsert_discipline_rows() -> int:
    create_db_and_tables()

    inserted_or_updated = 0

    with get_session() as session:
        for row in iter_discipline_rows():
            existing = session.exec(
                select(Discipline).where(Discipline.discipline_id == row["discipline_id"])
            ).first()

            if existing is None:
                session.add(Discipline(**row))
            else:
                existing.discipline = row["discipline"]

            inserted_or_updated += 1

        session.commit()

    return inserted_or_updated


if __name__ == "__main__":
    count = upsert_discipline_rows()
    print(f"Loaded {count} discipline rows from {SOURCE_PATH.name}")
