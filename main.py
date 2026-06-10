from typing import Annotated
from datetime import datetime
from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session

import models 
from database import Base, engine, get_db
from schemas import (
    RoomCreate, RoomResponse, RoomUpdate,
    ReviewCreate, ReviewResponse, ReviewUpdate,
    UserCreate, UserResponse,
    BookingCreate, BookingResponse
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", include_in_schema=False, name="home")
@app.get("/rooms", include_in_schema=False)
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Room))
    rooms = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"rooms": rooms, "title": "Home"}
    )


@app.get("/rooms/{room_id}", include_in_schema=False, name="room_page")
def room_page(request: Request, room_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Room).where(models.Room.id == room_id))
    current_room = result.scalar_one_or_none() 
    
    if current_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Room not found"
        )
    
    return templates.TemplateResponse(
        request=request, 
        name="room.html", 
        context={
            "room": current_room, 
            "reviews": current_room.reviews, 
            "title": current_room.title
        }
    )

#users
@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    result = db.execute(select(models.User).where(models.User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    new_user = models.User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


#rooms
@app.get("/api/rooms", response_model=list[RoomResponse])
def get_rooms(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Room)) 
    return result.scalars().all()


@app.post("/api/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(room: RoomCreate, db: Annotated[Session, Depends(get_db)]):
    new_room = models.Room(
        title=room.title,
        capacity=room.capacity,
        price_per_hour=room.price_per_hour
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room
    

@app.patch("/api/rooms/{room_id}", response_model=RoomResponse, status_code=status.HTTP_200_OK)
def update_room(room_id: int, room_data: RoomUpdate, db: Annotated[Session, Depends(get_db)]):
    
    result = db.execute(select(models.Room).where(models.Room.id == room_id))
    db_room = result.scalar_one_or_none()
    
    if db_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Room with ID {room_id} not found"
        )
    
    update_data = room_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_room, key, value)
        
    db.commit()
    db.refresh(db_room) 
    
    return db_room

@app.delete("/api/rooms/{room_id}")
def delete_room(room_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Room).where(models.Room.id == room_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Room with ID {room_id} not found"
        )
        
    db.delete(item)
    db.commit()

    return {"detail": "Room with ID {room_id} succesfully deleted"}


#revies
@app.get("/api/rooms/{room_id}/reviews", response_model=list[ReviewResponse])
def get_api_reviews(room_id: int, db: Annotated[Session, Depends(get_db)]):
    room_result = db.execute(select(models.Room).where(models.Room.id == room_id))
    if not room_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    result = db.execute(select(models.Review).where(models.Review.room_id == room_id))
    return result.scalars().all()


@app.post("/api/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(review: ReviewCreate, db: Annotated[Session, Depends(get_db)]):
    room_result = db.execute(select(models.Room).where(models.Room.id == review.room_id))
    if not room_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Комната с ID {review.room_id} не найдена. Невозможно оставить отзыв."
        )

    temp_user_id = 1 

    new_review = models.Review(
        room_id=review.room_id,
        user_id=temp_user_id,
        author=review.author,
        text=review.text
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

@app.patch("/api/reviews/{review_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
def update_review(review_id: int, review: ReviewUpdate, db: Annotated[Session, Depends(get_db)]): # Добавили : int
    
    review_result = db.execute(select(models.Review).where(models.Review.id == review_id))
    db_review = review_result.scalar_one_or_none()

    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Review with id: {review_id} not found"
        )
    
    update_data = review.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_review, key, value)
        
    db.commit()
    db.refresh(db_review) 
    
    return db_review

@app.delete("/api/reviews/{review_id}", status_code=status.HTTP_200_OK)
def review_delete(review_id: int, db: Annotated[Session, Depends(get_db)]):

    result_review = db.execute(select(models.Review).where(models.Review.id == review_id))
    db_review = result_review.scalar_one_or_none()

    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID: {review_id} not found"
        )

    db.delete(db_review)
    db.commit()

    return {"detail": "Review with ID {review_id} succesfully deleted"}   

#bookings
@app.post("/api/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking: BookingCreate, db: Annotated[Session, Depends(get_db)]):
    room_result = db.execute(select(models.Room).where(models.Room.id == booking.room_id))
    if not room_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    overlap_query = select(models.Booking).where(
        models.Booking.room_id == booking.room_id,
        models.Booking.start_time < booking.end_time,
        models.Booking.end_time > booking.start_time
    )
    overlap_result = db.execute(overlap_query)
    if overlap_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Комната уже забронирована на это время."
        )

    temp_user_id = 1

    new_booking = models.Booking(
        user_id=temp_user_id,
        room_id=booking.room_id,
        start_time=booking.start_time,
        end_time=booking.end_time
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = exception.detail if exception.detail else "An error occurred."
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exception.status_code, content={"detail": message})
    return templates.TemplateResponse(request, "error.html", {"status_code": exception.status_code, "message": message}, status_code=exception.status_code)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        errors = exception.errors()
        
        for err in errors:
            if "ctx" in err and "error" in err["ctx"]:
                err["ctx"]["error"] = str(err["ctx"]["error"])

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, 
            content={"detail": errors}
        )
    
    return templates.TemplateResponse(
        request, 
        "error.html", 
        {"status_code": status.HTTP_422_UNPROCESSABLE_CONTENT, "message": "Invalid request."}, 
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )