from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class ParkingSpot(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    address: str
    price_per_hour: float
    total_spots: int
    available_spots: int

class Booking(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    parking_spot_id: str
    vehicle: str
    date: str  # e.g., "2025-08-25"
    start_time: str  # e.g., "14:00"
    end_time: str  # e.g., "18:00"
    price: float
    status: str = "confirmed"  # confirmed, completed, cancelled
    spot_number: str

class BookingCreate(BaseModel):
    user_id: str
    parking_spot_id: str
    vehicle: str
    date: str
    start_time: str
    end_time: str
    spot_number: str

class Fastag(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    balance: float = 0.0
    linked_vehicles: List[str] = []

class Transaction(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    type: str  # recharge, payment
    amount: float
    date: datetime = Field(default_factory=datetime.utcnow)
    description: str

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: str
    phone: Optional[str] = None
    profileImage: Optional[str] = None

class RechargeRequest(BaseModel):
    user_id: str
    amount: float

class LinkVehicleRequest(BaseModel):
    user_id: str
    vehicle: str

class SlotBooking(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    slotId: Optional[str]
    userId: Optional[str]
    vehicleId: Optional[str]
    stationId: Optional[str]
    bookingStartTime: Optional[datetime]
    bookingEndTime: Optional[datetime]
    amountPaid: Optional[float]
    paymentMethod: Optional[str]
    paymentStatus: Optional[str]
    status: Optional[str]
    reservationExpiresAt: Optional[datetime]
    cancelReason: Optional[str]
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]
