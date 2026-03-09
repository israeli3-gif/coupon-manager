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

from sqlalchemy import func

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
            
        # Update status to inactive + set used_date
        coupon.is_active = False
        coupon.used_date = datetime.now()
        db.commit()
        
        return {"status": "success", "message": "Coupon marked as used!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

from fastapi import Query

# --- NEW ENDPOINT: Algorithm to recommend optimal coupons ---
@app.get("/recommend-coupons/")
def recommend_coupons(
    company: str,
    bill_amount: float = Query(..., gt=0),
    db: Session = Depends(get_db)
):
    try:
        # 1. Fetch all active coupons for the requested company
        available_coupons = db.query(models.Coupon).filter(
            models.Coupon.company == company,
            models.Coupon.is_active == True
        ).all()

        # 2. Dynamic Programming approach (0/1 Knapsack variation)
        # dp dictionary format -> current_sum: (number_of_coupons, [list_of_coupon_ids])
        dp = {0.0: (0, [])}

        for coupon in available_coupons:
            current_dp = dict(dp) # Copy to prevent updating the dictionary while iterating
            for current_sum, (count, used_ids) in current_dp.items():
                # Calculate new sum and round to 2 decimals to avoid Python float precision issues
                new_sum = round(current_sum + coupon.amount, 2)
                
                # Rule 1: We cannot exceed the bill amount
                if new_sum <= bill_amount:
                    new_count = count + 1
                    
                    # Rule 2 & 3: Add to dp if it's a new sum, OR if we reached this sum with FEWER coupons
                    if new_sum not in dp or dp[new_sum][0] > new_count:
                        dp[new_sum] = (new_count, used_ids + [coupon.id])

        # 3. Find the best result
        max_sum = max(dp.keys())
        
        # If the max sum is 0, it means all coupons are bigger than the bill
        if max_sum == 0.0:
            return {"status": "success", "message": "No relevant coupons found for this amount.", "coupons": []}

        # Retrieve the winning coupon IDs
        best_coupon_ids = dp[max_sum][1]
        
        # Get the actual coupon objects to return to the user
        recommended = [c for c in available_coupons if c.id in best_coupon_ids]
        
        return {
            "status": "success",
            "total_value": max_sum,
            "coupons": recommended
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- NEW ENDPOINT: Statistics Dashboard ---
@app.get("/api/stats")
def get_statistics(db: Session = Depends(get_db)):
    try:
        # 1. Total value of active coupons
        total_value = db.query(func.sum(models.Coupon.amount)).filter(models.Coupon.is_active == True).scalar() or 0.0
        
        # 2. Total count of active coupons
        active_count = db.query(models.Coupon).filter(models.Coupon.is_active == True).count()
        
        # 3. Total count of used coupons
        used_count = db.query(models.Coupon).filter(models.Coupon.is_active == False).count()
        
        # 4. Group by company (for the Pie Chart)
        company_stats = db.query(
            models.Coupon.company, 
            func.sum(models.Coupon.amount), 
            func.count(models.Coupon.id)
        ).filter(models.Coupon.is_active == True).group_by(models.Coupon.company).all()

        companies_data = [{"name": c[0], "total_amount": round(c[1], 2), "count": c[2]} for c in company_stats]

        return {
            "status": "success",
            "total_active_value": round(total_value, 2),
            "active_count": active_count,
            "used_count": used_count,
            "by_company": companies_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}