from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from database import Base
import datetime

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True)
    amount = Column(Float)
    used_date = Column(DateTime, nullable=True)
    
    # Changed from network to company!
    company = Column(String, index=True) 
    expiration_date = Column(DateTime, nullable=True) 
    
    # Status fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)