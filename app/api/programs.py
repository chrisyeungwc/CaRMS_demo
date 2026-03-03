from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlmodel import Session

from app.db import get_db_session
from app.schemas import (
    ProgramContentSummary,
    ProgramDetailResponse,
    ProgramDisciplineInfo,
    ProgramListFilters,
    ProgramListItem,
    ProgramListPagination,
    ProgramListResponse,
    ProgramMetadata,
    ProgramSectionAvailability,
    ProgramSectionsResponse,
    ProgramSections,
)


router = APIRouter(prefix="/programs", tags=["programs"])


BASE_LIST_SQL = """
select
    document_id,
    match_iteration_id,
    program_description_id,
    discipline_id,
    discipline,
    school_id,
    school_name,
    program_site,
    program_stream,
    program_stream_name,
    master_program_name as program_name,
    content_language,
    n_program_description_sections,
    non_empty_section_count,
    section_text_total_chars,
    has_interviews,
    has_return_of_service,
    has_faq,
    source_url
from program_api_dataset
where (:discipline is null or discipline = :discipline)
  and (:school_name is null or school_name = :school_name)
  and (:content_language is null or content_language = :content_language)
  and (
        :has_return_of_service is null
        or has_return_of_service = :has_return_of_service
      )
order by discipline, school_name, program_site, program_stream
offset :offset
limit :limit
"""


BASE_COUNT_SQL = """
select count(*)
from program_api_dataset
where (:discipline is null or discipline = :discipline)
  and (:school_name is null or school_name = :school_name)
  and (:content_language is null or content_language = :content_language)
  and (
        :has_return_of_service is null
        or has_return_of_service = :has_return_of_service
      )
"""


DETAIL_SQL = """
select *
from program_api_dataset
where document_id = :document_id
"""


@router.get("", response_model=ProgramListResponse)
def list_programs(
    discipline: str | None = Query(default=None),
    school_name: str | None = Query(default=None),
    content_language: str | None = Query(default=None),
    has_return_of_service: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    session: Session = Depends(get_db_session),
) -> ProgramListResponse:
    params = {
        "discipline": discipline,
        "school_name": school_name,
        "content_language": content_language,
        "has_return_of_service": has_return_of_service,
        "offset": offset,
        "limit": limit,
    }

    connection = session.connection()
    rows = connection.execute(text(BASE_LIST_SQL), params).mappings().all()
    total = connection.execute(text(BASE_COUNT_SQL), params).scalar_one()

    items = [ProgramListItem.model_validate(dict(row)) for row in rows]

    return ProgramListResponse(
        items=items,
        pagination=ProgramListPagination(offset=offset, limit=limit, total=total),
        filters=ProgramListFilters(
            discipline=discipline,
            school_name=school_name,
            content_language=content_language,
            has_return_of_service=has_return_of_service,
        ),
    )


@router.get("/{document_id}", response_model=ProgramDetailResponse)
def get_program(document_id: str, session: Session = Depends(get_db_session)) -> ProgramDetailResponse:
    row = session.connection().execute(text(DETAIL_SQL), {"document_id": document_id}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Program not found")

    data = dict(row)

    return ProgramDetailResponse(
        document_id=data["document_id"],
        match_iteration_id=data["match_iteration_id"],
        program_description_id=data["program_description_id"],
        discipline=ProgramDisciplineInfo(
            discipline_id=data["discipline_id"],
            discipline=data["discipline"],
        ),
        program=ProgramMetadata(
            school_id=data["school_id"],
            school_name=data["school_name"],
            program_site=data["program_site"],
            program_stream=data["program_stream"],
            program_stream_name=data["program_stream_name"],
            program_name=data["master_program_name"],
            raw_program_name=data["raw_program_name"],
            source_url=data["source_url"],
            source_document_url=data["source_document_url"],
            content_language=data["content_language"],
        ),
        content_summary=ProgramContentSummary(
            n_program_description_sections=data["n_program_description_sections"],
            non_empty_section_count=data["non_empty_section_count"],
            section_text_total_chars=data["section_text_total_chars"],
        ),
        section_availability=ProgramSectionAvailability(
            has_program_contacts=data["has_program_contacts"],
            has_general_instructions=data["has_general_instructions"],
            has_supporting_documentation_information=data["has_supporting_documentation_information"],
            has_review_process=data["has_review_process"],
            has_interviews=data["has_interviews"],
            has_selection_criteria=data["has_selection_criteria"],
            has_program_highlights=data["has_program_highlights"],
            has_program_curriculum=data["has_program_curriculum"],
            has_training_sites=data["has_training_sites"],
            has_additional_information=data["has_additional_information"],
            has_return_of_service=data["has_return_of_service"],
            has_faq=data["has_faq"],
            has_summary_of_changes=data["has_summary_of_changes"],
        ),
        sections=ProgramSections(
            program_contacts=data["program_contacts"],
            general_instructions=data["general_instructions"],
            supporting_documentation_information=data["supporting_documentation_information"],
            review_process=data["review_process"],
            interviews=data["interviews"],
            selection_criteria=data["selection_criteria"],
            program_highlights=data["program_highlights"],
            program_curriculum=data["program_curriculum"],
            training_sites=data["training_sites"],
            additional_information=data["additional_information"],
            return_of_service=data["return_of_service"],
            faq=data["faq"],
            summary_of_changes=data["summary_of_changes"],
        ),
    )


@router.get("/{document_id}/sections", response_model=ProgramSectionsResponse)
def get_program_sections(
    document_id: str, session: Session = Depends(get_db_session)
) -> ProgramSectionsResponse:
    row = session.connection().execute(text(DETAIL_SQL), {"document_id": document_id}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Program not found")

    data = dict(row)

    return ProgramSectionsResponse(
        document_id=data["document_id"],
        section_availability=ProgramSectionAvailability(
            has_program_contacts=data["has_program_contacts"],
            has_general_instructions=data["has_general_instructions"],
            has_supporting_documentation_information=data["has_supporting_documentation_information"],
            has_review_process=data["has_review_process"],
            has_interviews=data["has_interviews"],
            has_selection_criteria=data["has_selection_criteria"],
            has_program_highlights=data["has_program_highlights"],
            has_program_curriculum=data["has_program_curriculum"],
            has_training_sites=data["has_training_sites"],
            has_additional_information=data["has_additional_information"],
            has_return_of_service=data["has_return_of_service"],
            has_faq=data["has_faq"],
            has_summary_of_changes=data["has_summary_of_changes"],
        ),
        sections=ProgramSections(
            program_contacts=data["program_contacts"],
            general_instructions=data["general_instructions"],
            supporting_documentation_information=data["supporting_documentation_information"],
            review_process=data["review_process"],
            interviews=data["interviews"],
            selection_criteria=data["selection_criteria"],
            program_highlights=data["program_highlights"],
            program_curriculum=data["program_curriculum"],
            training_sites=data["training_sites"],
            additional_information=data["additional_information"],
            return_of_service=data["return_of_service"],
            faq=data["faq"],
            summary_of_changes=data["summary_of_changes"],
        ),
    )
