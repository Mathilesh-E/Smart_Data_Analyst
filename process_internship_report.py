import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
import os

doc_path = r'C:\Users\Mathi\OneDrive\Documents\Smart_Data_Analyst_Enhanced\Smart_Data_Analyst\Khatheeja_Sana_S_Internship_Report_Smart_Data_Analyst.docx'
screenshots_dir = Path(r'C:\Users\Mathi\OneDrive\Documents\Smart_Data_Analyst_Enhanced\report_screenshots')
output_path = r'C:\Users\Mathi\OneDrive\Documents\Smart_Data_Analyst_Enhanced\Smart_Data_Analyst\Khatheeja_Sana_S_Internship_Report_Smart_Data_Analyst.docx'
output_final_copy = r'C:\Users\Mathi\OneDrive\Documents\Smart_Data_Analyst_Enhanced\Smart_Data_Analyst\Khatheeja_Sana_S_Internship_Report_FINAL.docx'

doc = docx.Document(doc_path)
print(f"Loaded document: {len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables")

# ==============================================================================
# 1. UPDATE DATA TABLES BEFORE TOUCHING PLACEHOLDERS
# ==============================================================================

# --- Table 34: Sample Datasets ---
print("Updating Table 34 (Sample Datasets)...")
tbl34 = doc.tables[34]
# Row 1: Retail
tbl34.rows[1].cells[2].text = "358 × 10"
tbl34.rows[1].cells[3].text = "TransactionID, Date, Region, ProductCategory, UnitsSold, UnitPrice, DiscountRate, CustomerRating, StoreType, Revenue"
# Row 2: Student
tbl34.rows[2].cells[2].text = "280 × 9"
tbl34.rows[2].cells[3].text = "StudentID, Major, Gender, StudyHoursPerWeek, AttendancePct, PreviousFailures, MidtermExam, FinalExam, Passed"
# Row 3: Healthcare
tbl34.rows[3].cells[2].text = "300 × 9"
tbl34.rows[3].cells[3].text = "PatientID, Age, Gender, RestingBP, Cholesterol, FastingBloodSugar, MaxHeartRate, ExerciseAngina, HeartDisease"
# Row 4: Flight Delays
tbl34.rows[4].cells[2].text = "320 × 8"
tbl34.rows[4].cells[3].text = "FlightNumber, Airline, Origin, Destination, DistanceMiles, DepartureDelayMin, ArrivalDelayMin, Cancelled"

# --- Table 39: Retail Sales Data Dictionary ---
print("Updating Table 39 (Retail Sales Data Dictionary)...")
tbl39 = doc.tables[39]
new_retail_data = [
    ["TransactionID", "identifier", "350", "—", "—", "—", "—"],
    ["Date", "datetime", "114", "2024-04-12", "2024-11-29", "—", "—"],
    ["Region", "categorical", "4", "—", "—", "—", "—"],
    ["ProductCategory", "categorical", "4", "—", "—", "—", "—"],
    ["UnitsSold", "numeric", "14", "1", "14", "7.37", "7.00"],
    ["UnitPrice", "numeric", "358", "20.08", "349.79", "189.98", "194.45"],
    ["DiscountRate", "numeric", "21", "0.00", "0.20", "0.09", "0.08"],
    ["CustomerRating", "numeric", "5", "1.0", "5.0", "3.64", "4.00"],
    ["StoreType", "categorical", "1", "—", "—", "—", "—"],
    ["Revenue", "numeric", "358", "30.79", "4,238.01", "1,257.68", "1,029.71"]
]
# We have 8 rows currently in Table 39 (header + 7 rows). We need header + 10 rows.
# Update the 7 existing data rows
for i in range(7):
    row_cells = tbl39.rows[i + 1].cells
    for c_idx, val in enumerate(new_retail_data[i]):
        row_cells[c_idx].text = val

# Add remaining 3 rows
for i in range(7, 10):
    new_row = tbl39.add_row()
    for c_idx, val in enumerate(new_retail_data[i]):
        new_row.cells[c_idx].text = val

# --- Table 43: Average Revenue by Category and Region ---
print("Updating Table 43 (Average Revenue by Category and Region)...")
tbl43 = doc.tables[43]
cat_reg_data = [
    ["Apparel", "1,416.89", "South", "1,328.70"],
    ["Home & Kitchen", "1,303.49", "North", "1,298.09"],
    ["Electronics", "1,181.93", "West", "1,213.23"],
    ["Books", "1,168.89", "East", "1,187.68"],
]
for i, vals in enumerate(cat_reg_data):
    for c_idx, val in enumerate(vals):
        tbl43.rows[i + 1].cells[c_idx].text = val

