from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import random

# Initialise flask app
app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secretkey"

# Initialise database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

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
            return render_template("sign_up.html", error="Username already taken!")
        
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = Users(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    
    return render_template("sign_up.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("live_view"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html",fact=get_fact())

@app.route("/dashboard/data")
@login_required
def dashboard_data():
    time = request.args.get("time")

    data = {
        "xs":[
            ["Plastic","Paper","Glass","General Waste","Food"],
            ["17/3","18/3","19/3","20/3","21/3","Yesterday","Today"],
            [i for i in range(24)]
        ],
        "ys":[
            [random.randint(0,50) for _ in range(5)],
            [random.randint(0,100) for _ in range(7)],
            [random.randint(0,20) for _ in range(24)]
        ]
    }
    return data

@app.route("/live")
@login_required
def live_view():
    return render_template("live.html",fact=get_fact())

@app.route("/live/data")
@login_required
def live_data():
    tod = random.randint(9,20)
    data = {
        "recent":["Plastic","Paper","Glass","General Waste","Food"][random.randint(0,4)],
        "today_count":random.randint(20,50),
        "xs":[
            [i for i in range(24)]
        ],
        "ys":[
            [random.randint(0,10) for _ in range(tod)] + [0]*(24-tod)
        ]
    }
    return data

@app.route("/leaderboard")
@login_required
def leaderboard():
    return render_template("leaderboard.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html", user=current_user, password=current_user.password)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

def get_fact():
    from pathlib import Path
    PROJECT_DIR = Path(__file__).parent
    path = PROJECT_DIR / 'static/facts.txt'
    try:
        file = path.read_text()
        lines = file.split("\n")
        facts = []
        for line in lines:
            facts.append(line)
        return facts[random.randint(0,len(facts)-1)]
    except Exception as e:
        return e

if __name__ == "__main__":
    app.run(port='7001')