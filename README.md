# HFRC Axial Capacity Prediction Tool

**A Windows desktop application for predicting the axial load capacity of fire-damaged, FRP-confined reinforced concrete columns using Gaussian Process Regression (GPR).**

The HFRC Axial Capacity Prediction Tool provides a user-friendly graphical interface for estimating the axial load capacity (*Pₙ*, kN) of fire-exposed reinforced concrete (RC) columns strengthened with fiber-reinforced polymer (FRP) systems.

The application is designed for structural engineers and researchers, allowing predictions without programming knowledge or a web-based interface.

## Features

- **Single Prediction:** Predict axial load capacity by manually entering eight input parameters.
- **Batch Prediction:** Import multiple specimens from Excel or CSV files.
- **Excel Export:** Save prediction results in Excel format.
- **Input Ranges:** Display the parameter ranges represented in the model's training dataset.
- **Range Warnings:** Identify input values outside the displayed training ranges.
- **Parameter Definitions:** View an embedded schematic illustrating the input parameters.

## Download and Installation

The application is distributed as a standalone Windows executable.

1. Navigate to the **Releases** section of this repository.
2. Download `HFRC_Prediction_Tool.exe` from the latest release.
3. Run the executable to launch the application.

The packaged version includes the trained prediction model and required application resources. No separate Python installation is necessary.

## Prediction Model

The tool implements a Gaussian Process Regression (GPR) model developed using SMOTE-based data augmentation (2×).

The trained model uses eight input variables:

| Input Parameter | Unit |
|---|---|
| `Rb` | Dimensionless |
| `R.A` | As defined in the accompanying study |
| `S.R` | Dimensionless |
| `fy` | MPa |
| `T` | °C |
| `Ag` | mm² |
| `flu` | MPa |
| `fc` | MPa |

**Output:** Predicted axial load capacity, *Pₙ* (kN).

The model is pre-trained and loaded directly by the application. No additional training is performed during prediction.

## Input Ranges and Model Applicability

The GUI displays the minimum and maximum values of each input parameter represented in the fitted training dataset.

These ranges are derived from the training data consisting of 58 original experimental samples and 164 SMOTE-generated synthetic samples.

**Important:** If an input parameter falls outside its displayed range, the GUI provides a warning identifying the affected parameter. **The warning does not prevent prediction; the application continues to calculate and display the predicted axial capacity.**

Predictions outside the training-data ranges should be interpreted with additional caution, as extrapolation may reduce model reliability. Furthermore, predictions within the individual input ranges are not necessarily reliable for every possible combination of parameters.

## Batch Prediction

The application supports batch prediction using Excel or CSV files.

Input files should contain the following columns:

`Rb, R.A, S.R, fy, T, Ag, flu, fc`

Users can import their data, calculate predicted axial capacities for multiple specimens, and export the results to an Excel file.

The prediction output is reported under the column `Pred_Pn_kN`.

## Engineering Disclaimer

This application is intended for research and preliminary engineering assessment purposes only.

Predictions are based on a limited experimental database and should not be used as the sole basis for structural design, post-fire safety assessment, strengthening decisions, or reoccupancy.

Independent verification, appropriate structural analysis, and professional engineering judgment are required when interpreting the predicted results.

## Authors

Developed by Nefise Akdağ, Yavuz S. Karavin, and Uğur Demir.
