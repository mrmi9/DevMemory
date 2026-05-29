from contextlib import asynccontextmanager
import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import Settings, get_settings, validate_runtime_settings
from app.database import run_migrations


request_logger = logging.getLogger("app.request")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    validate_runtime_settings(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        run_migrations()
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix=settings.api_prefix)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started_at = perf_counter()
        request_id = request.headers.get("x-request-id") or str(uuid4())
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        request_logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                },
                ensure_ascii=False,
            )
        )
        return response

    @app.get("/health")
    def health():
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
