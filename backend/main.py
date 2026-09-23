"""EventDNA API and static frontend."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data_loader import load_contractors
from .engine import recommend
from .models import RecommendationRequest
from .what_if import build_what_if

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def create_app(dataset_path=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.contractors = load_contractors(dataset_path)
        yield

    app = FastAPI(title="EventDNA API", version="1.0.0", lifespan=lifespan)

    def dataset():
        contractors = app.state.contractors
        if not contractors:
            raise HTTPException(503, "Датасет пуст. Добавьте исходные записи в backend/data/contractors.csv и перезапустите сервер.")
        return contractors

    @app.get("/health")
    def health():
        count = len(app.state.contractors)
        return dict(status="ok" if count else "dataset_empty", contractors_loaded=count)

    @app.get("/filters")
    @app.get("/api/filters")
    def filters():
        contractors = dataset()
        prices = [c.price_from_kzt for c in contractors if c.price_from_kzt is not None]
        return dict(cities=sorted({c.city for c in contractors if c.city}),
                    categories=sorted({v for c in contractors for v in c.categories}),
                    event_formats=sorted({v for c in contractors for v in c.event_formats}),
                    languages=sorted({v for c in contractors for v in c.languages}),
                    price_range=dict(min=min(prices) if prices else None, max=max(prices) if prices else None))

    @app.post("/recommendations")
    @app.post("/api/recommend")
    def recommendations(request: RecommendationRequest):
        return recommend(dataset(), request)

    @app.post("/what-if")
    @app.post("/api/what-if")
    def what_if(request: RecommendationRequest):
        return build_what_if(dataset(), request)

    @app.get("/", include_in_schema=False)
    def root():
        return FileResponse(FRONTEND / "index.html")

    app.mount("/", StaticFiles(directory=FRONTEND), name="frontend")
    return app


app = create_app()
