from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.db import get_db_session
from app.schemas import CompletenessResponse, CompletenessSectionStat, CompletenessSummary


router = APIRouter(prefix="/reports", tags=["reports"])


SUMMARY_SQL = """
select
    count(*) as total_programs,
    round(avg(non_empty_section_count)::numeric, 2) as avg_non_empty_section_count,
    round(avg(section_text_total_chars)::numeric, 2) as avg_section_text_total_chars
from program_description_content
"""


SECTION_STATS_SQL = """
select 'program_contacts' as section_name,
       count(*) filter (where has_program_contacts) as programs_with_section,
       count(*) filter (where not has_program_contacts) as programs_missing_section,
       round(avg(case when has_program_contacts then 1.0 else 0.0 end)::numeric, 4) as coverage_ratio
from program_description_content
union all
select 'general_instructions',
       count(*) filter (where has_general_instructions),
       count(*) filter (where not has_general_instructions),
       round(avg(case when has_general_instructions then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'supporting_documentation_information',
       count(*) filter (where has_supporting_documentation_information),
       count(*) filter (where not has_supporting_documentation_information),
       round(avg(case when has_supporting_documentation_information then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'review_process',
       count(*) filter (where has_review_process),
       count(*) filter (where not has_review_process),
       round(avg(case when has_review_process then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'interviews',
       count(*) filter (where has_interviews),
       count(*) filter (where not has_interviews),
       round(avg(case when has_interviews then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'selection_criteria',
       count(*) filter (where has_selection_criteria),
       count(*) filter (where not has_selection_criteria),
       round(avg(case when has_selection_criteria then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'program_highlights',
       count(*) filter (where has_program_highlights),
       count(*) filter (where not has_program_highlights),
       round(avg(case when has_program_highlights then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'program_curriculum',
       count(*) filter (where has_program_curriculum),
       count(*) filter (where not has_program_curriculum),
       round(avg(case when has_program_curriculum then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'training_sites',
       count(*) filter (where has_training_sites),
       count(*) filter (where not has_training_sites),
       round(avg(case when has_training_sites then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'additional_information',
       count(*) filter (where has_additional_information),
       count(*) filter (where not has_additional_information),
       round(avg(case when has_additional_information then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'return_of_service',
       count(*) filter (where has_return_of_service),
       count(*) filter (where not has_return_of_service),
       round(avg(case when has_return_of_service then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'faq',
       count(*) filter (where has_faq),
       count(*) filter (where not has_faq),
       round(avg(case when has_faq then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
union all
select 'summary_of_changes',
       count(*) filter (where has_summary_of_changes),
       count(*) filter (where not has_summary_of_changes),
       round(avg(case when has_summary_of_changes then 1.0 else 0.0 end)::numeric, 4)
from program_description_content
order by section_name
"""


@router.get("/completeness", response_model=CompletenessResponse)
def report_completeness(session: Session = Depends(get_db_session)) -> CompletenessResponse:
    connection = session.connection()
    summary_row = connection.execute(text(SUMMARY_SQL)).mappings().first()
    stat_rows = connection.execute(text(SECTION_STATS_SQL)).mappings().all()

    return CompletenessResponse(
        summary=CompletenessSummary.model_validate(dict(summary_row)),
        section_stats=[CompletenessSectionStat.model_validate(dict(row)) for row in stat_rows],
    )
