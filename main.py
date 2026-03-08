from fastapi import FastAPI, File, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from PIL import Image, ImageEnhance
import io
import zxingcpp
from datetime import datetime, timedelta
from enum import Enum  # <--- Added Enum import

# Import our database and models
from database import engine, Base, get_db
import models

# Create the tables in the database (if they don't exist)
models.Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI(title="Coupon Manager API")

# --- Define our constrained list of companies (Enum) ---
class CompanyEnum(str, Enum):
    shufersal = "Shufersal"
    victory = "Victory"
    wolt = "Wolt"
    buyme = "BuyMe"

@app.get("/")
def read_root():
    return {"message": "Welcome to the Coupon Manager API!"}

@app.post("/upload-coupon/")
async def upload_coupon(
    amount: float = Form(...),            
    company: CompanyEnum = Form(...),     # <--- Changed type to CompanyEnum
    file: UploadFile = File(...),         
    db: Session = Depends(get_db)         
):
    try:
        # Read the uploaded file into memory
        contents = await file.read()
        
        # --- IMAGE PREPROCESSING ---
        image = Image.open(io.BytesIO(contents)).convert('L')
        image.thumbnail((1000, 1000))
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Decode the barcode
        decoded_objects = zxingcpp.read_barcodes(image)
        
        if len(decoded_objects) == 0:
            return {"status": "error", "message": "No barcode found in the image. Please try a clearer screenshot."}
        
        barcode_number = decoded_objects[0].text
        
        # Check if exists
        existing_coupon = db.query(models.Coupon).filter(models.Coupon.barcode == barcode_number).first()
        if existing_coupon:
            return {"status": "error", "message": "This coupon already exists in the system."}

        future_expiration_date = datetime.now() + timedelta(days=3652)

        # Create new coupon (using company.value to get the actual string)
        new_coupon = models.Coupon(
            barcode=barcode_number,
            amount=amount,
            company=company.value,  # <--- Extracting the string from the Enum
            expiration_date=future_expiration_date  
        )
        
        db.add(new_coupon)
        db.commit()
        db.refresh(new_coupon) 
        
        return {
            "status": "success",
            "message": "Coupon saved successfully!",
            "coupon_id": new_coupon.id,
            "barcode": new_coupon.barcode,
            "company": new_coupon.company
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- NEW ENDPOINT: Get all active coupons ---
@app.get("/coupons/")
def get_coupons(db: Session = Depends(get_db)):
    try:
        active_coupons = db.query(models.Coupon).filter(models.Coupon.is_active == True).all()
        return {
            "status": "success",
            "total_count": len(active_coupons),
            "coupons": active_coupons
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}