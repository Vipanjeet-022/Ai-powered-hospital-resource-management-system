import os
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

# 1. Page Configuration
st.set_page_config(
    page_title="Hospital AI Resource System", page_icon="🏥", layout="wide"
)

# 2. Database Connection
DB_URL = "mysql+mysqlconnector://root:vipan001@localhost/hospital_db"


@st.cache_resource
def get_db_engine():
    return create_engine(DB_URL)


engine = get_db_engine()

st.title("🏥 AI-Powered Hospital Resource Management System")
st.markdown(
    "Real-time monitoring, resource forecasting, and intelligent hospital alerts."
)
st.divider()

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Overview & KPIs",
        "Bed Utilization",
        "AI Resource Forecasting",
        "Inventory Status",
    ],
)

# --- PAGE 1: OVERVIEW & KPIS ---
if page == "Overview & KPIs":
    st.header("📊 Hospital Overview & Real-Time KPIs")

    col1, col2, col3, col4 = st.columns(4)

    total_beds = pd.read_sql("SELECT COUNT(*) FROM beds", con=engine).iloc[0, 0]
    occupied_beds = pd.read_sql(
        "SELECT SUM(is_occupied) FROM beds", con=engine
    ).iloc[0, 0]
    occupancy_rate = round((occupied_beds / total_beds) * 100, 1)
    total_patients = pd.read_sql("SELECT COUNT(*) FROM patients", con=engine).iloc[
        0, 0
    ]

    col1.metric("Total Beds", total_beds)
    col2.metric("Occupied Beds", occupied_beds)
    col3.metric("Bed Occupancy Rate", f"{occupancy_rate}%")
    col4.metric("Registered Patients", total_patients)

    st.divider()

    # Department Patient Distribution Chart
    st.subheader("Department-wise Bed Allocation")
    dept_query = """
    SELECT d.department_name, COUNT(b.bed_id) as total_beds, SUM(b.is_occupied) as occupied_beds
    FROM beds b
    JOIN departments d ON b.department_id = d.department_id
    GROUP BY d.department_name;
    """
    dept_df = pd.read_sql(dept_query, con=engine)
    fig = px.bar(
        dept_df,
        x="department_name",
        y=["total_beds", "occupied_beds"],
        barmode="group",
        title="Beds Available vs Occupied by Department",
    )
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 2: BED UTILIZATION ---
elif page == "Bed Utilization":
    st.header("🛏️ Bed Utilization & Department Status")

    query = """
    SELECT b.bed_id, d.department_name, b.bed_type, 
           CASE WHEN b.is_occupied = 1 THEN 'Occupied' ELSE 'Available' END as status
    FROM beds b
    JOIN departments d ON b.department_id = d.department_id;
    """
    beds_df = pd.read_sql(query, con=engine)

    # Filter by department
    selected_dept = st.selectbox(
        "Filter by Department", ["All"] + list(beds_df["department_name"].unique())
    )
    if selected_dept != "All":
        beds_df = beds_df[beds_df["department_name"] == selected_dept]

    st.dataframe(beds_df, use_container_width=True)

# --- PAGE 3: AI RESOURCE FORECASTING ---
elif page == "AI Resource Forecasting":
    st.header("🔮 AI Bed Demand Prediction & Risk Alerts")

    if os.path.exists("models/bed_prediction_model.pkl"):
        model = joblib.load("models/bed_prediction_model.pkl")

        st.subheader("Simulate Tomorrow's Admission Conditions")
        col_a, col_b, col_c = st.columns(3)

        day_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        selected_day = col_a.selectbox("Day of Week", list(day_map.keys()))
        month = col_b.slider("Month", 1, 12, 8)
        prev_admissions = col_c.number_input(
            "Admissions Yesterday", value=12, min_value=0
        )

        avg_7_days = st.number_input(
            "Average Admissions Over Last 7 Days", value=10.5, min_value=0.0
        )

        if st.button("Predict Bed Demand"):
            features = [[day_map[selected_day], month, prev_admissions, avg_7_days]]
            prediction = round(model.predict(features)[0])

            st.success(
                f"🎯 **Predicted Bed Demand Tomorrow:** {prediction} admissions"
            )

            # Intelligent Alert Trigger
            if prediction > 12:
                st.error(
                    "🚨 **HIGH RISK ALERT**: Predicted occupancy exceeds normal operational capacity! Consider reallocating staff and freeing up general beds."
                )
            elif prediction > 8:
                st.warning(
                    "⚠️ **MODERATE RISK**: Expected workload is high. Monitor ICU and Emergency bed flow closely."
                )
            else:
                st.info(
                    "✅ **LOW RISK**: Resources are predicted to remain within normal limits."
                )
    else:
        st.error(
            "Model file 'bed_prediction_model.pkl' not found. Run train_model.py first!"
        )

# --- PAGE 4: INVENTORY STATUS ---
elif page == "Inventory Status":
    st.header("💊 Pharmacy & Medicine Inventory")

    med_df = pd.read_sql("SELECT * FROM medicines", con=engine)

    # Highlight Low Stock
    med_df["Stock Status"] = med_df.apply(
        lambda r: "CRITICAL"
        if r["current_stock"] < r["min_threshold"]
        else "NORMAL",
        axis=1,
    )

    st.dataframe(med_df, use_container_width=True)

    low_stock = med_df[med_df["Stock Status"] == "CRITICAL"]
    if not low_stock.empty:
        for _, row in low_stock.iterrows():
            st.warning(
                f"⚠️ **Low Stock Warning**: {row['medicine_name']} stock ({row['current_stock']}) is below minimum threshold ({row['min_threshold']})!"
            )