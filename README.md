# HFRC Prediction Desktop Application

This repository provides a **standalone desktop graphical user interface (GUI)** developed for predicting the axial load capacity (**Pₙ**) of **fire-damaged reinforced concrete (RC) columns strengthened with fiber-reinforced polymer (FRP)** systems using machine learning models.

The application is specifically designed for **structural engineers and researchers** who want to perform fast and reliable predictions **without writing any code or using a web-based interface**.

---

## Application Overview

The HFRC Prediction Desktop Application enables users to:

- Perform **single predictions** by manually entering input parameters
- Perform **batch predictions** using Excel or CSV files
- Select between different trained **machine learning models**
- View results directly within the application
- Export batch prediction results to Excel format

The software runs as a **native Windows desktop application** and does not require Python, a browser, or an internet connection.

---

## Input Parameters

The prediction models require the following input parameters:

| Symbol | Description |
|------|-------------|
| \( R_b \) | Corner radius ratio |
| \( H \) | Specimen height (mm) |
| \( R.R \) | Longitudinal reinforcement ratio |
| \( S.R \) | Transverse reinforcement ratio |
| \( f_y \) | Yield strength of reinforcing steel (MPa) |
| \( T \) | Fire exposure temperature (°C) |
| \( A_g \) | Gross cross-sectional area (mm²) |
| \( E_f \) | Elastic modulus of FRP (GPa) |
| \( t_f \) | Total FRP thickness (mm) |
| \( \varepsilon_{f\varepsilon} \) | Effective FRP strain |
| \( f_c \) | Concrete compressive strength (MPa) |

### Output

- **\( P_n \)**: Predicted axial load capacity

---

## How to Use the Application

### 1. Download and Run

1. Download the compressed application package (`HFRC_Desktop.zip`) from the **Releases** section.
2. Extract the contents of the zip file to any folder.
3. Run `HFRC_Desktop.exe`.

> ⚠️ Important:  
> Do not delete or move the `_internal` or `models` folders. These files are required for the application to function properly.

---

### 2. Single Prediction (Manual Input)

1. Select a machine learning model from the **Model** dropdown menu.
2. Enter the required input parameters.
3. Click the **Predict** button.
4. The predicted value of **Pₙ** will be displayed immediately.

---

### 3. Batch Prediction (Excel / CSV)

1. Click **Load Excel/CSV** and select a data file.
2. Click **Run batch prediction**.
3. Review the prediction results displayed in the table.
4. Click **Export results to Excel** to save the results.

The application automatically recognizes common variations in column names (e.g., `fy`, `f_y`, `yield_strength`) and converts them internally.

---

## Machine Learning Models

The application currently supports the following models:

- **XGBoost**
- **CatBoost**

The models were trained on a consistent database of **fire-damaged FRP-confined RC columns**, including both experimental data and augmented samples.

---

## System Requirements

- Operating System: **Windows 10 / Windows 11 (64-bit)**
- No Python installation required
- No internet connection required

---


