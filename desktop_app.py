# -*- coding: utf-8 -*-
"""
HFRC Prediction (Desktop App)
- PySide6 GUI (no browser)
- Manual single prediction + Excel/CSV batch prediction
- Works in normal run + PyInstaller (onefile/onedir) via resource_path()
- LaTeX-like display for header + form labels (rendered to images via matplotlib mathtext)
- Hides technical/debug text from UI
"""

import os
import sys
import unicodedata
from io import BytesIO

import numpy as np
import pandas as pd

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QDoubleSpinBox, QPushButton, QFileDialog,
    QMessageBox, QGroupBox, QTableView, QSplitter
)

# ----------------- PATH HELPERS (FIX FOR EXE) -----------------
def resource_path(*parts) -> str:
    """
    Returns absolute path to resource in both:
    - normal python run
    - PyInstaller (onefile/onedir) run
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS  # temp extracted folder
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)

# Base directory for file dialogs (a real, writable folder)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Models folder (bundle as: --add-data "models;models")
MODELS_DIR = resource_path("models")

# ----------------- FEATURES -----------------
CANONICAL_FEATURES = [ "Rb", "H", "R.R", "S.R", "fy", "T", "Ag", "Ef", "tf", "εfε", "fc"]
RENAME_TO_NTF_EFE = {"tf": "ntf", "εfε": "efe"}
FONT_SIZE=5
UNIT_MAP = {
    "H": "mm",
    "Ag": "mm²",
    "T": "°C",
    "fc": "MPa",
    "fy": "MPa",
    "Ef": "MPa",
    "tf": "mm",
}

# ----------------- LaTeX DISPLAY (rendered to pixmap) -----------------
def latex_to_pixmap(latex: str, fontsize: int = 16, dpi: int = 220) -> QPixmap:
    """
    Render a LaTeX-like math string to a transparent PNG QPixmap.
    Uses matplotlib mathtext (NO TeX installation required).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(0.01, 0.01), dpi=dpi)
    fig.patch.set_alpha(0.0)

    # Draw text to get bounding box
    txt = fig.text(0, 0, latex, fontsize=fontsize)
    fig.canvas.draw()
    bbox = txt.get_window_extent()

    # Resize tightly
    w_in = bbox.width / dpi
    h_in = bbox.height / dpi
    fig.set_size_inches(max(w_in, 0.01), max(h_in, 0.01))

    txt.set_position((0, 0))
    fig.canvas.draw()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.0)
    plt.close(fig)

    pix = QPixmap()
    pix.loadFromData(buf.getvalue(), "PNG")
    return pix



# Per-feature LaTeX labels for the form (canonical -> latex)
LATEX_LABELS = {
    "Rb": r"$R_b$",
    "H": r"$H$",
    "R.R": r"$R.R$",
    "S.R": r"$S.R$",
    "fy": r"$f_y$",
    "T": r"$T$",
    "Ag": r"$A_g$",
    "Ef": r"$E_f$",
    "tf": r"$t_f$",
    "εfε": r"$\varepsilon_{f\varepsilon}$",
    "fc": r"$f_c$",
}

# Cache pixmaps so labels render once (faster)
_PIX_CACHE: dict[tuple[str, int], QPixmap] = {}

def get_pix(latex: str, fontsize: int = 14) -> QPixmap:
    key = (latex, fontsize)
    if key not in _PIX_CACHE:
        _PIX_CACHE[key] = latex_to_pixmap(latex, fontsize=fontsize)
    return _PIX_CACHE[key]


# ----------------- Excel column aliasing -> canonical -----------------
def _normalize_col(s: str) -> str:
    s = "" if s is None else str(s).strip()
    s = unicodedata.normalize("NFKC", s)
    s = s.replace(" ", "").replace("\n", "").replace("\t", "")
    s = s.replace("–", "-").replace("—", "-")
    return s.lower()

COL_ALIASES = {
    "Rb": ["rb", "r/b", "corneradiusratio", "corner_ratio", "rb_ratio"],
    "H": ["h", "height", "specimenheight"],
    "R.R": ["r.r", "rr", "longratio", "longitudinalratio", "rho_l"],
    "S.R": ["s.r", "sr", "transratio", "transverseratio", "rho_t"],
    "fy": ["fy", "f_y", "yieldstrength", "yield_strength"],
    "T": ["t", "temp", "temperature", "heatingtemperature"],
    "Ag": ["ag", "area", "grossarea", "gross_area"],
    "Ef": ["ef", "e_f", "modulus", "frpmodulus", "frp_modulus"],
    "tf": ["tf", "t_f", "thickness", "frpthickness", "frp_thickness", "totalfrpthickness"],
    "εfε": ["εfε", "efe", "epsf", "epsilonf", "effectivefrpstrain", "effstrain"],
    "fc": ["fc", "f_c", "compressivestrength", "concretestrength", "fck"],
    "ntf": ["ntf"],
    "efe": ["efe"],
}

