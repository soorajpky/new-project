import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, FileField, PasswordField
from wtforms.validators import DataRequired, Length
from geopy.geocoders import Nominatim
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_or_phone = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Advertisement Model
class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    renewal_date = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

# Form for Advertisement
class AdForm(FlaskForm):
    company_name = StringField("Company Name", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    renewal_date = DateField("Renewal Date", format='%Y-%m-%d', validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired()])
    image = FileField("Advertisement Image")

# Form for Login
class LoginForm(FlaskForm):
    email_or_phone = StringField("Email or Phone", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])

# Form for Registration
class RegisterForm(FlaskForm):
    email_or_phone = StringField("Email or Phone", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), Length(min=6)])

# Create database tables
with app.app_context():
    db.create_all()

# Home Route - List Ads
@app.route('/')
def index():
    ads = Advertisement.query.all()
    return render_template('index.html', ads=ads)

# Add Advertisement Route
@app.route('/add', methods=['GET', 'POST'])
@login_required  # Only logged-in users can add ads
def add_ad():
    form = AdForm()
    if form.validate_on_submit():
        company_name = form.company_name.data
        location = form.location.data
        renewal_date = form.renewal_date.data
        amount = form.amount.data
        image_file = request.files['image']

        # Save image
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
        else:
            filename = None

        # Get geolocation coordinates
        geolocator = Nominatim(user_agent="geoapi")
        geolocation = geolocator.geocode(location)
        latitude = geolocation.latitude if geolocation else None
        longitude = geolocation.longitude if geolocation else None

        new_ad = Advertisement(
            company_name=company_name,
            location=location,
            renewal_date=str(renewal_date),
            amount=float(amount),
            image=filename,
            latitude=latitude,
            longitude=longitude
        )

        db.session.add(new_ad)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add.html', form=form)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email_or_phone=form.email_or_phone.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html', form=form)

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data == form.confirm_password.data:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(email_or_phone=form.email_or_phone.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            return "Passwords do not match."
    return render_template('register.html', form=form)

# Get Geo-location
@app.route('/get_location/<address>')
def get_location(address):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(address)
    if location:
        return jsonify({'latitude': location.latitude, 'longitude': location.longitude})
    return jsonify({'error': 'Location not found'})

# Load User for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(debug=True)








