from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

rooms = [
    {"id": 1, "title": "Mini-Room", "capacity": 2, "price_per_hour": 10},
    {"id": 2, "title": "Conference Hall", "capacity": 20, "price_per_hour": 50}
]

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", include_in_schema=False)
@app.get("/rooms", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"rooms": rooms, "title": "Home"})

@app.get("/api/rooms")
def get_rooms():
    return rooms