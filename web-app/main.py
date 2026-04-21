import logging
from pathlib import Path
import sys
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
from threading import Thread

from council.setup_council import setup_council
plt.switch_backend('agg')
import random
import data
import os
from api import api_view
from api import ThingsBoardAuth
from telemetry.subscribe_telemetry import subscribe
from whitenoise import WhiteNoise
from dotenv import load_dotenv
from database import db
from users import Users
from council import Council
import httpx

load_dotenv()

# Initialise flask app
app = Flask(__name__, static_folder="static")
bootstrap = Bootstrap(app)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "pool_size": 2,
    "max_overflow": 3,
}
app.config["THINGSBOARD_URL"] = os.getenv("THINGSBOARD_URL", "https://thingsboard.cs.cf.ac.uk")
app.config["THINGSBOARD_USERNAME"] = os.getenv("THINGSBOARD_USERNAME")
app.config["THINGSBOARD_PASSWORD"] = os.getenv("THINGSBOARD_PASSWORD")

app.config["BIN_COLLECTION_API"] = os.getenv("BIN_COLLECTION_API", "https://group-30-collection.apps.containers.cs.cf.ac.uk")

app.logger.setLevel(logging.INFO if app.debug else logging.WARNING)
print(f"Logging level set to: {app.logger.level}")

# Set up static files in production
static_directory = Path(__file__).resolve().parent / "static"
app.logger.info(f"Configuring static file serving from: {static_directory}")
app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_directory.as_posix(), prefix=static_directory.as_posix())

# Initialise shared ThingsBoard auth client once per app process.
tb_auth = ThingsBoardAuth(
    app.config["THINGSBOARD_URL"],
    app.config["THINGSBOARD_USERNAME"],
    app.config["THINGSBOARD_PASSWORD"],
)
app.extensions["thingsboard_auth"] = tb_auth

try:
    tb_auth.warmup()
except Exception as exc:
    app.logger.warning("ThingsBoard auth warmup failed: %s", exc)

# Initialise database and login manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# Add API blueprint
app.register_blueprint(api_view)



def create_thread_for_device(device_id: str) -> Thread:
    """Helper function to create a background thread for subscribing to telemetry for a given device ID."""
    # Start telemetry subscription in background
    app.logger.info(f"Starting telemetry subscription for  device_id: {device_id}")
    tb_token = tb_auth.get_token()
    return Thread(
        target=subscribe,
        args=(app, tb_token, device_id),
        daemon=True
    )

def setup_telemetry_threads():
    """Set up telemetry subscription threads for all users in the database."""
    with app.app_context():
        # Get all unique device IDs
        device_ids = set(user.device_id for user in Users.query.all())
        app.logger.info(f"Setting up telemetry threads for device IDs: {device_ids}")
        for device_id in device_ids:
            thread = create_thread_for_device(device_id)
            thread.start()
            app.logger.info(f"Started telemetry thread for device_id: {device_id}")

setup_telemetry_threads()

def get_facts():
    from pathlib import Path
    PROJECT_DIR = Path(__file__).parent
    path = PROJECT_DIR / 'static/facts.txt'
    try:
        file = path.read_text()
        lines = file.split("\n")
        facts = []
        for line in lines:
            facts.append(line)
        return facts
    except Exception as e:
        return [""]

FACTS = get_facts()


# create database
with app.app_context():
    # db.drop_all() # USE TO ADD NEW COLUMN IF ALL DATA CAN BE LOST
    db.create_all()

with app.app_context():
    inserted_councils = setup_council()
    if inserted_councils:
        app.logger.info("Inserted %s councils during startup setup", inserted_councils)

