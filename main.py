from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import RoomCreate, RoomResponse, ReviewCreate, ReviewResponse

rooms = [
    {"id": 1, "title": "Mini-Room", "capacity": 2, "price_per_hour": 10},
    {"id": 2, "title": "Conference Hall", "capacity": 20, "price_per_hour": 50}
]

reviews = [
    {"id": 1, "room_id": 1, "author": "Алексей", "text": "Отличная комната, Wi-Fi летит!"},
    {"id": 2, "room_id": 1, "author": "Мария", "text": "Немного шумно от кондиционера."},
    {"id": 3, "room_id": 2, "author": "Иван", "text": "Зал огромный, проектор топ."}
]

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", include_in_schema=False, name="home")
@app.get("/rooms", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"rooms": rooms, "title": "Home"})

@app.get("/api/rooms", response_model=list[RoomResponse])
def get_rooms():
    return rooms

@app.post("/api/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(room: RoomCreate):
    new_id = max(r["id"] for r in rooms) + 1 if rooms else 1
    new_room = {
        "id": new_id,
        "title": room.title,
        "capacity": room.capacity,
        "price_per_hour": room.price_per_hour,
    }
    rooms.append(new_room)
    return new_room

@app.get("/rooms/{room_id}", include_in_schema=False, name="get_room")
def get_room(request: Request, room_id: int):
    current_room = None
    for room in rooms:
        if room["id"] == room_id:
            current_room = room
            break
            
    if current_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    
    room_reviews = [rev for rev in reviews if rev["room_id"] == room_id]
    
    return templates.TemplateResponse(
        request, 
        "room.html", 
        {
            "room": current_room, 
            "reviews": room_reviews, 
            "title": current_room["title"]
        }
    )

@app.get("/api/rooms/{room_id}/reviews")
def get_api_reviews(room_id: int):
    room_reviews = [rev for rev in reviews if rev["room_id"] == room_id]
    return room_reviews

@app.post("/api/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(review: ReviewCreate):
    room_exists = any(r["id"] == review.room_id for r in rooms)
    if not room_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Комната с ID {review.room_id} не найдена. Невозможно оставить отзыв."
        )

    new_id = max(rev["id"] for rev in reviews) + 1 if reviews else 1

    new_review = {
        "id": new_id,
        "room_id": review.room_id,
        "author": review.author,
        "text": review.text,
    }
    reviews.append(new_review)
    return new_review

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = exception.detail if exception.detail else "An error occurred."
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exception.status_code, content={"detail": message})
    return templates.TemplateResponse(request, "error.html", {"status_code": exception.status_code, "message": message}, status_code=exception.status_code)

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": exception.errors()})
    return templates.TemplateResponse(request, "error.html", {"status_code": status.HTTP_422_UNPROCESSABLE_CONTENT, "message": "Invalid request."}, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)