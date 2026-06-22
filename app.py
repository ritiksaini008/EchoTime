from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime

app = Flask(__name__)

app.config["SECRET_KEY"] = "echotime_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True
    )

    password = db.Column(
        db.String(300)
    )


class Capsule(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200)
    )

    message = db.Column(
        db.Text
    )

    unlock_date = db.Column(
        db.String(50)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):
            login_user(user)

            return redirect(
                url_for("dashboard")
            )

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():

    capsules = Capsule.query.filter_by(
        user_id=current_user.id
    ).all()

    capsule_data = []

    today = datetime.now().date()

    for capsule in capsules:

        unlock = datetime.strptime(
            capsule.unlock_date,
            "%Y-%m-%d"
        ).date()

        days_left = (
            unlock - today
        ).days

        unlocked = days_left <= 0

        capsule_data.append({
            "id": capsule.id,
            "title": capsule.title,
            "unlock_date": capsule.unlock_date,
            "days_left": days_left,
            "unlocked": unlocked
        })

    return render_template(
        "dashboard.html",
        username=current_user.username,
        capsules=capsule_data
    )


@app.route(
    "/create_capsule",
    methods=["GET", "POST"]
)
@login_required
def create_capsule():

    if request.method == "POST":

        capsule = Capsule(
            title=request.form["title"],
            message=request.form["message"],
            unlock_date=request.form["unlock_date"],
            user_id=current_user.id
        )

        db.session.add(capsule)
        db.session.commit()

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "create_capsule.html"
    )


@app.route("/capsule/<int:id>")
@login_required
def capsule(id):

    capsule = Capsule.query.get_or_404(id)

    unlock = datetime.strptime(
        capsule.unlock_date,
        "%Y-%m-%d"
    ).date()

    today = datetime.now().date()

    if today < unlock:
        return """
        <h1>
        This capsule is still locked.
        </h1>
        """

    return render_template(
        "capsule.html",
        capsule=capsule
    )


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("home")
    )


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)