# HFRC Axial Capacity Prediction Desktop Application

This repository provides a standalone desktop graphical user interface (GUI) developed for predicting the axial load capacity (**Pₙ**) of fire-damaged reinforced concrete (RC) columns strengthened with fiber-reinforced polymer (FRP) systems using a Gaussian Process Regression (GPR) model.

The application is designed for structural engineers and researchers who want to perform fast predictions without writing code or using a web-based interface.

---

## Application Overview

The HFRC Axial Capacity Prediction Tool enables users to:

- Perform single predictions by manually entering input parameters
- Perform batch predictions using Excel or CSV files
- View the applicable model input range directly in the interface
- Check whether entered values are outside the model input range
- View input parameter definitions using the embedded schematic figure
- Export batch prediction results to Excel format

The software runs as a native Windows desktop application and does not require Python, a browser, or an internet connection after packaging.

---

## Model

The current version uses a trained **Gaussian Process Regression (GPR)** model.

The model is loaded from:

```text
models/gpr_model.pkl