import os
import secrets
import string
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl, StringConstraints

DATABASE_URL = os.environ["DATABASE_URL"]
ALPHABET = string.ascii_letters + string.digits
DIST = Path(__file__).parent / "dist"
Code = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9]{8}$")]


class CreateLink(BaseModel):
    url: HttpUrl


class ShortLink(BaseModel):
    code: str
    short_url: str
    url: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                code text PRIMARY KEY,
                url text NOT NULL
            )
        """)
    yield


app = FastAPI(title="URL Shortener", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(DIST / "index.html")


@app.get("/health")
def health():
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            conn.execute("SELECT 1 FROM links LIMIT 1")
    except psycopg.Error as exc:
        raise HTTPException(503, "Database unavailable") from exc
    return {"status": "ok"}


@app.post("/api/links", status_code=201)
def create_link(payload: CreateLink, request: Request) -> ShortLink:
    if payload.url.username is not None or payload.url.password is not None:
        raise HTTPException(422, "URLs containing credentials are not supported")
    url = str(payload.url)
    with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
        for _ in range(5):
            code = "".join(secrets.choice(ALPHABET) for _ in range(8))
            row = conn.execute(
                "INSERT INTO links (code, url) VALUES (%s, %s) "
                "ON CONFLICT (code) DO NOTHING RETURNING code",
                (code, url),
            ).fetchone()
            if row:
                return ShortLink(
                    code=code, short_url=str(request.url_for("follow_link", code=code)), url=url
                )
    raise HTTPException(503, "Could not allocate a short link. Please retry.")


@app.get("/s/{code}", response_class=RedirectResponse, status_code=307)
def follow_link(code: Code):
    with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
        row = conn.execute("SELECT url FROM links WHERE code = %s", (code,)).fetchone()
    if row is None:
        raise HTTPException(404, "Short link not found")
    return RedirectResponse(row[0], status_code=307)
