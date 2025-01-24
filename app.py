from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import qrcode
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # manufacturer, distributor, pharmacy


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch_id = db.Column(db.String(50), unique=True, nullable=False)
    qr_code_path = db.Column(db.String(200), nullable=False)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    history = db.relationship('TrackingHistory', backref='product', lazy=True)

class TrackingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who updated this

# Login Manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper Function: Generate QR Code
def generate_qr_code(batch_id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"http://192.168.0.105:8080/track/{batch_id}")
    qr.make(fit=True)
    qr_code_path = os.path.join('static/qr_codes', f"{batch_id}.png")
    os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_code_path)
    return qr_code_path

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        # Correct password hashing method
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create new user
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # Added role validation
        user = User.query.filter_by(email=email, role=role).first()  # Validate both email and role
        if user and check_password_hash(user.password, password):
            login_user(user)
            if role == 'manufacturer':
                return redirect(url_for('manufacturer'))
            elif role == 'distributor':
                return redirect(url_for('distributor'))
            elif role == 'pharmacy':
                return redirect(url_for('pharmacy'))
        flash('Invalid credentials or role', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Manufacturer Dashboard
@app.route('/manufacturer', methods=['GET', 'POST'])
@login_required
def manufacturer():
    if current_user.role != 'manufacturer':
        abort(403)
    if request.method == 'POST':
        name = request.form['name']
        batch_id = str(uuid.uuid4())
        qr_code_path = generate_qr_code(batch_id)
        product = Product(name=name, batch_id=batch_id, qr_code_path=qr_code_path, manufacturer_id=current_user.id)
        db.session.add(product)
        db.session.commit()
        flash('Product added and QR code generated!', 'success')
        return redirect(url_for('manufacturer'))
    products = Product.query.filter_by(manufacturer_id=current_user.id).all()
    return render_template('manufacturer.html', products=products)

# Distributor Dashboard
@app.route('/distributor', methods=['GET', 'POST'])
@login_required
def distributor():
    if current_user.role != 'distributor':
        abort(403)
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        status = request.form['status']
        
        # Create a new entry in TrackingHistory
        history = TrackingHistory(product_id=product_id, status=status, updated_by=current_user.id)
        db.session.add(history)
        db.session.commit()
        
        flash('Tracking status updated successfully!', 'success')
    
    # Fetch all products (added by manufacturers)
    products = Product.query.all()
    return render_template('distributor.html', products=products)


# Pharmacy Dashboard
@app.route('/pharmacy', methods=['GET', 'POST'])
@login_required
def pharmacy():
    if current_user.role != 'pharmacy':
        abort(403)
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        status = request.form['status']
        
        # Create a new entry in TrackingHistory
        history = TrackingHistory(product_id=product_id, status=status, updated_by=current_user.id)
        db.session.add(history)
        db.session.commit()
        flash('Tracking status updated!', 'success')
    
    # Fetch all products along with their tracking history
    products = Product.query.all()
    
    return render_template('pharmacy.html', products=products)



# Consumer: Track Product
@app.route('/track/<batch_id>')
def track_product(batch_id):
    product = Product.query.filter_by(batch_id=batch_id).first_or_404()
    
    # Retrieve the manufacturer (User) and distributor (User) from the Product model
    manufacturer = User.query.get(product.manufacturer_id)
    distributor = User.query.filter_by(role='distributor').first()  # Assuming there's one distributor, adjust as needed
    
    # Retrieve the tracking history for the product
    history = TrackingHistory.query.filter_by(product_id=product.id).all()

    # Create a list to store user data (updated_by users)
    history_details = []
    for entry in history:
        updated_user = User.query.get(entry.updated_by)  # Retrieve the user (pharmacy or admin) who updated the status
        history_details.append({
            'status': entry.status,
            'timestamp': entry.timestamp,
            'updated_by': updated_user.username if updated_user else 'Unknown'
        })

    # Pass all the necessary information to the template
    return render_template(
        'consumer.html', 
        product=product, 
        manufacturer=manufacturer,
        distributor=distributor,
        history=history_details
    )


# Initialize the Database
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080,debug=True)

