from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prescription_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hospital_name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    id_proof = db.Column(db.String(100), nullable=False)
    approved = db.Column(db.Boolean, default=False)

class Pharmacy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    medicine_list = db.Column(db.String(500), nullable=False)
    dosage = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fulfilled = db.Column(db.Boolean, default=False)

    # Add this relationship to the Doctor model
    doctor = db.relationship('Doctor', backref='prescriptions')

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Medicine {self.name}>'


# Routes
@app.route('/')
def index():
    return render_template('index.html')

import os

@app.route('/doctor_signup', methods=['GET', 'POST'])
def doctor_signup():
    if request.method == 'POST':
        name = request.form['name']
        hospital_name = request.form['hospital_name']
        contact_info = request.form['contact_info']
        password = request.form['password']
        id_proof = request.files['id_proof']

        hashed_password = generate_password_hash(password)

        # Ensure the uploads directory exists
        uploads_dir = os.path.join(app.root_path, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        # Save the ID proof file
        id_proof_path = os.path.join(uploads_dir, id_proof.filename)
        id_proof.save(id_proof_path)

        doctor = Doctor(name=name, hospital_name=hospital_name, contact_info=contact_info, password_hash=hashed_password, id_proof=id_proof_path)
        db.session.add(doctor)
        db.session.commit()

        flash('Signup successful! Awaiting admin approval.', 'success')
        return redirect(url_for('index'))

    return render_template('doctor_signup.html')

@app.route('/pharmacy_signup', methods=['GET', 'POST'])
def pharmacy_signup():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        contact_info = request.form['contact_info']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        pharmacy = Pharmacy(name=name, address=address, contact_info=contact_info, password_hash=hashed_password)
        db.session.add(pharmacy)
        db.session.commit()

        flash('Signup successful!', 'success')
        return redirect(url_for('index'))

    return render_template('pharmacy_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if role == 'doctor':
            user = Doctor.query.filter_by(contact_info=email).first()
        elif role == 'pharmacy':
            user = Pharmacy.query.filter_by(contact_info=email).first()
        else:
            flash('Invalid role!', 'danger')
            return redirect(url_for('login'))

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = role
            flash('Login successful!', 'success')
            return redirect(url_for(f'{role}_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')

    return render_template('login.html')


@app.route('/doctor_dashboard', methods=['GET', 'POST'])
def doctor_dashboard():
    if 'role' in session and session['role'] == 'doctor':
        if request.method == 'POST':
            patient_name = request.form['patient_name']
            patient_dob_str = request.form['patient_dob']  # String from the form
            
            # Convert string to Python date object
            try:
                patient_dob = datetime.strptime(patient_dob_str, "%Y-%m-%d").date()
            except ValueError:
                flash('Invalid date format. Please enter a valid date.', 'danger')
                return redirect(url_for('doctor_dashboard'))

            medicines = request.form.getlist('medicines')
            dosage_instructions = request.form.getlist('dosage_instructions')
            pharmacy_id = request.form['pharmacy']

            # If new medicine is added, add it to the Medicine table
            new_medicine = request.form.get('new_medicine')
            if new_medicine:
                existing_medicine = Medicine.query.filter_by(name=new_medicine).first()
                if not existing_medicine:
                    new_medicine_entry = Medicine(name=new_medicine)
                    db.session.add(new_medicine_entry)
                    db.session.commit()

            # Create the medicine list
            medicine_list = [f"{med} ({instr})" for med, instr in zip(medicines, dosage_instructions)]
            medicine_list_str = ", ".join(medicine_list)

            # Find or create patient
            patient = Patient.query.filter_by(name=patient_name, dob=patient_dob).first()
            if not patient:
                patient = Patient(name=patient_name, dob=patient_dob)
                db.session.add(patient)
                db.session.commit()

            # Create prescription
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=session['user_id'],
                pharmacy_id=pharmacy_id,
                medicine_list=medicine_list_str,
                dosage=""
            )
            db.session.add(prescription)
            db.session.commit()

            flash('Prescription created successfully!', 'success')

        pharmacies = Pharmacy.query.all()
        medicines = Medicine.query.all()  # Get medicines from the database
        return render_template('doctor_dashboard.html', pharmacies=pharmacies, medicines=medicines)

    flash('Unauthorized access!', 'danger')
    return redirect(url_for('login'))

# Route to add a new medicine directly via AJAX
@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    # Get the medicine name from the AJAX request
    medicine_name = request.form['medicine_name']

    # Check if the medicine already exists
    existing_medicine = Medicine.query.filter_by(name=medicine_name).first()
    if existing_medicine:
        return jsonify({'success': False, 'message': 'Medicine already exists!'})

    # Add new medicine to the database
    new_medicine = Medicine(name=medicine_name)
    db.session.add(new_medicine)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Medicine added successfully!'})


@app.route('/pharmacy_dashboard', methods=['GET', 'POST'])
def pharmacy_dashboard():
    if 'role' in session and session['role'] == 'pharmacy':
        prescriptions = None
        if request.method == 'POST':
            patient_name = request.form['patient_name']
            patient_dob = request.form['patient_dob']

            patient = Patient.query.filter_by(name=patient_name, dob=patient_dob).first()
            if patient:
                # Order prescriptions by timestamp in descending order (newest to oldest)
                prescriptions = Prescription.query.filter_by(patient_id=patient.id, pharmacy_id=session['user_id']).order_by(Prescription.timestamp.desc()).all()

        return render_template('pharmacy_dashboard.html', prescriptions=prescriptions)

    flash('Unauthorized access!', 'danger')
    return redirect(url_for('login'))



if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)
