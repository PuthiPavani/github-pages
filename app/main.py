from fastapi import FastAPI, Request, UploadFile, Form, HTTPException, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pathlib import Path
import shutil
import secrets
import json

from .database import init_db, get_session
from .models import Trip, Photo
from sqlmodel import select

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Travel Journal & Photo Album")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: Optional[str] = None):
    with get_session() as session:
        stmt = select(Trip).order_by(Trip.created_at.desc())
        trips = session.exec(stmt).all()
    return templates.TemplateResponse("trips/index.html", {"request": request, "trips": trips, "q": q})


@app.get("/trips/new", response_class=HTMLResponse)
def new_trip_form(request: Request):
    return templates.TemplateResponse("trips/new.html", {"request": request})


def generate_slug(base: str) -> str:
    base = "-".join(base.lower().split())[:40].strip("-") or "trip"
    return f"{base}-{secrets.token_hex(3)}"


@app.post("/trips")
async def create_trip(
    request: Request,
    title: str = Form(...),
    story: str = Form(""),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
):
    slug = generate_slug(title)
    lat_value: Optional[float] = float(latitude) if latitude not in (None, "") else None
    lng_value: Optional[float] = float(longitude) if longitude not in (None, "") else None
    with get_session() as session:
        trip = Trip(title=title, story=story, latitude=lat_value, longitude=lng_value, slug=slug)
        session.add(trip)
        session.commit()
        session.refresh(trip)

        saved_files: List[Photo] = []
        for uf in files:
            if not uf or not uf.filename:
                continue
            safe_name = f"{trip.id}_{secrets.token_hex(4)}_{Path(uf.filename).name}"
            dest = UPLOAD_DIR / safe_name
            with dest.open("wb") as outfp:
                shutil.copyfileobj(uf.file, outfp)
            photo = Photo(trip_id=trip.id, filename=safe_name)
            session.add(photo)
            saved_files.append(photo)
        if saved_files:
            session.commit()

    return RedirectResponse(url=f"/trips/{slug}", status_code=303)


@app.get("/trips/{slug}", response_class=HTMLResponse)
async def trip_detail(request: Request, slug: str):
    with get_session() as session:
        trip = session.exec(select(Trip).where(Trip.slug == slug)).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        photos = session.exec(select(Photo).where(Photo.trip_id == trip.id).order_by(Photo.created_at)).all()
    return templates.TemplateResponse("trips/detail.html", {"request": request, "trip": trip, "photos": photos})


@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):
    with get_session() as session:
        trips = session.exec(select(Trip).where(Trip.latitude != None, Trip.longitude != None)).all()
        trips_payload = [
            {
                "title": t.title,
                "slug": t.slug,
                "latitude": t.latitude,
                "longitude": t.longitude,
            }
            for t in trips
        ]
    return templates.TemplateResponse(
        "trips/map.html",
        {"request": request, "trips": trips_payload},
    )
