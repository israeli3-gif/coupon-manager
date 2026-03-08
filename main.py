from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

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

# Setup templates directory
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def view_coupons(request: Request, db: Session = Depends(get_db)):
    # Fetch all active coupons from the database
    coupons = db.query(models.Coupon).filter(models.Coupon.is_active == True).all()
    
    # Render the index.html template with the coupons data
    return templates.TemplateResponse("index.html", {"request": request, "coupons": coupons})

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
    


# --- NEW ENDPOINT: Mark a coupon as used ---
@app.post("/use-coupon/{coupon_id}")
async def use_coupon(coupon_id: int, db: Session = Depends(get_db)):
    try:
        # Find the coupon by ID
        coupon = db.query(models.Coupon).filter(models.Coupon.id == coupon_id).first()
        
        if not coupon:
            return {"status": "error", "message": "Coupon not found"}
            
        # Update status to inactive
        coupon.is_active = False
        db.commit()
        
        return {"status": "success", "message": "Coupon marked as used!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}