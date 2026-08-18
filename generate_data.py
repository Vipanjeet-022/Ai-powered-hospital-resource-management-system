import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine

fake = Faker()


DB_URL = "mysql+mysqlconnector://root:vipan001@localhost/hospital_db"
engine = create_engine(DB_URL)

print("1/5 Populating Departments...")
depts = ["ICU", "General Ward", "Emergency", "Pediatrics", "Cardiology"]
dept_df = pd.DataFrame({"department_name": depts})
dept_df.to_sql("departments", con=engine, if_exists="append", index=False)

# Retrieve Department IDs
dept_ids = pd.read_sql("SELECT department_id, department_name FROM departments", con=engine)

print("2/5 Populating Beds...")
beds_data = []
for _, row in dept_ids.iterrows():
    num_beds = 15 if row["department_name"] == "ICU" else 35
    for _ in range(num_beds):
        beds_data.append({
            "department_id": row["department_id"],
            "bed_type": row["department_name"],
            "is_occupied": random.choice([0, 1])
        })
beds_df = pd.DataFrame(beds_data)
beds_df.to_sql("beds", con=engine, if_exists="append", index=False)

# Retrieve Bed IDs
bed_ids = pd.read_sql("SELECT bed_id FROM beds", con=engine)["bed_id"].tolist()

print("3/5 Populating Patients...")
patients_data = []
for _ in range(300):
    patients_data.append({
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "age": random.randint(1, 85),
        "gender": random.choice(["Male", "Female"])
    })
patients_df = pd.DataFrame(patients_data)
patients_df.to_sql("patients", con=engine, if_exists="append", index=False)

# Retrieve Patient IDs
patient_ids = pd.read_sql("SELECT patient_id FROM patients", con=engine)["patient_id"].tolist()

print("4/5 Populating Admissions (90 Days History)...")
admissions_data = []
start_date = datetime.now() - timedelta(days=90)

for _ in range(800):
    adm_date = start_date + timedelta(days=random.randint(0, 89), hours=random.randint(0, 23))
    stay_days = random.randint(1, 12)
    dis_date = adm_date + timedelta(days=stay_days)
    
    is_discharged = dis_date < datetime.now()
    
    admissions_data.append({
        "patient_id": random.choice(patient_ids),
        "bed_id": random.choice(bed_ids),
        "admission_date": adm_date.strftime("%Y-%m-%d %H:%M:%S"),
        "discharge_date": dis_date.strftime("%Y-%m-%d %H:%M:%S") if is_discharged else None,
        "status": "Discharged" if is_discharged else "Admitted"
    })

admissions_df = pd.DataFrame(admissions_data)
admissions_df.to_sql("admissions", con=engine, if_exists="append", index=False)

print("5/5 Populating Medicines...")
medicines_data = [
    {"medicine_name": "Paracetamol", "current_stock": 150, "min_threshold": 200},
    {"medicine_name": "Amoxicillin", "current_stock": 500, "min_threshold": 100},
    {"medicine_name": "Ibuprofen", "current_stock": 80, "min_threshold": 150},
    {"medicine_name": "Insulin", "current_stock": 40, "min_threshold": 50}
]
meds_df = pd.DataFrame(medicines_data)
meds_df.to_sql("medicines", con=engine, if_exists="append", index=False)

print("✅ Data generation complete and database successfully populated!")