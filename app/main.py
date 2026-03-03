from fastapi import FastAPI

from app.api.disciplines import router as disciplines_router
from app.api.programs import router as programs_router
from app.api.reports import router as reports_router
from app.api.search import router as search_router


app = FastAPI(
    title="CaRMS Residency Data Platform",
    version="0.1.0",
    description="FastAPI service for querying CaRMS residency program data.",
)

app.include_router(programs_router)
app.include_router(disciplines_router)
app.include_router(reports_router)
app.include_router(search_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
