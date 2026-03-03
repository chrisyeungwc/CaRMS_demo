from scripts.load_program_documents import chunk_text, parse_document_identity


def test_parse_document_identity_splits_match_and_program_ids():
    assert parse_document_identity("1503|27447") == (1503, 27447)


def test_chunk_text_respects_overlap_and_keeps_content():
    text = (
        "Paragraph one has enough content to trigger chunking.\n\n"
        "Paragraph two continues with more detail about rural training.\n\n"
        "Paragraph three adds final context."
    )

    chunks = chunk_text(text, chunk_size=70, overlap=10)

    assert len(chunks) >= 2
    assert chunks[0].startswith("Paragraph one")
    assert "Paragraph two" in "".join(chunks)
    assert all(chunk.strip() for chunk in chunks)
