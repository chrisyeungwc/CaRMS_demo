import csv
import re
from datetime import datetime
from pathlib import Path

from sqlmodel import select

from app.db import create_db_and_tables, get_session
from app.models import ProgramDescriptionContent


SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "source" / "1503_program_descriptions_x_section.csv"
)

SECTION_FIELDS = [
    "program_contacts",
    "general_instructions",
    "supporting_documentation_information",
    "review_process",
    "interviews",
    "selection_criteria",
    "program_highlights",
    "program_curriculum",
    "training_sites",
    "additional_information",
    "return_of_service",
    "faq",
    "summary_of_changes",
]


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned or None


def parse_int(value: str | None) -> int | None:
    cleaned = clean_text(value)
    return int(cleaned) if cleaned is not None else None


def detect_language(*values: str | None) -> str | None:
    text = " ".join(value for value in values if value)
    if not text:
        return None

    french_markers = [
        " programme ",
        " jumelage ",
        " médecine ",
        " approuve ",
        " critères ",
        " adresse électronique ",
        " agrément ",
    ]
    english_markers = [
        " program ",
        " match ",
        " approved ",
        " criteria ",
        " accreditation ",
        " email ",
    ]

    lowered = f" {text.lower()} "

    if any(marker in lowered for marker in french_markers):
        return "fr"
    if any(marker in lowered for marker in english_markers):
        return "en"

    if re.search(r"[éàèùâêîôûçëïüœ]", lowered):
        return "fr"

    return "en"


def derive_section_metrics(row: dict[str, str | None]) -> dict[str, int | bool]:
    populated_sections = [field for field in SECTION_FIELDS if row.get(field)]
    total_chars = sum(len(row[field]) for field in populated_sections if row.get(field))

    return {
        "has_program_contacts": bool(row.get("program_contacts")),
        "has_general_instructions": bool(row.get("general_instructions")),
        "has_supporting_documentation_information": bool(
            row.get("supporting_documentation_information")
        ),
        "has_review_process": bool(row.get("review_process")),
        "has_interviews": bool(row.get("interviews")),
        "has_selection_criteria": bool(row.get("selection_criteria")),
        "has_program_highlights": bool(row.get("program_highlights")),
        "has_program_curriculum": bool(row.get("program_curriculum")),
        "has_training_sites": bool(row.get("training_sites")),
        "has_additional_information": bool(row.get("additional_information")),
        "has_return_of_service": bool(row.get("return_of_service")),
        "has_faq": bool(row.get("faq")),
        "has_summary_of_changes": bool(row.get("summary_of_changes")),
        "non_empty_section_count": len(populated_sections),
        "section_text_total_chars": total_chars,
    }


def iter_program_description_rows():
    with SOURCE_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        for raw_row in reader:
            row = {key if key else "raw_row_id": clean_text(value) for key, value in raw_row.items()}

            normalized = {
                "document_id": row["document_id"],
                "raw_row_id": parse_int(row.get("raw_row_id")),
                "match_iteration_id": parse_int(row.get("match_iteration_id")),
                "program_description_id": parse_int(row.get("program_description_id")),
                "source": row["source"],
                "n_program_description_sections": parse_int(row.get("n_program_description_sections")),
                "program_name": row.get("program_name"),
                "match_iteration_name": row.get("match_iteration_name"),
                "program_contacts": row.get("program_contracts"),
                "general_instructions": row.get("general_instructions"),
                "supporting_documentation_information": row.get(
                    "supporting_documentation_information"
                ),
                "review_process": row.get("review_process"),
                "interviews": row.get("interviews"),
                "selection_criteria": row.get("selection_criteria"),
                "program_highlights": row.get("program_highlights"),
                "program_curriculum": row.get("program_curriculum"),
                "training_sites": row.get("training_sites"),
                "additional_information": row.get("additional_information"),
                "return_of_service": row.get("return_of_service"),
                "faq": row.get("faq"),
                "summary_of_changes": row.get("summary_of_changes"),
            }

            normalized["content_language"] = detect_language(
                normalized["program_name"],
                normalized["match_iteration_name"],
                normalized["general_instructions"],
            )
            normalized.update(derive_section_metrics(normalized))
            yield normalized


def upsert_program_description_rows() -> int:
    create_db_and_tables()
    upserted = 0

    with get_session() as session:
        for row in iter_program_description_rows():
            existing = session.exec(
                select(ProgramDescriptionContent).where(
                    ProgramDescriptionContent.document_id == row["document_id"]
                )
            ).first()

            if existing is None:
                session.add(ProgramDescriptionContent(**row))
            else:
                for field, value in row.items():
                    setattr(existing, field, value)
                existing.updated_at = datetime.utcnow()

            upserted += 1

        session.commit()

    return upserted


if __name__ == "__main__":
    count = upsert_program_description_rows()
    print(f"Loaded {count} program description content rows from {SOURCE_PATH.name}")