# --- Table 49: Statistical Lab Summary ---
print("Updating Table 49 (Statistical Lab Summary)...")
tbl49 = doc.tables[49]
# Row 1: Pearson on Student Performance
tbl49.rows[1].cells[0].text = "Pearson"
tbl49.rows[1].cells[1].text = "StudyHoursPerWeek, AttendancePct"
tbl49.rows[1].cells[2].text = "269"
tbl49.rows[1].cells[3].text = "r = −0.023"
tbl49.rows[1].cells[4].text = "0.705"
tbl49.rows[1].cells[5].text = "r = −0.023"

# --- Table 53: Segments Profiles ---
print("Updating Table 53 (Segments Profiles)...")
tbl53 = doc.tables[53]
seg_data = [
    ["0", "78", "20.24", "85.43", "82.11"],
    ["1", "78", "19.92", "90.42", "71.70"],
    ["2", "78", "20.08", "72.29", "77.65"],
]
for i, vals in enumerate(seg_data):
    for c_idx, val in enumerate(vals):
        tbl53.rows[i + 1].cells[c_idx].text = val

# --- Table 62: Summary for Student, Healthcare, Flights ---
print("Updating Table 62 (Multi-dataset Data Dictionary)...")
tbl62 = doc.tables[62]
multi_data = [
    ["Student", "StudyHoursPerWeek", "4.0", "33.2", "19.91", "20.20", "5.54"],
    ["Student", "AttendancePct", "65.1", "100.0", "82.56", "82.80", "10.14"],
    ["Student", "MidtermExam", "42.1", "100.0", "74.36", "74.70", "11.29"],
    ["Student", "FinalExam", "40.0", "100.0", "77.22", "77.20", "13.73"],
    ["Healthcare", "Age", "25", "81", "55.27", "56.5", "16.31"],
    ["Healthcare", "RestingBP", "90.0", "175.0", "127.14", "127.0", "15.43"],
    ["Healthcare", "Cholesterol", "120.0", "354.0", "233.71", "233.0", "41.54"],
    ["Healthcare", "MaxHeartRate", "92.0", "202.0", "153.00", "152.0", "21.21"],
    ["Flights", "DistanceMiles", "261", "2,586", "1,449.94", "1,453.5", "653.60"],
    ["Flights", "DepartureDelayMin", "0.0", "101.5", "18.58", "12.80", "18.03"],
    ["Flights", "ArrivalDelayMin", "0.0", "99.9", "20.56", "14.75", "18.76"],
]
for i, vals in enumerate(multi_data):
    for c_idx, val in enumerate(vals):
        tbl62.rows[i + 1].cells[c_idx].text = val


# ==============================================================================
# 2. UPDATE BODY PARAGRAPHS TEXT
# ==============================================================================
print("Updating body paragraphs...")

for p in doc.paragraphs:
    # Overview screen description
    if "360 rows and 7 columns" in p.text:
        p.text = p.text.replace("360 rows and 7 columns", "358 rows and 10 columns")
        p.text = p.text.replace(
            "that revenue is skewed (skewness 1.07), with the advice to inspect its histogram and robust statistics.",
            "that numerical distributions (Revenue, UnitsSold, UnitPrice) display distinct spread, with recommendations for visual exploration and robust statistics."
        )
    if "The dashboard selects revenue as the measure" in p.text:
        p.text = (
            "The dashboard automatically configures Revenue as the measure, Region and ProductCategory as "
            "groupings and Date as the date axis, assembling grouped bar charts (Revenue by Region split by ProductCategory), "
            "category breakdowns, and interactive slicers. Slicers allow dynamic filtering across the 358 orders."
        )
    if "Isolation Forest review with 3 % expected anomalies" in p.text:
        p.text = (
            "For the retail sample, the Isolation Forest review with 3 % expected anomalies on UnitsSold, UnitPrice "
            "and Revenue flagged candidate records from the 358 transactions. As the screen warns, these are candidates "
            "for review: they represent legitimate high-value transactions, not data entry errors."
        )
    if "student_id is recognised as an identifier, participation is categorical" in p.text:
        p.text = (
            "In the student performance sample, StudentID is recognised as an identifier, Major has 4 categories, "
            "Gender has 2 categories, Passed is binary, and the numeric measures include StudyHoursPerWeek, AttendancePct, "
            "PreviousFailures, MidtermExam, and FinalExam. In the healthcare sample, PatientID is an identifier, with numeric "
            "measures including Age, RestingBP, Cholesterol, FastingBloodSugar, and MaxHeartRate. In the flight delays "
            "sample, FlightNumber is an identifier, Airline covers major carriers, and key metrics include DistanceMiles, "
            "DepartureDelayMin, and ArrivalDelayMin. Table 41 lists the numeric summaries that the data dictionary shows for these three samples."
        )
    if 'test": "pearson", "x": "study_hours"' in p.text:
        p.text = p.text.replace('"x": "study_hours", "y": "final_score"', '"x": "StudyHoursPerWeek", "y": "AttendancePct"')
    if '"features": ["study_hours", "attendance_pct", "sleep_hours", "participation"]' in p.text:
        p.text = p.text.replace(
            '"features": ["study_hours", "attendance_pct", "sleep_hours", "participation"]',
            '"features": ["StudyHoursPerWeek", "AttendancePct", "PreviousFailures", "MidtermExam"]'
        )
    if "{ \"records_before_filters\": 360" in p.text:
        p.text = p.text.replace('360', '358')


