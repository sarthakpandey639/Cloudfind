# CloudFind — Campus Lost & Found Portal

A zero-cost college mini-project prototype built with Python Flask, SQLite, HTML, CSS, and JavaScript.

## Features
- Lost/found listings with search and category/type filters
- Create listings and upload images
- Mark items as returned or reopen them
- Delete listings
- Dashboard statistics
- SQLite database CRUD operations
- Local database backup
- Health endpoint at `/health`
- Responsive user interface

## Run on Windows
1. Install Python 3.10+ from https://www.python.org/downloads/ (check "Add Python to PATH").
2. Extract this folder.
3. Open a terminal in this folder.
4. Run:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

5. Open http://127.0.0.1:5000 in your browser.

If `py` doesn't work, try `python` instead.

## Demo plan
1. Browse the seeded sample listings.
2. Search for "backpack" and filter by Lost/Found.
3. Add a new found item and upload a photo.
4. Mark an item as Returned and show the dashboard counter update.
5. Delete a test listing.
6. Click "Create database backup"; a timestamped backup appears in `backups/`.
7. Open http://127.0.0.1:5000/health to show the health endpoint.

## How it maps to cloud computing concepts
- Web server/app hosting: Flask web server locally (cloud VM deployment can be discussed or done later).
- Relational database CRUD: SQLite locally; replace with MySQL/PostgreSQL for a cloud database demonstration.
- Object storage: `uploads/` simulates the object storage layer; S3 can replace it later.
- Backup and recovery: SQLite online backup creates a restorable `.db` copy.
- Monitoring: `/health` is a simple health-check endpoint; CloudWatch can be used if deployed on AWS.
- IAM/security: explain least privilege, private object storage, restricted inbound ports, and MFA as deployment controls.

**Be accurate in the presentation:** this version runs locally and does not itself create AWS resources. Explain S3, EC2, IAM, and CloudWatch as planned deployment equivalents unless you actually deploy them.

## Important prototype limitations
This is a college demo, not a production-ready service. It has no login/role enforcement, and contact emails are shown on item detail pages. Use only fake/sample data. Before real deployment, add authentication, authorization, CSRF protection, safer contact handling, production server configuration, secure secret management, and stricter upload validation.