# load user for flask-login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if Users.query.filter_by(username=username).first():
            return render_template("home.html", error="Username already taken.")
        
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        id = request.form.get("device_id")
        if Users.query.filter_by(device_id=id).first():
            return render_template("home.html", error="Device ID already taken.")
        # check the id matches a thingsboard device

        local_council_id = request.form.get("council")

        UPRN = request.form.get("UPRN")

        new_user = Users(username=username, password=hashed_password, device_id=id, local_council_id=local_council_id, UPRN=UPRN)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        
        # Start telemetry subscription in background
        tb_token = tb_auth.get_token()
        Thread(
            target=subscribe,
            args=(app, tb_token, new_user.device_id),
            daemon=True
        ).start()
        
        return redirect(url_for("live"))
    
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        app.logger.info(f"Login attempt for username: {username}, found user: {bool(user)}")
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                
                
                return redirect(url_for("live"))
            return render_template("home.html", error="Incorrect password.")
        return render_template("home.html", error="Username does not exist.")
    
    return render_template("home.html")

@app.route("/")
def home():
    id = request.args.get("id")
    if id:
        return render_template("home.html", id=id)
    return render_template("home.html", id="")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html",fact=get_fact())

@app.route("/dashboard/data")
@login_required
def dashboard_data():
    time = request.args.get("time")
    return data.dashboard_data(time)

@app.route("/live")
@login_required
def live():

    device_id = current_user.device_id

    with httpx.Client() as Client:

        r = Client.get(f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/SHARED_SCOPE", headers=tb_auth.auth_headers(), timeout=10)

        if not r.is_success:
            app.logger.error(f"Failed to retrieve Thingsboard device {device_id} collection dates. Response: {r.text}")
            return "HTTPS request failed", 500
        
        payload = r.json()

        date = [attribute for attribute in payload if attribute.get("key", "") == "collection_date"][0]
        bins = [attribute for attribute in payload if attribute.get("key", "") == "bins"][0]

    
    return render_template("live.html",fact=get_fact(),bins=bins, date=date)

@app.route("/live/data")
@login_required
def live_data():
    return data.live_data()

@app.route("/leaderboard")
@login_required
def leaderboard():
    leaderboard_entries = [
        {
            "username": current_user.username,
            "points": current_user.points,
            "avatar_text": "".join(part[0].upper() for part in current_user.username.split()[:2]) or "U1",
            "is_current_user": True,
        },
        {
            "username": "User 2",
            "points": 23910,
            "avatar_text": "U2",
            "is_current_user": False,
        },
        {
            "username": "User 3",
            "points": 22500,
            "avatar_text": "U3",
            "is_current_user": False,
        },
        {
            "username": "User 4",
            "points": 21880,
            "avatar_text": "U4",
            "is_current_user": False,
        },
        {
            "username": "User 5",
            "points": 20150,
            "avatar_text": "U5",
            "is_current_user": False,
        },
    ]

    leaderboard_entries.sort(key=lambda entry: entry["points"], reverse=True)

    for index, entry in enumerate(leaderboard_entries, start=1):
        entry["rank"] = index
        entry["rank_class"] = f"rank-{index}" if index <= 3 else ""

    return render_template("leaderboard.html", leaderboard_entries=leaderboard_entries)

@app.route("/settings")
@login_required
def settings():
    # Get council name and ID for template
    council = Council.query.filter_by(id=current_user.local_council_id).first()
    return render_template("settings.html", user=current_user, password=current_user.password, council = council)

@app.route("/change_password", methods=["GET","POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        if not check_password_hash(current_user.password, current_password):
            return render_template("change_password.html", error="Current password is incorrect.")
        
        if new_password != confirm_password:
            return render_template("change_password.html", error="New passwords do not match.")
        
        hashed_new_password = generate_password_hash(new_password, method="pbkdf2:sha256")
        current_user.password = hashed_new_password
        db.session.commit()
        
        return redirect(url_for("settings"))
    
    return render_template("change_password.html")

@app.route("/change_council", methods=["GET", "POST"])
@login_required
def change_council():
    if not request.method == "POST":
        # Get list of councils for dropdown
        councils = Council.query.all()
        return render_template("change_council.html", councils=councils)

    new_council = request.form.get("new_council")
    council = Council.query.filter_by(id=new_council).first()
    if not council:
        return render_template("change_council.html", error="Selected council does not exist.")
    current_user.local_council_id = new_council
    db.session.commit()

    return redirect(url_for("settings"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

def get_fact():
    return random.choice(FACTS)

if __name__ == "__main__":
    app.run(port='7001')
