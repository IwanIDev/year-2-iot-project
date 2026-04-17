from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import random
import data
import os
from api import api_view
from api import ThingsBoardAuth
from whitenoise import WhiteNoise
from dotenv import load_dotenv

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

app.wsgi_app = WhiteNoise(app.wsgi_app, root="static/", prefix="static/")

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
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# Add API blueprint
app.register_blueprint(api_view)

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

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    device_id = db.Column(db.String(250), unique=True, nullable=False)
    local_council = db.Column(db.String(250), nullable=False)

# create database
with app.app_context():
    db.create_all()

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

        local_council = request.form.get("local_council")

        new_user = Users(username=username, password=hashed_password, device_id=id, local_council=local_council)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("live"))
    
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

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
    return render_template("live.html",fact=get_fact())

@app.route("/live/data")
@login_required
def live_data():
    return data.live_data()

@app.route("/leaderboard")
@login_required
def leaderboard():
    return render_template("leaderboard.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html", user=current_user, password=current_user.password, council = current_user.local_council)

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
    if request.method == "POST":
        current_council = request.form.get("local_council")
        new_council = request.form.get("new_council")

        """
        Need section here for verifying council exists in dictionary.
        """

        current_user.local_council = new_council
        db.session.commit()

        return redirect(url_for("settings"))

    return render_template("change_council.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

def get_fact():
    return random.choice(FACTS)

if __name__ == "__main__":
    app.run(port='7001')
