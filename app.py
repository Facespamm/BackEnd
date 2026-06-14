import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db
from init_database.init_db import (
    init_admin,
    init_category,
    init_dans_new,
    init_roles_new,
)
from routers.athletes.athletes import athlete_router
from routers.auth.auth import auth_router
from routers.bracket.brackets import brackets_router
from routers.category.categories import categories_router
from routers.club.clubs import club_router
from routers.dan.dan import dans_bp
from routers.fight.fights import fights_router
from routers.pdf.pdf_routes import pdf_router
from routers.referee.referee import referee_router
from routers.result.results import results_router
from routers.score.scores import scores_router
from routers.statistic.statistics import statistics_router
from routers.tournament.tournaments import tournaments_router
from routers.user.user import user_router
from routers.weighing.weighing import weighing_router

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # создаёт БД и таблицы

    init_dans_new()
    init_roles_new()
    init_category()
    init_admin()

    yield


IS_PROD = os.getenv("ENV") == "prod"

app = FastAPI(
    lifespan=lifespan,
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(athlete_router)
app.include_router(brackets_router)
app.include_router(club_router)
app.include_router(tournaments_router)
app.include_router(dans_bp)
app.include_router(pdf_router)
app.include_router(results_router)
app.include_router(scores_router)
app.include_router(statistics_router)
app.include_router(weighing_router)
app.include_router(fights_router)
app.include_router(referee_router)
app.include_router(user_router)
