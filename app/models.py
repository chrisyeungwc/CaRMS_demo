from datetime import datetime

from sqlmodel import Field, SQLModel


class Discipline(SQLModel, table=True):
    __tablename__ = "discipline"

    discipline_id: int = Field(primary_key=True)
    discipline: str = Field(index=True, nullable=False)


class ProgramMaster(SQLModel, table=True):
    __tablename__ = "program_master"

    program_stream_id: int = Field(primary_key=True)
    discipline_id: int = Field(index=True, nullable=False, foreign_key="discipline.discipline_id")
    discipline_name: str = Field(nullable=False)
    school_id: int = Field(index=True, nullable=False)
    school_name: str = Field(index=True, nullable=False)
    program_stream_name: str = Field(nullable=False)
    program_site: str = Field(nullable=False)
    program_stream: str = Field(nullable=False)
    program_name: str = Field(index=True, nullable=False)
    program_url: str = Field(nullable=False)


class ProgramDescriptionContent(SQLModel, table=True):
    __tablename__ = "program_description_content"

    document_id: str = Field(primary_key=True)
    raw_row_id: int | None = Field(default=None, index=True)
    match_iteration_id: int = Field(index=True, nullable=False)
    program_description_id: int = Field(index=True, nullable=False)
    source: str = Field(nullable=False)

    n_program_description_sections: int | None = Field(default=None)
    program_name: str | None = Field(default=None)
    match_iteration_name: str | None = Field(default=None)
    content_language: str | None = Field(default=None, index=True, max_length=8)

    program_contacts: str | None = Field(default=None)
    general_instructions: str | None = Field(default=None)
    supporting_documentation_information: str | None = Field(default=None)
    review_process: str | None = Field(default=None)
    interviews: str | None = Field(default=None)
    selection_criteria: str | None = Field(default=None)
    program_highlights: str | None = Field(default=None)
    program_curriculum: str | None = Field(default=None)
    training_sites: str | None = Field(default=None)
    additional_information: str | None = Field(default=None)
    return_of_service: str | None = Field(default=None)
    faq: str | None = Field(default=None)
    summary_of_changes: str | None = Field(default=None)

    has_program_contacts: bool = Field(default=False, nullable=False)
    has_general_instructions: bool = Field(default=False, nullable=False)
    has_supporting_documentation_information: bool = Field(default=False, nullable=False)
    has_review_process: bool = Field(default=False, nullable=False)
    has_interviews: bool = Field(default=False, nullable=False)
    has_selection_criteria: bool = Field(default=False, nullable=False)
    has_program_highlights: bool = Field(default=False, nullable=False)
    has_program_curriculum: bool = Field(default=False, nullable=False)
    has_training_sites: bool = Field(default=False, nullable=False)
    has_additional_information: bool = Field(default=False, nullable=False)
    has_return_of_service: bool = Field(default=False, nullable=False)
    has_faq: bool = Field(default=False, nullable=False)
    has_summary_of_changes: bool = Field(default=False, nullable=False)
    non_empty_section_count: int = Field(default=0, nullable=False)
    section_text_total_chars: int = Field(default=0, nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ProgramDocument(SQLModel, table=True):
    __tablename__ = "program_document"

    document_id: str = Field(primary_key=True)
    match_iteration_id: int = Field(index=True, nullable=False)
    program_description_id: int = Field(index=True, nullable=False)
    source_url: str = Field(nullable=False)
    content_language: str | None = Field(default=None, index=True, max_length=8)
    content: str = Field(nullable=False)
    content_length: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunk"

    chunk_id: int | None = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="program_document.document_id", index=True, nullable=False)
    chunk_index: int = Field(nullable=False)
    chunk_text: str = Field(nullable=False)
    chunk_char_count: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
