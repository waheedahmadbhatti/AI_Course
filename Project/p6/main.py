import os

import numpy as np
import pandas as pd
import joblib
import streamlit as st


MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_diabetes_model.joblib")

FEATURE_INFO = {
    "age": "Age",
    "sex": "Sex",
    "bmi": "Body Mass Index",
    "bp": "Average Blood Pressure",
    "s1": "Total Serum Cholesterol (tc)",
    "s2": "Low-Density Lipoproteins (ldl)",
    "s3": "High-Density Lipoproteins (hdl)",
    "s4": "Total Cholesterol / HDL (tch)",
    "s5": "Log Serum Triglycerides (ltg)",
    "s6": "Blood Sugar Level (glu)",
}


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_data():
    return load_diabetes(as_frame=True).frame


st.set_page_config(page_title="Diabetes Progression Predictor", page_icon="🩺",
                   layout="wide")

model = load_model()
df = load_data()
features = df.drop(columns="target")
target = df["target"]

st.title("🩺 Diabetes Progression Predictor")
st.markdown(
    "Predicts the **disease progression one year after baseline** "
    "(a quantitative measure) from 10 patient features. "
    "Model trained on the sklearn diabetes dataset (442 patients)."
)

# ---- sidebar inputs ----
st.sidebar.header("Patient Features")

for col in features.columns:
    if col not in st.session_state:
        st.session_state[col] = float(features[col].median())
    lo = float(features[col].min())
    hi = float(features[col].max())
    label = f"{col} — {FEATURE_INFO.get(col, col)}"
    st.sidebar.slider(label, lo, hi, key=col, format="%.4f")

if st.sidebar.button("Load random sample patient"):
    row = features.sample(1, random_state=None).iloc[0]
    for col in features.columns:
        st.session_state[col] = float(row[col])
    st.rerun()

if st.sidebar.button("Reset to median patient"):
    for col in features.columns:
        st.session_state[col] = float(features[col].median())
    st.rerun()

inputs = {col: st.session_state[col] for col in features.columns}
input_df = pd.DataFrame([inputs])[features.columns]

# ---- prediction ----
prediction = float(model.predict(input_df)[0])

col1, col2, col3 = st.columns(3)
col1.metric("Predicted Progression", f"{prediction:.1f}")
col2.metric("Dataset Mean", f"{target.mean():.1f}")
col3.metric("Dataset Range", f"{target.min():.0f} – {target.max():.0f}")

if prediction > target.mean():
    st.warning(f"Predicted progression ({prediction:.1f}) is **above** the dataset "
               f"mean ({target.mean():.1f}) — higher risk of disease progression.")
else:
    st.success(f"Predicted progression ({prediction:.1f}) is **below** the dataset "
               f"mean ({target.mean():.1f}) — lower risk of disease progression.")

# ---- details ----
with st.expander("Input features"):
    st.dataframe(input_df.T.rename(columns={0: "Value"}), use_container_width=True)

with st.expander("About the model"):
    st.write(
        "The model is a scikit-learn pipeline (`StandardScaler` + tuned regressor) "
        "selected via cross-validation and GridSearchCV in "
        "`diabetes_regression_project.ipynb`, then saved with `joblib.dump`."
    )
    st.write(f"Model file: `{os.path.basename(MODEL_PATH)}`")
