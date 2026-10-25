from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import sqlite3, os, shutil
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, BotoCoreError

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = BASE_DIR / "cloudfind.db"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-for-real-deployment")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
UPLOAD_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")
s3 = boto3.client("s3", region_name=S3_REGION) if S3_BUCKET else None


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                item_type TEXT NOT NULL CHECK(item_type IN ('Lost', 'Found')),
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                item_date TEXT NOT NULL,
                description TEXT NOT NULL,
                contact TEXT NOT NULL,
                image_filename TEXT,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        if count == 0:
            examples = [
                ("Black Backpack", "Lost", "Bags", "Library, 2nd floor", "2026-10-24",
                 "Black backpack with a blue keychain.", "student@example.com", None, "Open"),
                ("Water Bottle", "Found", "Accessories", "Canteen", "2026-10-24",
                 "Blue stainless-steel bottle found near the tables.", "student2@example.com", None, "Open"),
                ("Scientific Calculator", "Found", "Electronics", "Engineering Block", "2026-10-23",
                 "Calculator found after the afternoon lecture.", "student3@example.com", None, "Returned")
            ]
            conn.executemany("""
                INSERT INTO items (title,item_type,category,location,item_date,description,contact,image_filename,status,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, [(*x, datetime.now().isoformat(timespec="seconds")) for x in examples])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    kind = request.args.get("type", "").strip()
    category = request.args.get("category", "").strip()
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        params += [f"%{search}%"] * 3
    if kind in ("Lost", "Found"):
        query += " AND item_type = ?"
        params.append(kind)
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY id DESC"
    with connect_db() as conn:
        items = conn.execute(query, params).fetchall()
        stats = {
            "total": conn.execute("SELECT COUNT(*) FROM items").fetchone()[0],
            "lost": conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Lost' AND status='Open'").fetchone()[0],
            "found": conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Found' AND status='Open'").fetchone()[0],
            "returned": conn.execute("SELECT COUNT(*) FROM items WHERE status='Returned'").fetchone()[0],
        }
        categories = [r["category"] for r in conn.execute("SELECT DISTINCT category FROM items ORDER BY category").fetchall()]
    return render_template("index.html", items=items, stats=stats, q=search, kind=kind, category=category, categories=categories)


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        item_type = request.form.get("item_type", "")
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        item_date = request.form.get("item_date", "")
        description = request.form.get("description", "").strip()
        contact = request.form.get("contact", "").strip()
        image = request.files.get("image")

        if not all([title, item_type in ("Lost", "Found"), category, location, item_date, description, contact]):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("report"))

        filename = None
        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Image must be PNG, JPG, JPEG, GIF, or WEBP.", "error")
                return redirect(url_for("report"))

            safe_name = secure_filename(image.filename)
            unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"

            if S3_BUCKET and s3:
                object_key = f"items/{unique_name}"
                try:
                    image.seek(0)
                    s3.upload_fileobj(
                        image,
                        S3_BUCKET,
                        object_key,
                        ExtraArgs={"ContentType": image.mimetype or "application/octet-stream"}
                    )
                    # Prefix identifies this as an S3 object in the existing DB column.
                    filename = f"s3__{object_key}"
                except (ClientError, BotoCoreError) as exc:
                    app.logger.exception("S3 upload failed")
                    flash("Photo upload to cloud storage failed. Check AWS permissions and region, then try again.", "error")
                    return redirect(url_for("report"))
            else:
                filename = unique_name
                image.save(UPLOAD_DIR / filename)

        with connect_db() as conn:
            conn.execute("""
                INSERT INTO items (title,item_type,category,location,item_date,description,contact,image_filename,status,created_at)
                VALUES (?,?,?,?,?,?,?,?, 'Open', ?)
            """, (title, item_type, category, location, item_date, description, contact, filename,
                  datetime.now().isoformat(timespec="seconds")))
        flash("Your item report was added successfully.", "success")
        return redirect(url_for("index"))
    return render_template("report.html")


@app.route("/item/<int:item_id>")
def item_detail(item_id):
    with connect_db() as conn:
        item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not item:
        flash("Item not found.", "error")
        return redirect(url_for("index"))
    return render_template("detail.html", item=item)


@app.route("/item/<int:item_id>/status", methods=["POST"])
def update_status(item_id):
    status = request.form.get("status")
    if status not in ("Open", "Returned"):
        flash("Invalid status.", "error")
        return redirect(url_for("index"))
    with connect_db() as conn:
        conn.execute("UPDATE items SET status=? WHERE id=?", (status, item_id))
    flash("Item status updated.", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    with connect_db() as conn:
        row = conn.execute("SELECT image_filename FROM items WHERE id=?", (item_id,)).fetchone()
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))

    if row and row["image_filename"]:
        filename = row["image_filename"]
        try:
            if filename.startswith("s3__"):
                if S3_BUCKET and s3:
                    object_key = filename[len("s3__"):]
                    s3.delete_object(Bucket=S3_BUCKET, Key=object_key)
            else:
                (UPLOAD_DIR / filename).unlink(missing_ok=True)
        except (OSError, ClientError, BotoCoreError):
            app.logger.exception("Image cleanup failed")
    flash("Listing deleted.", "success")
    return redirect(url_for("index"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    if filename.startswith("s3__"):
        if not S3_BUCKET or not s3:
            return "S3 is not configured", 503

        object_key = filename[len("s3__"):]
        try:
            signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET, "Key": object_key},
                ExpiresIn=300
            )
            return redirect(signed_url)
        except (ClientError, BotoCoreError):
            app.logger.exception("Unable to generate S3 image URL")
            return "Unable to retrieve image from S3", 404

    # Compatibility with images uploaded before S3 was configured.
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/backup", methods=["POST"])
def backup():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"cloudfind_backup_{stamp}.db"
    try:
        with connect_db() as conn:
            destination = sqlite3.connect(target)
            conn.backup(destination)
            destination.close()
        flash(f"Database backup created: {target.name}", "success")
    except Exception as exc:
        app.logger.exception("Database backup failed")
        flash(f"Backup failed: {exc}", "error")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "ok", "application": "CloudFind", "database": "SQLite"}, 200


init_db()

if __name__ == "__main__":
    # debug=False avoids Flask's interactive debugger during normal testing.
    app.run(debug=False)
