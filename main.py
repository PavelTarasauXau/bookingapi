from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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

@app.get("/rooms/{room_id}")
def get_room(request: Request, room_id: int):
    for room in rooms:
        if room.get("id") == room_id:
            title = room["title"][:50]
            return templates.TemplateResponse(
                request, 
                "room.html", 
                {"room": room, "title": title},
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "Room not found")

## StarletteHTTPException Handler
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


### RequestValidationError Handler
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
