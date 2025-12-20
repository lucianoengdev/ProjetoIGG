# 🛣️ DNIT 008 Analyzer 

## 📋 What is it?
DNIT 008 Analyzer is a web-based engineering tool designed to automate the evaluation of flexible pavement surfaces. It strictly follows the Brazilian standard DNIT 008/2003 - PRO (*Continuous Visual Survey*).

The software processes raw field inventory data to calculate key indicators used in transport engineering for road maintenance planning:
* IGGE (Índice de Gravidade Global Expedito - Expedited Global Gravity Index)
* IES (Índice do Estado da Superfície - Surface Condition Index)

## ⚙️ What does it do?
This application replaces manual calculation spreadsheets with an automated, database-driven process. Its core workflow includes:

1.  Data Ingestion: Accepts Excel (`.xlsx`) spreadsheets containing raw defect inventory (Cracks, Deformations, Potholes/Patches) by station (20m).
2.  Standard Compliance: Automatically converts raw data into Frequency (High, Medium, Low) and Gravity factors based on the DNIT 008 tables.
3.  Segmentation: Aggregates data by kilometer segments.
4.  Reporting: Generates a visual HTML report containing:
    * Bar charts showing the IGGE evolution along the road.
    * A Summary Table with the final Concept (Optimal, Good, Fair, Poor, Very Poor).
    * Detailed Calculation Memory: A "traceability" table showing exactly how the algorithm reached the final numbers (counts, percentages, and factors applied).
5.  Clean Slate Protocol: Automatically cleans old files upon startup to save server storage.

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

1.  Formula Verification (Critical):
    * The core mathematical logic (`app.py`) implements the DNIT 008 standard rules. However, a rigorous manual cross-check of the results against a known control dataset has not yet been performed.
    * Action Required: The user must validate the "Calculation Memory" table against a manually calculated spreadsheet to ensure 100% accuracy before using the outputs for official engineering reports.

2.  Column Mapping:
    * Currently, the system expects specific columns for defects (e.g., G1 to G8). Customizing column mapping requires editing the source code dictionary.

---

### 📝 How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt