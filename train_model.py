import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sqlalchemy import create_engine

DB_URL = "mysql+mysqlconnector://root:vipan001@localhost/hospital_db"
engine = create_engine(DB_URL)

# 1. Train Bed Demand Model
print("1/2 Training Bed Demand Model...")
df = pd.read_sql("SELECT admission_date FROM admissions", con=engine)
df["admission_date"] = pd.to_datetime(df["admission_date"])
daily = (
    df.groupby(df["admission_date"].dt.date)
    .size()
    .reset_index(name="admissions_count")
)
daily["day_of_week"] = pd.to_datetime(daily["admission_date"]).dt.dayofweek
daily["month"] = pd.to_datetime(daily["admission_date"]).dt.month
daily["prev_day_admissions"] = daily["admissions_count"].shift(1)
daily["avg_7_days"] = (
    daily["admissions_count"].rolling(window=7).mean().shift(1)
)
daily = daily.dropna()

X_bed = daily[["day_of_week", "month", "prev_day_admissions", "avg_7_days"]]
y_bed = daily["admissions_count"]

bed_model = RandomForestRegressor(n_estimators=100, random_state=42)
bed_model.fit(X_bed, y_bed)
joblib.dump(bed_model, "models/bed_prediction_model.pkl")

# 2. Train Medicine Depletion Model
print("2/2 Training Medicine Depletion Classifier...")
med_df = pd.read_sql("SELECT * FROM medicines", con=engine)
# Synthetic feature dataset: Predict if stock runs out within 3 days based on current stock vs min threshold
med_df["days_to_depletion"] = (
    med_df["current_stock"] / (med_df["min_threshold"] * 0.1)
).round()
med_df["critical_flag"] = (med_df["days_to_depletion"] <= 3).astype(int)

X_med = med_df[["current_stock", "min_threshold"]]
y_med = med_df["critical_flag"]

med_model = RandomForestClassifier(n_estimators=50, random_state=42)
med_model.fit(X_med, y_med)
joblib.dump(med_model, "models/medicine_depletion_model.pkl")

print(
    "✅ Both AI Models Trained & Saved successfully ('bed_prediction_model.pkl' & 'medicine_depletion_model.pkl')!"
)


