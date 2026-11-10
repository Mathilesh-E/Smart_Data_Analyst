"""
Creates the 4 benchmark datasets in sample_data/:
1. retail_sales.csv
2. student_performance.csv
3. healthcare_sample.csv
4. flight_delays.csv
"""
import os
import pandas as pd
import numpy as np

def generate_benchmarks():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
    os.makedirs(out_dir, exist_ok=True)
    np.random.seed(42)

    # 1. Retail Sales
    n = 350
    dates = pd.date_range("2024-01-01", periods=120, freq="D")
    retail = pd.DataFrame({
        "TransactionID": [f"TXN-{10000+i}" for i in range(n)],
        "Date": np.random.choice(dates, n),
        "Region": np.random.choice(["North", "South", "East", "West"], n),
        "ProductCategory": np.random.choice(["Electronics", "Apparel", "Home & Kitchen", "Books"], n),
        "UnitsSold": np.random.randint(1, 15, n),
        "UnitPrice": np.random.uniform(20.0, 350.0, n).round(2),
        "DiscountRate": np.random.choice([0.0, 0.05, 0.10, 0.20], n),
        "CustomerRating": np.random.choice([1, 2, 3, 4, 5, np.nan], n, p=[0.05, 0.1, 0.25, 0.35, 0.2, 0.05]),
        "StoreType": ["Flagship Retail"] * n # constant column
    })
    retail["Revenue"] = (retail["UnitsSold"] * retail["UnitPrice"] * (1 - retail["DiscountRate"])).round(2)
    retail = pd.concat([retail, retail.iloc[:8]], ignore_index=True) # duplicates
    retail.to_csv(os.path.join(out_dir, "retail_sales.csv"), index=False)

    # 2. Student Performance
    n = 280
    student = pd.DataFrame({
        "StudentID": [f"STU-{5000+i}" for i in range(n)],
        "Major": np.random.choice(["Computer Science", "Data Analytics", "Finance", "Biology"], n),
        "Gender": np.random.choice(["Female", "Male"], n),
        "StudyHoursPerWeek": np.random.normal(20, 6, n).clip(4, 50).round(1),
        "AttendancePct": np.random.uniform(65, 100, n).round(1),
        "PreviousFailures": np.random.choice([0, 0, 0, 1, 2], n),
        "MidtermExam": np.random.normal(74, 11, n).clip(35, 100).round(1),
        "FinalExam": np.random.normal(76, 13, n).clip(40, 100).round(1),
        "Passed": np.random.choice(["Yes", "No"], n, p=[0.84, 0.16])
    })
    # Inject missing
    mask = np.random.rand(*student.shape) < 0.03
    student = student.mask(mask)
    student.to_csv(os.path.join(out_dir, "student_performance.csv"), index=False)

    # 3. Healthcare Sample
    n = 300
    health = pd.DataFrame({
        "PatientID": range(1001, 1001 + n),
        "Age": np.random.randint(25, 82, n),
        "Gender": np.random.choice(["Male", "Female"], n),
        "RestingBP": np.random.normal(128, 16, n).clip(90, 195).round(0),
        "Cholesterol": np.random.normal(235, 42, n).clip(120, 420).round(0),
        "FastingBloodSugar": np.random.choice([0, 1], n, p=[0.85, 0.15]),
        "MaxHeartRate": np.random.normal(152, 22, n).clip(75, 202).round(0),
        "ExerciseAngina": np.random.choice(["Yes", "No"], n, p=[0.35, 0.65]),
        "HeartDisease": np.random.choice([0, 1], n, p=[0.52, 0.48])
    })
    health.to_csv(os.path.join(out_dir, "healthcare_sample.csv"), index=False)

    # 4. Flight Delays
    n = 320
    flight = pd.DataFrame({
        "FlightNumber": [f"FL-{200+i}" for i in range(n)],
        "Airline": np.random.choice(["Delta", "United", "American", "Southwest"], n),
        "Origin": np.random.choice(["JFK", "LAX", "ORD", "ATL", "DFW"], n),
        "Destination": np.random.choice(["SFO", "MIA", "SEA", "BOS", "DEN"], n),
        "DistanceMiles": np.random.randint(250, 2600, n),
        "DepartureDelayMin": np.random.exponential(18, n).round(1),
        "ArrivalDelayMin": np.random.exponential(20, n).round(1),
        "Cancelled": np.random.choice([0, 1], n, p=[0.97, 0.03])
    })
    flight.to_csv(os.path.join(out_dir, "flight_delays.csv"), index=False)

    print(f"Generated 4 benchmark datasets in {out_dir}")

if __name__ == "__main__":
    generate_benchmarks()