def rename_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    norm_map = {_normalize_col(c): c for c in df.columns}
    rename_dict = {}
    for canon, aliases in COL_ALIASES.items():
        for a in aliases:
            a_norm = _normalize_col(a)
            if a_norm in norm_map:
                rename_dict[norm_map[a_norm]] = canon
                break
    return df.rename(columns=rename_dict)

def _coerce_numeric_series(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s
    s2 = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s2, errors="coerce")


# ----------------- MODEL LOADING -----------------
def load_models():
    models = {}

    # XGBoost
    try:
        import xgboost as xgb
        path = os.path.join(MODELS_DIR, "xgb_model.json")
        if os.path.exists(path):
            m = xgb.XGBRegressor()
            m.load_model(path)
            models["XGBoost"] = m
    except Exception:
        # Do NOT show error in UI; just hide the model option by not adding it
        pass

    # CatBoost
    try:
        from catboost import CatBoostRegressor
        path = os.path.join(MODELS_DIR, "catboost_model.cbm")
        if os.path.exists(path):
            cb = CatBoostRegressor()
            cb.load_model(path)
            models["CatBoost"] = cb
    except Exception:
        pass

    if not models:
        # keep one placeholder so UI doesn't crash
        models["(No model found)"] = ("ERR", f"No model files in {MODELS_DIR}")

    return models

def get_expected_features(model):
    # sklearn
    if hasattr(model, "feature_names_in_"):
        try:
            return list(model.feature_names_in_)
        except Exception:
            pass

    # xgboost
    if hasattr(model, "get_booster"):
        try:
            booster = model.get_booster()
            names = booster.feature_names
            if names:
                return list(names)
        except Exception:
            pass

    # catboost
    if hasattr(model, "feature_names_"):
        try:
            names = list(model.feature_names_)
            if names:
                return names
        except Exception:
            pass

    return CANONICAL_FEATURES

def build_input_df_for_model(user_values: dict, model):
    expected = get_expected_features(model)

    # If model expects ntf/efe, convert
    if "ntf" in expected or "efe" in expected:
        converted = {RENAME_TO_NTF_EFE.get(k, k): v for k, v in user_values.items()}
    else:
        converted = dict(user_values)

    missing = [c for c in expected if c not in converted]
    if missing:
        raise ValueError(f"Missing columns for model input: {missing}")

    return pd.DataFrame([[converted[c] for c in expected]], columns=expected)

def predict_fn(model, X_df: pd.DataFrame) -> float:
    return float(model.predict(X_df).ravel()[0])


# ----------------- TABLE MODEL -----------------
class PandasTableModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def set_df(self, df):
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if self._df is None else len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return 0 if self._df is None else len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or self._df is None:
            return None
        if role == Qt.DisplayRole:
            val = self._df.iat[index.row(), index.column()]
            if isinstance(val, float):
                if np.isnan(val):
                    return ""
                return f"{val:.6f}"
            return str(val)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if self._df is None or role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section)


