import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd

# --- Database Schema ---
def create_tables(conn):
    cursor = conn.cursor()
    
    # Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            date_of_birth DATE,
            gender TEXT,
            city TEXT,
            registered_date DATE
        )
    ''')
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT,
            department TEXT,
            phone TEXT
        )
    ''')
    
    # Appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            appointment_date DATETIME,
            status TEXT,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    
    # Treatments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            treatment_name TEXT,
            cost REAL,
            duration_minutes INTEGER,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')
    
    # Invoices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            invoice_date DATE,
            total_amount REAL,
            paid_amount REAL,
            status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    ''')
    
    conn.commit()
    print("✓ Database tables created successfully")

# --- Dummy Data Insertion ---
def insert_dummy_data(conn):
    cursor = conn.cursor()
    
    # 1. Insert Doctors (15 doctors across 5 specializations)
    doctors = [
        # Dermatology
        ("Dr. Sarah Johnson", "Dermatology", "Skin Care", "555-0101"),
        ("Dr. Michael Lee", "Dermatology", "Skin Care", "555-0102"),
        ("Dr. Emily Brown", "Dermatology", "Skin Care", "555-0103"),
        # Cardiology
        ("Dr. James Wilson", "Cardiology", "Heart Center", "555-0201"),
        ("Dr. Maria Garcia", "Cardiology", "Heart Center", "555-0202"),
        ("Dr. Robert Taylor", "Cardiology", "Heart Center", "555-0203"),
        # Orthopedics
        ("Dr. Jennifer Martinez", "Orthopedics", "Bone & Joint", "555-0301"),
        ("Dr. David Anderson", "Orthopedics", "Bone & Joint", "555-0302"),
        ("Dr. Lisa Thomas", "Orthopedics", "Bone & Joint", "555-0303"),
        # General
        ("Dr. Richard Jackson", "General", "Primary Care", "555-0401"),
        ("Dr. Patricia White", "General", "Primary Care", "555-0402"),
        ("Dr. Charles Harris", "General", "Primary Care", "555-0403"),
        # Pediatrics
        ("Dr. Susan Martin", "Pediatrics", "Children's Health", "555-0501"),
        ("Dr. Paul Thompson", "Pediatrics", "Children's Health", "555-0502"),
        ("Dr. Karen Robinson", "Pediatrics", "Children's Health", "555-0503"),
    ]
    
    for doctor in doctors:
        cursor.execute('INSERT INTO doctors (name, specialization, department, phone) VALUES (?, ?, ?, ?)', doctor)
    
    doctor_ids = list(range(1, 16))
    print(f"✓ Inserted {len(doctors)} doctors")
    
    # 2. Insert Patients (200 patients)
    first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Lisa", "James", "Maria",
                   "William", "Jennifer", "Richard", "Patricia", "Charles", "Susan", "Thomas", "Karen", "Daniel", "Linda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Wilson", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Robinson"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]
    genders = ["M", "F"]
    
    patients = []
    for i in range(200):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}@example.com" if random.random() > 0.1 else None
        phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}" if random.random() > 0.05 else None
        date_of_birth = f"{random.randint(1950, 2010)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        gender = random.choice(genders)
        city = random.choice(cities)
        registered_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        patients.append((first_name, last_name, email, phone, date_of_birth, gender, city, registered_date))
    
    cursor.executemany('''
        INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', patients)
    
    patient_ids = list(range(1, 201))
    print(f"✓ Inserted 200 patients")
    
    # 3. Insert Appointments (500 appointments over past 12 months)
    statuses = ["Scheduled", "Completed", "Cancelled", "No-Show"]
    # Weighted distribution: more Completed, some Cancelled/No-Show
    status_weights = [0.3, 0.5, 0.1, 0.1]  # Scheduled=30%, Completed=50%, Cancelled=10%, No-Show=10%
    
    appointments = []
    appointment_ids = []
    
    for i in range(500):
        patient_id = random.choice(patient_ids)
        doctor_id = random.choice(doctor_ids)
        # Spread appointments over last 12 months
        days_ago = random.randint(0, 365)
        appointment_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        status = random.choices(statuses, weights=status_weights)[0]
        notes = f"Notes for appointment {i+1}" if random.random() > 0.7 else None
        appointments.append((patient_id, doctor_id, appointment_date, status, notes))
    
    cursor.executemany('''
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', appointments)
    
    # Get all appointment IDs after insertion
    cursor.execute('SELECT id FROM appointments')
    appointment_ids = [row[0] for row in cursor.fetchall()]
    print(f"✓ Inserted 500 appointments")
    
    # 4. Insert Treatments (350 treatments linked to completed appointments)
    treatment_names = ["Check-up", "X-Ray", "Blood Test", "MRI", "CT Scan", "Physical Therapy", 
                       "Surgery", "Vaccination", "ECG", "Ultrasound", "Biopsy", "Endoscopy"]
    
    treatments = []
    # Only link to completed appointments
    cursor.execute('SELECT id FROM appointments WHERE status = "Completed"')
    completed_appointment_ids = [row[0] for row in cursor.fetchall()]
    
    for i in range(min(350, len(completed_appointment_ids))):
        appointment_id = random.choice(completed_appointment_ids)
        treatment_name = random.choice(treatment_names)
        cost = round(random.uniform(50, 5000), 2)
        duration_minutes = random.choice([15, 30, 45, 60, 90, 120])
        treatments.append((appointment_id, treatment_name, cost, duration_minutes))
    
    cursor.executemany('''
        INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes)
        VALUES (?, ?, ?, ?)
    ''', treatments)
    print(f"✓ Inserted {len(treatments)} treatments")
    
    # 5. Insert Invoices (300 invoices with mix of statuses)
    invoice_statuses = ["Paid", "Pending", "Overdue"]
    invoice_weights = [0.5, 0.3, 0.2]  # 50% Paid, 30% Pending, 20% Overdue
    
    invoices = []
    # Use a subset of patients for invoices
    invoice_patient_ids = random.sample(patient_ids, min(250, len(patient_ids)))
    
    for i in range(300):
        patient_id = random.choice(invoice_patient_ids)
        invoice_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        total_amount = round(random.uniform(100, 10000), 2)
        status = random.choices(invoice_statuses, weights=invoice_weights)[0]
        paid_amount = round(total_amount if status == "Paid" else total_amount * random.uniform(0, 0.5), 2) if status != "Overdue" else 0
        invoices.append((patient_id, invoice_date, total_amount, paid_amount, status))
    
    cursor.executemany('''
        INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status)
        VALUES (?, ?, ?, ?, ?)
    ''', invoices)
    print(f"✓ Inserted 300 invoices")
    
    conn.commit()
    print("\n" + "="*50)
    print("DATABASE SETUP COMPLETE")
    print("="*50)
    print(f"Patients: {len(patients)}")
    print(f"Doctors: {len(doctors)}")
    print(f"Appointments: {len(appointments)}")
    print(f"Treatments: {len(treatments)}")
    print(f"Invoices: {len(invoices)}")
    print("="*50)

# --- Main execution ---
if __name__ == "__main__":
    conn = sqlite3.connect("clinic.db")
    create_tables(conn)
    insert_dummy_data(conn)
    conn.close()
    print("\n✓ Database file 'clinic.db' created successfully!")