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
    * Cracks & Deformations: Calculates the Frequency (%D) using the Area Ratio method. It sums the exact defect area ($m^2$) entered in the spreadsheet and divides it by the Total Segment Area (Assumed 7.0m width × 1000m), converting field measurements into the normative percentage.
    * Potholes & Patches: Offers a User Selection feature at upload. The user can choose between Incidence Mode (Binary: considers if the defect exists or not per station) or Real Counting Mode (Sums the exact quantity of potholes), adapting to different survey styles.3.  Standard Compliance: Automatically converts raw data into Frequency (High, Medium, Low) and applies Weight Factors ($P_t, P_{oap}, P_{pr}$) from DNIT 008 Table 4.
4.  Segmentation: Aggregates data by kilometer segments.
5.  Reporting: Generates a visual HTML report containing:
    * Interactive Multi-Axis Chart: Plots IGGE (Left Axis) vs IES/ICPF (Right Axis) simultaneously for correlation analysis.
    * Official DNIT Export (.xlsx): Generates the Anexo C (Calculation Memory) strictly following the visual layout and mathematical rules of PRO-008 (Weight × Frequency), ready for official filing.
    * Calculated Indices: Displays IGGE, IES (based on Table 5 Matrix), and estimated ICPF.
    * Normative Annexes: Embeds the official DNIT 008 Tables (1 to 5) directly in the report footer for immediate technical consultation.
7.  Clean Slate Protocol: Automatically cleans old files upon startup to save server storage.

## 🛠️ Technologies Used
This project relies on a robust Python stack for data analysis and a lightweight web interface:

* Backend: Python 3, Flask.
* Data Processing: Pandas, NumPy (Vectorized calculations for performance).
* Database: SQLite (for storing processed segments and calculation history).
* Frontend: HTML5, Bootstrap 5 (Responsive UI), Chart.js (Data Visualization).
* Format Handling: OpenPyXL (Excel integration).

## 🚀 Project Ambition
The goal of this project is to provide Transport Engineers in Brazil with a reliable, open, and fast tool to interpret pavement surveys. By automating the PRO-008 standard, we aim to eliminate human error in extensive road network calculations and provide instant, report-ready visualizations for infrastructure planning.

## 📍 Project Status
Current Version: `2.3.0` (Enhanced Reporting & Flex Input)

The software architecture is fully functional, featuring dynamic chart plotting, flexible data processing options (Incidence/Counting), and embedded normative references.

## ⚠️ Known Issues & Improvements (Read Carefully)
While the software is functionally stable, the following points require attention before professional deployment:

1.  Methodological Validation (Critical):
    * The system uses an automated technical approximation to convert Area ($m^2$) into Extension (%). The current algorithm assumes a Double Lane Width (7.0m) for the segment area calculation. Users surveying single lanes (3.5m) should be aware that the percentage results might appear halved unless the code constant is adjusted.
2.  Column Mapping:
    * The system uses a hardcoded index mapping (defined in the `INDICES` dictionary). Any changes to the Excel column order require updating the source code.
3.  * Official DNIT Export (.xlsx): 
    * Generates the Anexos B and D from regulation

---

### 📝 How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt