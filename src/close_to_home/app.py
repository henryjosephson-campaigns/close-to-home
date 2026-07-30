"""Close to Home — event proximity outreach demo.

Run: uv run uvicorn close_to_home.app:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from shapely.geometry import Point, shape

from .events import EVENTS
from .isochrone import get_isochrone
from .mock_ngp import PEOPLE

app = FastAPI(title="Close to Home")

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


class ReachableRequest(BaseModel):
    lat: float
    lng: float
    minutes: int = 20


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/people")
def people():
    return {"people": PEOPLE, "count": len(PEOPLE)}


@app.get("/api/events")
def events():
    return {"events": EVENTS}


@app.post("/api/reachable")
def reachable(req: ReachableRequest):
    polygon_geojson = get_isochrone(req.lat, req.lng, req.minutes)
    polygon = shape(polygon_geojson)

    inside = [
        p for p in PEOPLE if polygon.contains(Point(p["lng"], p["lat"]))
    ]
    donors = [p for p in inside if p["contributionSummary"]]
    return {
        "polygon": polygon_geojson,
        "insideVanIds": [p["vanId"] for p in inside],
        "stats": {
            "inside": len(inside),
            "total": len(PEOPLE),
            "donorsInside": len(donors),
            "donorTotalAmount": round(
                sum(p["contributionSummary"]["totalAmount"] for p in donors), 2
            ),
            "volunteersInside": sum(1 for p in inside if p["isVolunteer"]),
        },
    }