# ----------------- MAIN WINDOW -----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HFRC Prediction (Desktop)")
        self.resize(1100, 650)

        self.models = load_models()
        self.model_name = None
        self.model_obj = None

        self.df_loaded = None
        self.df_out = None

        root = QVBoxLayout(self)



        # -------- top row: model select (no status text) --------
        top = QHBoxLayout()
        top.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(list(self.models.keys()))
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        top.addWidget(self.model_combo, 1)

        # status hidden (user asked to remove)
        self.status = QLabel("")
        self.status.setText("")
        top.addWidget(self.status, 0)
        root.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        SPIN_W = 260
        UNIT_W = 50
        
        grp_manual = QGroupBox("Single prediction (manual input)")
        form = QFormLayout(grp_manual)
        
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        form.setFormAlignment(Qt.AlignTop)
        form.setLabelAlignment(Qt.AlignRight)
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        
        self.inputs = {}
        
        for feat in CANONICAL_FEATURES:
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setRange(-1e12, 1e12)
            spin.setValue(0.0)
            spin.setSingleStep(1.0)
            spin.setFixedWidth(SPIN_W)
        
            latex = LATEX_LABELS.get(feat, feat)
            label_widget = QLabel()
            label_widget.setPixmap(get_pix(latex, fontsize=FONT_SIZE))
            label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
            unit_text = UNIT_MAP.get(feat, "")
            unit_lbl = QLabel(unit_text)
            unit_lbl.setFixedWidth(UNIT_W)
            unit_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            unit_lbl.setStyleSheet("color:#666; padding-left:6px;")
        
            field = QWidget()
            h = QHBoxLayout(field)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            h.addWidget(spin)
            h.addWidget(unit_lbl)
        
            form.addRow(label_widget, field)
            self.inputs[feat] = spin
        
        left_layout.addWidget(grp_manual)   # <- important

        self.btn_predict = QPushButton("Predict")
        self.btn_predict.clicked.connect(self.single_predict)
        left_layout.addWidget(self.btn_predict)

        self.lbl_result = QLabel("Predicted $F_n$: -")
        # Render output label as LaTeX pixmap too
        self.lbl_result_img = QLabel()
        self.lbl_result_img.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._set_result_pix(None)
        left_layout.addWidget(self.lbl_result_img)

        left_layout.addStretch(1)

        # -------- right panel: batch --------
        right = QWidget()
        right_layout = QVBoxLayout(right)

        grp_batch = QGroupBox("Batch prediction (Excel/CSV)")
        batch_layout = QVBoxLayout(grp_batch)

        btn_row = QHBoxLayout()
        self.btn_load = QPushButton("Load Excel/CSV")
        self.btn_load.clicked.connect(self.load_file)
        btn_row.addWidget(self.btn_load)

        self.btn_run = QPushButton("Run batch prediction")
        self.btn_run.clicked.connect(self.run_batch)
        self.btn_run.setEnabled(False)
        btn_row.addWidget(self.btn_run)

        self.btn_export = QPushButton("Export results to Excel")
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setEnabled(False)
        btn_row.addWidget(self.btn_export)

        batch_layout.addLayout(btn_row)

        self.table = QTableView()
        self.table_model = PandasTableModel(pd.DataFrame())
        self.table.setModel(self.table_model)
        batch_layout.addWidget(self.table, 1)

        right_layout.addWidget(grp_batch, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([420, 680])

        self.on_model_changed(self.model_combo.currentText())

    def _set_result_pix(self, value: float | None):
        if value is None:
            latex = r"$\mathbf{Predicted}\ \it{F_n}: \ -$"
        else:
            latex = rf"$\mathbf{{Predicted}}\ \it{{F_n}}: \ {value:.6f}$"
        self.lbl_result_img.setPixmap(get_pix(latex, fontsize=FONT_SIZE))

    def on_model_changed(self, name: str):
        self.model_name = name
        obj = self.models.get(name)

        if isinstance(obj, tuple) and obj and obj[0] == "ERR":
            self.model_obj = None
            self.btn_predict.setEnabled(False)
            self.btn_run.setEnabled(False)
            return

        self.model_obj = obj
        self.btn_predict.setEnabled(True)
        self.btn_run.setEnabled(self.df_loaded is not None)

    def single_predict(self):
        if self.model_obj is None:
            QMessageBox.warning(self, "Error", "Model not loaded.")
            return

        user_vals = {k: float(sp.value()) for k, sp in self.inputs.items()}
        try:
            X = build_input_df_for_model(user_vals, self.model_obj)
            y = predict_fn(self.model_obj, X)
            self._set_result_pix(y)
        except Exception as e:
            QMessageBox.critical(self, "Prediction error", str(e))

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel/CSV",
            BASE_DIR,
            "Data Files (*.xlsx *.xls *.csv)"
        )
        if not path:
            return

        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)

            self.df_loaded = df
            self.df_out = None
            self.table_model.set_df(df.head(200))
            self.btn_run.setEnabled(self.model_obj is not None)
            self.btn_export.setEnabled(False)
            QMessageBox.information(self, "Loaded", f"Loaded {len(df)} rows.\nShowing first 200 rows in table.")
        except Exception as e:
            QMessageBox.critical(self, "Load error", str(e))

    def run_batch(self):
        if self.model_obj is None or self.df_loaded is None:
            return

        try:
            df = self.df_loaded.copy()
            df = rename_to_canonical(df)

            # map ntf/efe if present
            if "tf" not in df.columns and "ntf" in df.columns:
                df["tf"] = df["ntf"]
            if "εfε" not in df.columns and "efe" in df.columns:
                df["εfε"] = df["efe"]

            missing = [c for c in CANONICAL_FEATURES if c not in df.columns]
            if missing:
                raise ValueError(
                    "Missing columns:\n" + ", ".join(missing) +
                    "\n\nRecommended columns:\n" + ", ".join(CANONICAL_FEATURES)
                )

            for c in CANONICAL_FEATURES:
                df[c] = _coerce_numeric_series(df[c])

            preds = []
            bad_rows = 0

            for _, row in df.iterrows():
                user_vals = {c: row[c] for c in CANONICAL_FEATURES}
                if any(pd.isna(user_vals[c]) for c in CANONICAL_FEATURES):
                    preds.append(np.nan)
                    bad_rows += 1
                    continue
                X = build_input_df_for_model(user_vals, self.model_obj)
                preds.append(predict_fn(self.model_obj, X))

            df["Pred_Fn"] = preds
            self.df_out = df
            self.table_model.set_df(df.head(500))
            self.btn_export.setEnabled(True)

            ok = int(df["Pred_Fn"].notna().sum())
            QMessageBox.information(
                self,
                "Batch done",
                f"Predicted: {ok}/{len(df)}\nRows with missing/invalid inputs: {bad_rows}\nShowing first 500 rows."
            )

        except Exception as e:
            QMessageBox.critical(self, "Batch error", str(e))

    def export_results(self):
        if self.df_out is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel",
            os.path.join(BASE_DIR, "hfrc_predictions.xlsx"),
            "Excel (*.xlsx)"
        )
        if not path:
            return

        try:
            self.df_out.to_excel(path, index=False, sheet_name="Predictions")
            QMessageBox.information(self, "Saved", f"Saved:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
