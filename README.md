# CloudFind — Campus Lost & Found Portal

CloudFind is a web application designed to help students report, search for, and recover lost and found items on campus. It combines a simple web interface with cloud-based image storage using Amazon Web Services (AWS).

## Features

- Report lost and found items.
- Upload item photographs.
- Browse and search listings by keywords, item type, and category.
- View detailed information about each listing.
- Update item status to Open or Returned.
- Store item information in an SQLite database.
- Upload photographs to Amazon S3.
- Display private S3 images using temporary pre-signed URLs.
- Delete listings and their associated images.
- Create local database backups.
- Health-check endpoint for basic application status.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| HTML and CSS | User interface |
| SQLite | Local database |
| Amazon S3 | Cloud object storage for photographs |
| AWS IAM | Access control and permissions |
| AWS CLI | AWS command-line configuration |
| Boto3 | Python SDK for AWS |

## System Architecture

CloudFind currently uses a hybrid architecture:

1. **Frontend:** HTML and CSS provide the user interface.
2. **Backend:** Flask handles requests, form submissions, validation, and application logic.
3. **Database:** SQLite stores item details and image references locally.
4. **Cloud storage:** Amazon S3 stores newly uploaded photographs.
5. **Authentication:** Boto3 uses the AWS credential configuration to authenticate requests to S3.
6. **Image retrieval:** Flask generates temporary pre-signed URLs so the browser can display images without making the bucket public.

**Important:** The Flask application and SQLite database currently run on the local computer. Only the integrated image storage uses AWS S3.

## AWS S3 Integration

CloudFind uses an S3 bucket to store uploaded photographs.

When a user submits an item with a photograph:

1. Flask validates the submitted form and image extension.
2. Boto3 uploads the image to the configured S3 bucket.
3. The database stores the item's details and a reference to the image.
4. When the image is requested, Flask generates a temporary pre-signed URL.
5. The browser retrieves the image using that URL.

The application supports locally stored images as a fallback when S3 is not configured.

### Security

- Keep S3 Block Public Access enabled.
- Use a dedicated IAM identity with only the required permissions.
- Never hardcode AWS access keys or secret keys in the source code.
- Configure AWS credentials using the AWS CLI or another supported credential provider.
- Store the Flask secret key in an environment variable for deployment.
- Use temporary pre-signed URLs for private image access.

## Project Structure

```text
Cloudfind/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── detail.html
│   └── report.html
├── uploads/       # Local image fallback
├── backups/       # Local database backups
└── cloudfind.db   # Local SQLite database
```

The `uploads/`, `backups/`, and `cloudfind.db` entries represent local runtime data and should not be committed to GitHub.

## Prerequisites

- Python 3.10 or later
- Git
- An AWS account
- An S3 bucket
- AWS CLI installed and configured
- An IAM identity with the required S3 permissions

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/sarthakpandey639/Cloudfind.git
cd Cloudfind
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure AWS credentials

Configure the AWS CLI using your own IAM credentials:

```powershell
aws configure
```

Enter your access key ID, secret access key, actual bucket region, and `json` as the output format when prompted.

Never include these credentials in the repository.

### 5. Set environment variables

For the existing project bucket, run these commands in PowerShell:

```powershell
$env:S3_BUCKET = "cloudfind-photos-123"
$env:AWS_DEFAULT_REGION = "ap-southeast-2"
```

The region `ap-southeast-2` corresponds to Asia Pacific (Sydney), where the current bucket is hosted.

These variables apply to the current PowerShell session. Set them again in a new terminal before starting the application.

### 6. Run the application

```powershell
python app.py
```

Open the application in your browser:

http://127.0.0.1:5000

## Testing the S3 Integration

Verify that AWS credentials work:

```powershell
aws sts get-caller-identity
```

Check that the bucket is accessible:

```powershell
aws s3 ls s3://cloudfind-photos-123
```

List uploaded item photographs:

```powershell
aws s3 ls s3://cloudfind-photos-123/items/
```

To test the complete workflow, submit a new item with a JPG, PNG, or WEBP photograph and confirm that the image appears in the application and in the S3 bucket.

## Application Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | View and search listings |
| `/report` | GET, POST | Submit a lost or found item |
| `/item/<id>` | GET | View item details |
| `/item/<id>/status` | POST | Update item status |
| `/item/<id>/delete` | POST | Delete a listing |
| `/uploads/<filename>` | GET | Retrieve a local or S3 image |
| `/backup` | POST | Create a local SQLite backup |
| `/health` | GET | Check application status |

## Current Limitations

- The website is not yet deployed to a public web server.
- The SQLite database is stored locally.
- Database backups are currently local rather than automatically uploaded to S3.
- The application is a college project prototype and requires additional security hardening before production deployment.

## Future Enhancements

- Deploy the Flask application to a cloud server.
- Migrate SQLite to a managed relational database.
- Store database backups in S3.
- Add user authentication and authorization.
- Implement automated monitoring and logging.
- Improve input validation and production security.

## Learning Outcomes

This project demonstrates web application development, database operations, cloud object storage, IAM-based access control, AWS CLI usage, SDK integration, and secure retrieval of private cloud objects.

## Author

**Sarthak Pandey**

GitHub: https://github.com/sarthakpandey639/Cloudfind

