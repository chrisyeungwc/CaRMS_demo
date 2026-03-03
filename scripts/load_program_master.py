from pathlib import Path

from sqlmodel import select

from app.db import create_db_and_tables, get_session
from app.models import ProgramMaster
from scripts.xlsx_utils import iter_xlsx_rows


SOURCE_PATH = Path(__file__).resolve().parents[1] / "source" / "1503_program_master.xlsx"


def iter_program_master_rows():
    rows = iter_xlsx_rows(SOURCE_PATH)
    next(rows)

    for row in rows:
        if not row or row[5] is None:
            continue

        yield {
            "discipline_id": int(row[1]),
            "discipline_name": str(row[2]).strip(),
            "school_id": int(row[3]),
            "school_name": str(row[4]).strip(),
            "program_stream_id": int(row[5]),
            "program_stream_name": str(row[6]).strip(),
            "program_site": str(row[7]).strip(),
            "program_stream": str(row[8]).strip(),
            "program_name": str(row[9]).strip(),
            "program_url": str(row[10]).strip(),
        }


def upsert_program_master_rows() -> int:
    create_db_and_tables()

    inserted_or_updated = 0

    with get_session() as session:
        for row in iter_program_master_rows():
            existing = session.exec(
                select(ProgramMaster).where(
                    ProgramMaster.program_stream_id == row["program_stream_id"]
                )
            ).first()

            if existing is None:
                session.add(ProgramMaster(**row))
            else:
                existing.discipline_id = row["discipline_id"]
                existing.discipline_name = row["discipline_name"]
                existing.school_id = row["school_id"]
                existing.school_name = row["school_name"]
                existing.program_stream_name = row["program_stream_name"]
                existing.program_site = row["program_site"]
                existing.program_stream = row["program_stream"]
                existing.program_name = row["program_name"]
                existing.program_url = row["program_url"]

            inserted_or_updated += 1

        session.commit()

    return inserted_or_updated


if __name__ == "__main__":
    count = upsert_program_master_rows()
    print(f"Loaded {count} program master rows from {SOURCE_PATH.name}")
