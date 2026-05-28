from pydantic import BaseModel, ConfigDict, Field

class RoomBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0, description="Capacity should be greater then 0")
    price_per_hour: int = Field(ge=0, description="Price cant be less then 0")

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    id:int

class ReviewBase(BaseModel):
    author: str = Field(min_length=1, max_length = 100)
    text: str = Field(min_length=1, max_length=500)
    room_id: int = Field(gt=0, description="ID комнаты, к которой оставляется отзыв")

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id:int