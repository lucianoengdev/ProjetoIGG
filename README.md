# 🛣️ DNIT 008 Analyzer 

## 📋 What is it?
DNIT 008 Analyzer is a web-based engineering tool designed to automate the evaluation of flexible pavement surfaces. It strictly follows the Brazilian standard DNIT 008/2003 - PRO (*Continuous Visual Survey*).

The software processes raw field inventory data to calculate key indicators used in transport engineering for road maintenance planning:
* IGGE (Índice de Gravidade Global Expedito - Expedited Global Gravity Index)
* IES (Índice do Estado da Superfície - Surface Condition Index)
* ICPF (Índice de Condição do Pavimento Flexível - Estimated Pavement Condition Index)

## ⚙️ What does it do?
This application replaces manual calculation spreadsheets with an automated, database-driven process. Its core workflow includes:

1.  Data Ingestion: Accepts Excel (`.xlsx`) spreadsheets containing raw defect inventory (Cracks, Deformations, Potholes/Patches) by station (20m).
2.  Hybrid Methodology (DNIT Adaptation):
    * Cracks & Deformations: Calculates the Frequency (%D) using the **Area Ratio method** (Sum of Defect Areas / Total Segment Area) to estimate the percentage of extension affected, converting quantitative field data ($m^2$) into normative percentages.
    * Potholes & Patches: Uses Absolute Counting (occurrences/km) as strictly required by Table 1 of the standard.
3.  Standard Compliance: Automatically converts raw data into Frequency (High, Medium, Low) and applies Weight Factors ($P_t, P_{oap}, P_{pr}$) from DNIT 008 Table 4.
4.  Segmentation: Aggregates data by kilometer segments.
5.  Reporting: Generates a visual HTML report containing:
    * Bar charts showing the IGGE evolution along the road.
    * A Summary Table with the final Concept (Optimal, Good, Fair, Poor, Very Poor).
    * Calculated Indices: Displays IGGE, IES (based on Table 5 Matrix), and estimated ICPF.
    * Detailed Calculation Memory: A "traceability" table showing exactly how the algorithm reached the final numbers.
    * (Planned): Display of Normative Reference Tables (DNIT Tables 1-5) within the report for quick consultation.
6.  Template System: Provides a built-in downloadable Excel template (`modelo_padrao.xlsx`) to ensure correct data entry.
7.  Clean Slate Protocol: Automatically cleans old files upon startup to save server storage.

## 🛠️ Technologies Used
This project relies on a robust Python stack for data analysis and a lightweight web interface:

* Backend: Python 3, Flask.
* Data Processing: Pandas, NumPy (Vectorized calculations for performance).
* Database: SQLite (for storing processed segments and calculation history).
* Frontend: HTML5, Bootstrap 5 (Responsive UI), Chart.js (Data Visualization).
* Format Handling: OpenPyXL (Excel integration).

## 🚀 Project Ambition
The goal of this project is to provide Transport Engineers in Brazil with a **reliable, open, and fast tool** to interpret pavement surveys. By automating the PRO-008 standard, we aim to eliminate human error in extensive road network calculations and provide instant, report-ready visualizations for infrastructure planning.

## 📍 Project Status
Current Version: `2.1.0` (Feature Complete)

The software architecture, database structure, and web interface are fully implemented and functional. The application successfully reads files, processes logic, and renders reports.

## ⚠️ Known Issues & Improvements (Read Carefully)
While the software is functionally stable, the following points require attention before professional deployment:

1.  Methodological Validation (Critical):
    * The system uses an automated technical approximation to convert Area ($m^2$) into Extension (%). While mathematically sound for engineering estimates, the "Calculation Memory" must be cross-checked against a manual control dataset to validate the conversion factors (Assumed: Lane Width = 3.5m, Station = 20m).

2.  Column Mapping:
    * The system uses a hardcoded index mapping (defined in the `INDICES` dictionary). Any changes to the Excel column order require updating the source code.

---

### 📝 How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt