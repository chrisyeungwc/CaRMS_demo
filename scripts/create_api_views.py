from pathlib import Path

from sqlalchemy import text

from app.db import engine


SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
VIEW_FILES = [
    SQL_DIR / "program_api_dataset_view.sql",
]


def create_views() -> None:
    with engine.begin() as connection:
        for view_file in VIEW_FILES:
            connection.execute(text(view_file.read_text()))


if __name__ == "__main__":
    create_views()
    print("Created API views:")
    for view_file in VIEW_FILES:
        print(f"- {view_file.name}")
