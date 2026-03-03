from pydantic import BaseModel


class ProgramListItem(BaseModel):
    document_id: str
    match_iteration_id: int
    program_description_id: int
    discipline_id: int
    discipline: str
    school_id: int
    school_name: str
    program_site: str
    program_stream: str
    program_stream_name: str
    program_name: str
    content_language: str | None
    n_program_description_sections: int | None
    non_empty_section_count: int
    section_text_total_chars: int
    has_interviews: bool
    has_return_of_service: bool
    has_faq: bool
    source_url: str


class ProgramListPagination(BaseModel):
    offset: int
    limit: int
    total: int


class ProgramListFilters(BaseModel):
    discipline: str | None = None
    school_name: str | None = None
    content_language: str | None = None
    has_return_of_service: bool | None = None


class ProgramListResponse(BaseModel):
    items: list[ProgramListItem]
    pagination: ProgramListPagination
    filters: ProgramListFilters


class ProgramDisciplineInfo(BaseModel):
    discipline_id: int
    discipline: str


class ProgramMetadata(BaseModel):
    school_id: int
    school_name: str
    program_site: str
    program_stream: str
    program_stream_name: str
    program_name: str
    raw_program_name: str | None
    source_url: str
    source_document_url: str
    content_language: str | None


class ProgramContentSummary(BaseModel):
    n_program_description_sections: int | None
    non_empty_section_count: int
    section_text_total_chars: int


class ProgramSectionAvailability(BaseModel):
    has_program_contacts: bool
    has_general_instructions: bool
    has_supporting_documentation_information: bool
    has_review_process: bool
    has_interviews: bool
    has_selection_criteria: bool
    has_program_highlights: bool
    has_program_curriculum: bool
    has_training_sites: bool
    has_additional_information: bool
    has_return_of_service: bool
    has_faq: bool
    has_summary_of_changes: bool


class ProgramSections(BaseModel):
    program_contacts: str | None
    general_instructions: str | None
    supporting_documentation_information: str | None
    review_process: str | None
    interviews: str | None
    selection_criteria: str | None
    program_highlights: str | None
    program_curriculum: str | None
    training_sites: str | None
    additional_information: str | None
    return_of_service: str | None
    faq: str | None
    summary_of_changes: str | None


class ProgramDetailResponse(BaseModel):
    document_id: str
    match_iteration_id: int
    program_description_id: int
    discipline: ProgramDisciplineInfo
    program: ProgramMetadata
    content_summary: ProgramContentSummary
    section_availability: ProgramSectionAvailability
    sections: ProgramSections


class ProgramSectionsResponse(BaseModel):
    document_id: str
    section_availability: ProgramSectionAvailability
    sections: ProgramSections


class DisciplineListItem(BaseModel):
    discipline_id: int
    discipline: str
    program_count: int


class DisciplineListResponse(BaseModel):
    items: list[DisciplineListItem]
    total: int


class CompletenessSummary(BaseModel):
    total_programs: int
    avg_non_empty_section_count: float
    avg_section_text_total_chars: float


class CompletenessSectionStat(BaseModel):
    section_name: str
    programs_with_section: int
    programs_missing_section: int
    coverage_ratio: float


class CompletenessResponse(BaseModel):
    summary: CompletenessSummary
    section_stats: list[CompletenessSectionStat]


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    discipline: str | None = None
    content_language: str | None = None


class SearchChunkResult(BaseModel):
    chunk_id: int
    document_id: str
    chunk_index: int
    chunk_text: str
    chunk_char_count: int
    source_url: str
    content_language: str | None
    program_name: str
    school_name: str
    program_site: str
    program_stream: str
    discipline: str
    rank_score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    items: list[SearchChunkResult]


class AskRequest(BaseModel):
    question: str
    limit: int = 5
    discipline: str | None = None
    content_language: str | None = None
    model: str = "qwen3:0.6b"


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[SearchChunkResult]
