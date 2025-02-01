
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, FileField
from wtforms.validators import DataRequired
from geopy.geocoders import Nominatim

app = Flask(__name__)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Advertisement Model
class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    renewal_date = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)

# Form for Advertisement
class AdForm(FlaskForm):
    company_name = StringField("Company Name", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    renewal_date = DateField("Renewal Date", format='%Y-%m-%d', validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired()])
    image = FileField("Advertisement Image")

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

        new_ad = Advertisement(company_name=company_name, location=location,
                               renewal_date=str(renewal_date), amount=float(amount), image=filename)
        db.session.add(new_ad)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add.html', form=form)

# Get Geo-location
@app.route('/get_location/<address>')
def get_location(address):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(address)
    if location:
        return {'latitude': location.latitude, 'longitude': location.longitude}
    return {'error': 'Location not found'}

if __name__ == '__main__':
    app.run(debug=True)





