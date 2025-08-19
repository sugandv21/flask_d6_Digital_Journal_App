from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from forms import RegistrationForm, LoginForm, JournalForm
from models import db, User, Journal

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecret"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "journal.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("login"))
        hashed_pw = generate_password_hash(form.password.data)
        user = User(email=form.email.data, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user:
            flash("No account found. Please register first.", "warning")
            return redirect(url_for("register"))

        if check_password_hash(user.password_hash, form.password.data):
            login_user(user)  # ✅ This logs user in
            session["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            flash("Login successful!", "success")
            return redirect(url_for("home"))  # ✅ Redirect to home
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/home")
@login_required
def home():
    entries = Journal.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", entries=entries, last_login=session.get("last_login"))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_entry():
    form = JournalForm()
    if form.validate_on_submit():
        entry = Journal(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(entry)
        db.session.commit()
        flash("Journal entry added!", "success")
        return redirect(url_for("home"))
    return render_template("add_entry.html", form=form)


@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = Journal.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("home"))

    form = JournalForm(obj=entry)
    if form.validate_on_submit():
        entry.title = form.title.data
        entry.content = form.content.data
        db.session.commit()
        flash("Journal entry updated!", "success")
        return redirect(url_for("home"))
    return render_template("edit_entry.html", form=form, entry=entry)


@app.route("/delete/<int:entry_id>")
@login_required
def delete_entry(entry_id):
    entry = Journal.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("home"))

    db.session.delete(entry)
    db.session.commit()
    flash("Journal entry deleted.", "info")
    return redirect(url_for("home"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
