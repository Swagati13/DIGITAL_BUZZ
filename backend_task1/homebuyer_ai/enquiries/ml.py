# enquiries/ml.py
import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report
from enquiries.models import Enquiry

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model_artifact.joblib"   # store tuple (model, encoders, feature_names, meta)
MODEL_JSON = BASE_DIR / "model_metadata.json"

CATEGORICAL_COLS = ['city', 'property_type', 'name']  # keep consistent across train/predict
NUMERIC_COLS = ['age', 'income', 'budget', 'followups', 'site_visited']

def _load_data_from_db():
    df = pd.DataFrame(list(Enquiry.objects.all().values()))
    if df.empty:
        return df
    # ensure created_at exists; if not, silence
    if 'created_at' not in df.columns:
        df['created_at'] = pd.NaT
    return df

def train_model(model_name='rf_v1'):
    df = _load_data_from_db()
    if df.empty:
        raise ValueError("No data available for training")

    # ensure columns types and fillna
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df.get(c), errors='coerce').fillna(0)

    for c in CATEGORICAL_COLS:
        df[c] = df.get(c, '').astype(str).fillna('unknown')

    # Prepare encoders
    label_encoders = {}
    for c in CATEGORICAL_COLS:
        le = LabelEncoder()
        df[c] = le.fit_transform(df[c])
        label_encoders[c] = le

    feature_names = NUMERIC_COLS + CATEGORICAL_COLS
    X = df[feature_names]
    y = df['booked'].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique())>1 else None)

    model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = float(accuracy_score(y_test, preds))
    f1 = float(f1_score(y_test, preds, zero_division=0))
    report = classification_report(y_test, preds, zero_division=0, output_dict=True)

    # Save artifact: model object + encoders + feature_names
    artifact = {'model': model, 'encoders': label_encoders, 'feature_names': feature_names}
    joblib.dump(artifact, MODEL_PATH)

    # Save metadata easy-to-read JSON
    metadata = {
        'model_name': model_name,
        'accuracy': acc,
        'f1': f1,
        'n_samples': len(df),
        'n_features': len(feature_names),
    }
    with open(MODEL_JSON, 'w', encoding='utf-8') as f:
        json.dump(metadata, f)

    return metadata

def load_artifact():
    if not MODEL_PATH.exists():
        return None
    artifact = joblib.load(MODEL_PATH)
    return artifact

def predict_user(enquiry_data):
    artifact = load_artifact()
    if not artifact:
        raise ValueError("No trained model available. Call /api/train/ first.")

    model = artifact['model']
    encoders = artifact['encoders']
    feature_names = artifact['feature_names']

    # Build input row
    row = {}
    # numeric
    for c in NUMERIC_COLS:
        val = enquiry_data.get(c, None)
        if val is None and c == 'site_visited':  # ensure boolean handled
            val = 0
        row[c] = val if val is not None else 0

    # categorical
    for c in CATEGORICAL_COLS:
        row[c] = str(enquiry_data.get(c, 'unknown'))

    df = pd.DataFrame([row])[feature_names]

    # Transform categorical using encoders; handle unseen by adding as unseen -> map to a new class index
    for c in CATEGORICAL_COLS:
        enc = encoders[c]
        val = df.at[0, c]
        if val not in enc.classes_:
            # Option: map unseen categories to a special index by adding to classes
            enc.classes_ = np.append(enc.classes_, val)
        df[c] = enc.transform(df[c])

    proba = None
    if hasattr(model, "predict_proba"):
        proba = float(max(model.predict_proba(df)[0]))
    pred = int(model.predict(df)[0])
    return {'prediction': int(pred), 'probability': proba}

def get_feature_importances(top_k=10):
    artifact = load_artifact()
    if not artifact:
        raise ValueError("No trained model available")
    model = artifact['model']
    feature_names = artifact['feature_names']
    importances = model.feature_importances_
    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    return [{'feature': f, 'importance': float(imp)} for f, imp in pairs[:top_k]]

def generate_report():
    """
    Auto-generate textual AI summary report using model metadata and DB stats.
    """
    df = _load_data_from_db()
    if df.empty:
        return "No data available to generate report."
    # Load model metadata
    meta = {}
    if MODEL_JSON.exists():
        with open(MODEL_JSON, 'r', encoding='utf-8') as f:
            meta = json.load(f)

    total = len(df)
    booked = int(df['booked'].sum())
    positive_rate = booked / total if total else 0

    # top cities by interested buyers
    city_counts = df[df['booked']==1]['city'].value_counts().head(5).to_dict()
    # top property types
    pt_counts = df[df['booked']==1]['property_type'].value_counts().head(5).to_dict()

    features = get_feature_importances(top_k=5) if MODEL_PATH.exists() else []

    lines = []
    lines.append(f"AI Summary Report — Model: {meta.get('model_name','N/A')}")
    lines.append(f"Dataset size: {total} enquiries; Booked: {booked} ({positive_rate:.1%})")
    if meta:
        lines.append(f"Model accuracy: {meta.get('accuracy', 'N/A'):.2f}, F1: {meta.get('f1','N/A'):.2f}")
    if features:
        lines.append("Top features influencing booking (descending):")
        for f in features:
            lines.append(f"- {f['feature']}: importance {f['importance']:.3f}")
    if city_counts:
        lines.append("Top cities (booked): " + ", ".join([f"{k} ({v})" for k,v in city_counts.items()]))
    if pt_counts:
        lines.append("Top property types (booked): " + ", ".join([f"{k} ({v})" for k,v in pt_counts.items()]))

    # A simple actionable insight
    if 'income' in [f['feature'] for f in features]:
        lines.append("Insight: Income is a strong predictor — consider targeted financing offers.")
    else:
        lines.append("Insight: Consider gathering more income-related data to improve targeting.")

    return "\n".join(lines)

# Very small helper to compute funnel counts:
def compute_funnel():
    """
    returns counts: total enquiries, with followups (>0), site_visited True, booked True
    """
    df = _load_data_from_db()
    total = len(df)
    followups = int(df[df['followups'] > 0].shape[0]) if not df.empty else 0
    visited = int(df[df['site_visited']==True].shape[0]) if not df.empty else 0
    booked = int(df[df['booked']==True].shape[0]) if not df.empty else 0
    return {'total': total, 'with_followups': followups, 'site_visited': visited, 'booked': booked}