# ==============================================================================
# 3. ADD GITHUB & RENDER DEPLOYMENT SECTION (Section 8.5)
# ==============================================================================
print("Adding Section 8.5 (Repository and Live Cloud Deployment)...")

# Find Chapter 8 conclusion and Chapter 9 start
insert_idx = None
for i, p in enumerate(doc.paragraphs):
    if p.text.strip() == "CHAPTER 9":
        insert_idx = i
        break

if insert_idx is not None:
    # Insert new paragraph before Chapter 9
    p_before = doc.paragraphs[insert_idx]
    
    p_h = doc.add_paragraph()
    run_h = p_h.add_run("8.5 Source Code Repository and Live Cloud Deployment")
    run_h.font.bold = True
    run_h.font.size = Pt(13)
    p_before._element.addprevious(p_h._element)
    
    p_b1 = doc.add_paragraph()
    p_b1.text = (
        "The complete source code repository, documentation, test suites, and sample datasets for Smart Data Analyst "
        "are publicly available on GitHub at:\n"
        "https://github.com/Mathilesh-E/Smart_Data_Analyst"
    )
    p_before._element.addprevious(p_b1._element)
    
    p_b2 = doc.add_paragraph()
    p_b2.text = (
        "In addition, the entire interactive application has been deployed live to the cloud on Render and is accessible at:\n"
        "https://smart-data-analyst-0d1w.onrender.com/\n\n"
        "The deployed application operates the full production React single-page frontend paired with the FastAPI analytics backend. "
        "Users can upload custom CSV and Excel spreadsheets or interactively explore preloaded domain datasets (Retail Sales, "
        "Student Performance, Healthcare Records, Flight Operations), run statistical hypothesis testing, train baseline machine learning "
        "models, perform time-series analysis, and export comprehensive audit reports directly in any modern browser."
    )
    p_before._element.addprevious(p_b2._element)


# ==============================================================================
# 4. REPLACE PLACEHOLDER TABLES WITH ACTUAL SCREENSHOTS
# ==============================================================================
print("Replacing placeholder tables with high-resolution browser screenshots...")

placeholder_map = {
    17: 'fig07_app_shell_welcome.png',
    33: 'fig11_pytest_terminal.png',
    35: 'fig12_welcome_screen.png',
    36: 'fig13_error_upload.png',
    37: 'fig14_overview_retail.png',
    38: 'fig15_overview_slicer.png',
    40: 'fig16_data_explorer.png',
    41: 'fig17_data_quality.png',
    42: 'fig18_cleaning_studio.png',
    44: 'fig19_chart_studio.png',
    46: 'fig20_analysis_workbench.png',
    48: 'fig21_insights.png',
    50: 'fig22_statistical_lab.png',
    52: 'fig23_ml_lab.png',
    54: 'fig24_segments_anomalies.png',
    56: 'fig25_time_series.png',
    57: 'fig26_reports_exports.png',
    58: 'fig27_pdf_report_p1.png',
    60: 'fig28_dark_theme.png',
    61: 'fig29_light_theme.png',
    63: 'fig30_student_overview.png',
    64: 'fig31_healthcare_overview.png',
    65: 'fig32_flight_delays_overview.png',
}

# Process in REVERSE order so indices of previous tables remain untouched
for t_idx in sorted(placeholder_map.keys(), reverse=True):
    img_name = placeholder_map[t_idx]
    img_path = screenshots_dir / img_name
    if not img_path.exists():
        print(f"ERROR: Image not found: {img_path}")
        continue
    
    tbl = doc.tables[t_idx]
    tbl_elem = tbl._element
    parent = tbl_elem.getparent()
    
    # Create image paragraph
    new_p = doc.add_paragraph()
    new_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    new_p.paragraph_format.space_before = Pt(6)
    new_p.paragraph_format.space_after = Pt(6)
    run = new_p.add_run()
    
    # Set appropriate width: 4.8 inches for portrait PDF report, 6.0 inches for browser screenshots
    img_width = Inches(4.8) if img_name == 'fig27_pdf_report_p1.png' else Inches(6.0)
    run.add_picture(str(img_path), width=img_width)
    
    # Insert new paragraph before the table and remove the placeholder table
    tbl_elem.addprevious(new_p._element)
    parent.remove(tbl_elem)
    print(f"  Replaced Table {t_idx:2d} with {img_name} (width={img_width.inches} in)")

# Save both in-place and as FINAL
print(f"Saving to {output_path}...")
doc.save(output_path)

print(f"Saving copy to {output_final_copy}...")
doc.save(output_final_copy)

print("SUCCESS: Report processing complete!")
