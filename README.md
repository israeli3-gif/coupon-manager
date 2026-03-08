Coupon Manager MVP
A full-stack web application designed to digitize and manage shopping coupons for various retail chains in Israel. This tool allows users to upload screenshots of coupons, automatically extracts barcode data, and stores them in a mobile-friendly dashboard for easy use at the checkout.

Features
Automatic Barcode Extraction: Uses computer vision to extract barcode numbers from uploaded screenshots.

Image Preprocessing: Implements grayscale conversion, resizing, and contrast enhancement to ensure high recognition accuracy for mobile screenshots.

Automated Expiration Tracking: Automatically calculates a 10-year validity period for new coupons.

Data Integrity: Uses Python Enums to ensure consistent naming for supported networks such as Shufersal, Wolt, and BuyMe.

Mobile-First Dashboard: A responsive UI that regenerates barcodes on-the-fly using JsBarcode for easy scanning at the register.

Soft Delete: Allows users to mark coupons as used, removing them from the active list while maintaining data history.

Tech Stack
Backend: Python, FastAPI

Database: SQLite, SQLAlchemy (ORM)

Image Processing: Pillow (PIL), zxing-cpp

Frontend: Jinja2 Templates, Bootstrap 5, JavaScript (Fetch API)

Dev Tools: Virtualenv, Git, Uvicorn

Technical Challenges and Solutions
High-Resolution Screenshot Processing
Challenge: Modern phone screenshots are often too large or have transparency layers that confuse standard barcode scanners.
Solution: I implemented an image preprocessing pipeline that converts images to grayscale, resizes them to optimal dimensions, and boosts contrast. This significantly increased the success rate of the extraction algorithm.

Database Synchronization
Challenge: Keeping the UI updated without complex frontend frameworks.
Solution: Utilized a combination of FastAPI's Jinja2 integration for initial rendering and the JavaScript Fetch API for asynchronous state updates to provide a seamless user experience.

Installation and Setup
Clone the repository:

Bash
git clone https://github.com/your-username/coupon-manager.git
cd coupon-manager
Set up a virtual environment:

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

Bash
pip install -r requirements.txt
Run the server:

Bash
uvicorn main:app --reload
Access the app:
Open http://127.0.0.1:8000 in your browser.