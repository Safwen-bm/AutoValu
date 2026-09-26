from typing import Optional
from pydantic import BaseModel


class CarInput(BaseModel):
    brand: str
    model: Optional[str] = None
    year: int
    fuel: Optional[str] = "gasoline"
    body_style: Optional[str] = None
    car_condition: Optional[str] = "medium"
    trim_level: Optional[str] = "standard"
    mileage_km: Optional[float] = None
    engine_cc: Optional[float] = None
    seats: Optional[float] = None
    doors: Optional[float] = None
    user_price: Optional[float] = None


class SubmitInput(BaseModel):
    brand: str
    model: Optional[str] = None
    year: int
    fuel: Optional[str] = None
    body_style: Optional[str] = None
    car_condition: Optional[str] = None
    trim_level: Optional[str] = None
    mileage_km: Optional[float] = None
    engine_cc: Optional[float] = None
    user_price: float
    predicted_price: float
    segment: str


class LoginInput(BaseModel):
    username: str
    password: str
