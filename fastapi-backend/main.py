from fastapi import FastAPI, HTTPException, status, Form, Path, File, UploadFile, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from bson import ObjectId
from bson.errors import InvalidId
import bcrypt
import logging

from database import connect_to_mongo, close_mongo_connection, mongodb
from models import ParkingSpot, Booking, BookingCreate, Fastag, Transaction, User, RechargeRequest, LinkVehicleRequest, SlotBooking

app = FastAPI()

logging.basicConfig(level=logging.DEBUG)

# Allow CORS for Flutter app (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Helper to convert ObjectId to str
def obj_id_to_str(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# Parking Spot Endpoints
@app.get("/parking-spots", response_model=List[ParkingSpot])
async def get_parking_spots():
    spots = []
    cursor = mongodb.db.stations.find()
    async for spot in cursor:
        spot = obj_id_to_str(spot)
        # Map to ParkingSpot model, provide defaults if missing
        parking_spot = ParkingSpot(
            id=spot.get("_id"),
            name=spot.get("name", ""),
            address=spot.get("address", ""),
            price_per_hour=spot.get("price_per_hour", 0.0),
            total_spots=spot.get("total_spots", 0),
            available_spots=spot.get("available_spots", 0)
        )
        spots.append(parking_spot)
    return spots

@app.get("/stations/{station_id}")
async def get_station(station_id: str):
    from bson import ObjectId
    try:
        obj_id = ObjectId(station_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid station ID format")
    station = await mongodb.db.stations.find_one({"_id": obj_id})
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return obj_id_to_str(station)

@app.post("/parking-spots", response_model=ParkingSpot, status_code=status.HTTP_201_CREATED)
async def create_parking_spot(spot: ParkingSpot):
    spot_dict = spot.dict(by_alias=True)
    result = await mongodb.db.parking_spots.insert_one(spot_dict)
    spot_dict["_id"] = str(result.inserted_id)
    return spot_dict

# Booking Endpoints
@app.get("/bookings/{user_id}", response_model=List[Booking])
async def get_bookings(user_id: str):
    bookings = []
    cursor = mongodb.db.bookings.find({"user_id": user_id})
    async for booking in cursor:
        bookings.append(obj_id_to_str(booking))
    return bookings

@app.post("/bookings", response_model=Booking, status_code=status.HTTP_201_CREATED)
async def create_booking(booking: BookingCreate):
    booking_dict = booking.dict()
    booking_dict["status"] = "confirmed"
    result = await mongodb.db.bookings.insert_one(booking_dict)
    booking_dict["_id"] = str(result.inserted_id)
    return booking_dict

@app.put("/bookings/{booking_id}/cancel", response_model=Booking)
async def cancel_booking(booking_id: str):
    result = await mongodb.db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": "cancelled"}}
    )
    if result.modified_count == 1:
        booking = await mongodb.db.bookings.find_one({"_id": ObjectId(booking_id)})
        return obj_id_to_str(booking)
    raise HTTPException(status_code=404, detail="Booking not found")

# Fastag Endpoints
@app.get("/fastag/{user_id}/balance", response_model=Fastag)
async def get_fastag_balance(user_id: str):
    fastag = await mongodb.db.fastag.find_one({"user_id": user_id})
    if fastag:
        return obj_id_to_str(fastag)
    raise HTTPException(status_code=404, detail="Fastag not found")

@app.post("/fastag/recharge", response_model=Transaction)
async def recharge_fastag(recharge: RechargeRequest):
    fastag = await mongodb.db.fastag.find_one({"user_id": recharge.user_id})
    if not fastag:
        # Create fastag if not exists
        fastag_data = {"user_id": recharge.user_id, "balance": recharge.amount, "linked_vehicles": []}
        await mongodb.db.fastag.insert_one(fastag_data)
    else:
        new_balance = fastag["balance"] + recharge.amount
        await mongodb.db.fastag.update_one({"user_id": recharge.user_id}, {"$set": {"balance": new_balance}})
    transaction = {
        "user_id": recharge.user_id,
        "type": "recharge",
        "amount": recharge.amount,
        "description": "Fastag recharge"
    }
    result = await mongodb.db.transactions.insert_one(transaction)
    transaction["_id"] = str(result.inserted_id)
    return transaction

@app.get("/fastag/{user_id}/transactions", response_model=List[Transaction])
async def get_transactions(user_id: str):
    transactions = []
    cursor = mongodb.db.transactions.find({"user_id": user_id}).sort("date", -1)
    async for txn in cursor:
        txn["_id"] = str(txn["_id"])
        transactions.append(txn)
    return transactions

@app.post("/fastag/link-vehicle")
async def link_vehicle(link_req: LinkVehicleRequest):
    fastag = await mongodb.db.fastag.find_one({"user_id": link_req.user_id})
    if not fastag:
        raise HTTPException(status_code=404, detail="Fastag not found")
    if link_req.vehicle not in fastag.get("linked_vehicles", []):
        await mongodb.db.fastag.update_one(
            {"user_id": link_req.user_id},
            {"$push": {"linked_vehicles": link_req.vehicle}}
        )
    return JSONResponse(content={"message": "Vehicle linked successfully"})

@app.post("/fastag/deactivate")
async def deactivate_fastag(user_id: str):
    result = await mongodb.db.fastag.delete_one({"user_id": user_id})
    if result.deleted_count == 1:
        return JSONResponse(content={"message": "Fastag deactivated successfully"})
    raise HTTPException(status_code=404, detail="Fastag not found")

# User Endpoints
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await mongodb.db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user["_id"] = str(user["_id"])
        return user
    raise HTTPException(status_code=404, detail="User not found")

# Slots by Station ID
@app.get("/slots/{station_id}")
async def get_slots_by_station(station_id: str):
    from bson import ObjectId
    try:
        obj_station_id = ObjectId(station_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid station ID format")
    slots = []
    cursor = mongodb.db.slots.find({"stationId": obj_station_id})
    async for slot in cursor:
        slot["_id"] = str(slot["_id"])
        slots.append(slot)
    return slots

# Reviews by Station ID with average rating
@app.get("/reviews/{station_id}")
async def get_reviews_by_station(station_id: str):
    from bson import ObjectId
    try:
        obj_station_id = ObjectId(station_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid station ID format")
    reviews = []
    cursor = mongodb.db.reviews.find({"stationId": obj_station_id})
    total_rating = 0
    count = 0
    async for review in cursor:
        review["_id"] = str(review["_id"])
        reviews.append(review)
        if "rating" in review:
            total_rating += review["rating"]
            count += 1
    average_rating = total_rating / count if count > 0 else None
    return {"reviews": reviews, "average_rating": average_rating}

@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    user_dict = user.dict(exclude_unset=True)
    result = await mongodb.db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

# Login Endpoint

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    logging.debug(f"Login attempt with email: '{email}'")
    # Trim spaces and convert email to lowercase for case-insensitive search
    email_clean = email.strip().lower()
    user = await mongodb.db.users.find_one({"email": {"$regex": f"^{email_clean}$", "$options": "i"}})
    if not user:
        logging.debug(f"Login failed: user not found for email {email_clean}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    hashed_password = user.get("password")
    if not hashed_password:
        logging.debug(f"Login failed: no password hash for user {email_clean}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Debug prints
    logging.debug(f"Stored hash: {hashed_password}")
    logging.debug(f"Password input: {password}")
    # bcrypt hash stored in DB is a string, decode to bytes for checkpw
    hashed_password_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    password_bytes = password.encode('utf-8')
    if not bcrypt.checkpw(password_bytes, hashed_password_bytes):
        logging.debug(f"Login failed: password mismatch for user {email_clean}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Remove password before returning user data
    user.pop("password", None)
    user["_id"] = str(user["_id"])
    logging.debug(f"Login successful for user {email_clean}")
    return user

@app.get("/users/email/{email}")
async def get_user_by_email(email: str = Path(...)):
    email_clean = email.strip().lower()
    user = await mongodb.db.users.find_one({"email": {"$regex": f"^{email_clean}$", "$options": "i"}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    user.pop("password", None)
    return user

@app.post("/upload-profile-image")
async def upload_profile_image(file: UploadFile = File(...)):
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(file.file, folder="profile_images")
        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.put("/users/update-profile")
async def update_user_profile(email: str = Form(...), name: str = Form(...), phone: str = Form(None), profileImage: str = Form(None)):
    email_clean = email.strip().lower()
    user = await mongodb.db.users.find_one({"email": {"$regex": f"^{email_clean}$", "$options": "i"}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = {"name": name}
    if phone:
        update_data["phone"] = phone
    if profileImage:
        update_data["profileImage"] = profileImage
    await mongodb.db.users.update_one({"email": user["email"]}, {"$set": update_data})
    return {"message": "Profile updated successfully"}

@app.get("/slotbookings/{user_id}", response_model=List[SlotBooking])
async def get_slotbookings(user_id: str):
    from bson import ObjectId
    try:
        obj_user_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    bookings = []
    cursor = mongodb.db.slotbookings.find({"userId": obj_user_id})
    async for booking in cursor:
        # Convert ObjectId fields to str for JSON serialization
        booking["_id"] = str(booking["_id"])
        booking["slotId"] = str(booking["slotId"]) if "slotId" in booking else None
        booking["userId"] = str(booking["userId"]) if "userId" in booking else None
        booking["vehicleId"] = str(booking["vehicleId"]) if "vehicleId" in booking else None
        booking["stationId"] = str(booking["stationId"]) if "stationId" in booking else None
        bookings.append(booking)
    return bookings


import random
import string
import smtplib
import asyncio
from email.mime.text import MIMEText
from fastapi import Form, Depends, Header, File, UploadFile
from pydantic import EmailStr
from datetime import datetime, timedelta
import cloudinary
import cloudinary.uploader
import cloudinary.api

import os

# Email credentials from environment variables
EMAIL_USER = os.getenv("EMAIL_USER", "davinash46479@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "yygq zhjk pykh ntci")

# Cloudinary configuration
cloudinary.config(
    cloud_name="dwgwtx0jz",
    api_key="523154331876144",
    api_secret="j-XAGu4EUdSjqw9tGwa85ZbQ0v0"
)

# Verification code storage with expiration
verification_codes = {}

async def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, [to_email], msg.as_string())
        server.quit()
        print(f"Sent email to {to_email}")
    except Exception as e:
        import logging
        logging.error(f"Failed to send email to {to_email}: {e}")

@app.post("/change-password")
async def change_password(current_password: str = Form(...), new_password: str = Form(...), x_user_email: str = Header(...)):
    import logging
    logging.debug(f"Received /change-password request with headers: {dict()} and form data: current_password={current_password}, new_password={new_password}, x_user_email={x_user_email}")
    email = x_user_email
    user = await mongodb.db.users.find_one({"email": {"$regex": f"^{email.strip().lower()}$", "$options": "i"}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    hashed_password = user.get("password")
    if not hashed_password:
        raise HTTPException(status_code=401, detail="Invalid current password")
    hashed_password_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    current_password_bytes = current_password.encode('utf-8')
    if not bcrypt.checkpw(current_password_bytes, hashed_password_bytes):
        raise HTTPException(status_code=401, detail="Invalid current password")
    # Hash new password
    new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    await mongodb.db.users.update_one({"email": user["email"]}, {"$set": {"password": new_hashed.decode('utf-8')}})
    # TODO: Send email notification about password change
    return {"message": "Password changed successfully"}

@app.post("/send-verification-code")
async def send_verification_code(email: str = Form(...)):
    user = await mongodb.db.users.find_one({"email": {"$regex": f"^{email.strip().lower()}$", "$options": "i"}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    code = ''.join(random.choices(string.digits, k=4))
    expiration = datetime.utcnow() + timedelta(minutes=5)
    verification_codes[email] = {"code": code, "expires": expiration}
    # Send email asynchronously
    subject = "Your Verification Code"
    body = f"Your verification code is: {code}. It will expire in 5 minutes."
    asyncio.create_task(send_email(email, subject, body))
    print(f"Verification code for {email}: {code} (expires at {expiration.isoformat()} UTC)")
    return {"message": "Verification code sent"}

@app.post("/change-password-with-code")
async def change_password_with_code(email: str = Form(...), code: str = Form(...), new_password: str = Form(...)):
    stored_code = verification_codes.get(email)
    from datetime import datetime
    if (
        not stored_code
        or stored_code["code"] != code
        or stored_code["expires"] < datetime.utcnow()
    ):
        raise HTTPException(status_code=401, detail="Invalid or expired verification code")
    user = await mongodb.db.users.find_one({"email": {"$regex": f"^{email.strip().lower()}$", "$options": "i"}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    await mongodb.db.users.update_one({"email": user["email"]}, {"$set": {"password": new_hashed.decode('utf-8')}})
    # Remove used code
    verification_codes.pop(email, None)
    # TODO: Send email notification about password change
    return {"message": "Password changed successfully"}
