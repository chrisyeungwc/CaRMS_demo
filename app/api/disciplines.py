from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.db import get_db_session
from app.schemas import DisciplineListItem, DisciplineListResponse


router = APIRouter(prefix="/disciplines", tags=["disciplines"])


DISCIPLINE_SQL = """
select
    discipline_id,
    discipline,
    count(*) as program_count
from program_api_dataset
group by discipline_id, discipline
order by discipline
"""


@router.get("", response_model=DisciplineListResponse)
def list_disciplines(session: Session = Depends(get_db_session)) -> DisciplineListResponse:
    rows = session.connection().execute(text(DISCIPLINE_SQL)).mappings().all()
    items = [DisciplineListItem.model_validate(dict(row)) for row in rows]
    return DisciplineListResponse(items=items, total=len(items))
