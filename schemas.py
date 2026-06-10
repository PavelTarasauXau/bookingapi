from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserBase(BaseModel):
    username: str = Field(min_length = 1, max_length= 20)
    email: EmailStr = Field(max_length = 50)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id:int


class RoomBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0, description="Capacity should be greater then 0")
    price_per_hour: int = Field(ge=0, description="Price cant be less then 0")

class RoomCreate(RoomBase):
    pass

class RoomUpdate(RoomBase):
    title: Optional[str] = None
    capacity: Optional[int] = None
    price_per_hour: Optional[int] = None


class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    id:int

class ReviewBase(BaseModel):
    author: str = Field(min_length=1, max_length = 100)
    text: str = Field(min_length=1, max_length=500)
    room_id: int = Field(gt=0, description="ID комнаты, к которой оставляется отзыв")

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(ReviewBase):
    author: Optional[str] = None
    text: Optional[str] = None
    room_id: Optional[int] = None

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id:int

class BookingBase(BaseModel):
    start_time: datetime
    end_time: datetime

class BookingCreate(BookingBase):
    room_id: int

    @field_validator("end_time")
    @classmethod
    def check_dates(cls, end_time: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("Время окончания бронирования должно быть позже времени начала")
        if start_time and start_time < datetime.utcnow():
            raise ValueError("Нельзя забронировать комнату на прошедшее время")
        return end_time

class BookingResponse(BookingBase):
    id: int
    user_id: int
    room_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)