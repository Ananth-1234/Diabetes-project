# ==========================================
# IMPORT LIBRARIES
# ==========================================
import numpy as np
import joblib
import os
import xgboost as xgb

# ==========================================
# LOAD MODEL SAFELY
# ==========================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Try multiple likely model filenames and prefer a non-empty file
PKL_PATH = os.path.join(BASE_DIR, "..", "diabetes_xgboost_model.pkl")
MODEL_FILE_PATH = os.path.join(BASE_DIR, "..", "diabetes_xgboost_model.model")

def _find_valid_model_path():
    candidates = [PKL_PATH, MODEL_FILE_PATH]
    for p in candidates:
        try:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                return p
        except OSError:
            continue
    return None

_path = _find_valid_model_path()
model = None
if _path is None:
    print("[prediction] No valid model file found. Checked: ", PKL_PATH, MODEL_FILE_PATH)
else:
    # First try joblib (scikit-learn pickled model)
    try:
        model = joblib.load(_path)
    except EOFError:
        print(f"[prediction] Model file '{_path}' appears to be empty or corrupted (EOFError).")
        model = None
    except Exception:
        # If joblib fails, try XGBoost native loading
        try:
            if _path.lower().endswith('.model'):
                # Try loading into an XGBClassifier (scikit-learn API)
                try:
                    clf = xgb.XGBClassifier()
                    clf.load_model(_path)
                    model = clf
                except Exception:
                    # Fallback to raw Booster
                    booster = xgb.Booster()
                    booster.load_model(_path)
                    model = booster
            else:
                # last resort: attempt joblib.load again to surface error
                model = joblib.load(_path)
        except Exception as e:
            print(f"[prediction] Failed to load model from '{_path}' as joblib/XGBoost: {e}")
            model = None


# ==========================================
# PREDICTION FUNCTION
# ==========================================
def predict_diabetes(pregnancies, glucose, blood_pressure,
                     skin_thickness, insulin, bmi,
                     dpf, age):
    """
    Takes individual patient values and returns:
    result (Diabetic / Not Diabetic)
    probability (float)
    """

    # Ensure model loaded
    if model is None:
        return ("Error: prediction model not available. Check server logs." , 0.0)

    try:
        # Convert to numpy array
        input_data = np.array([[pregnancies, glucose, blood_pressure,
                                skin_thickness, insulin, bmi,
                                dpf, age]])

        # If model is an XGBoost Booster (raw), use DMatrix and booster.predict
        if isinstance(model, xgb.Booster):
            dmat = xgb.DMatrix(input_data)
            probs = model.predict(dmat)
            # probs may be shape (n,) for binary:logistic
            prob = float(probs[0]) if hasattr(probs, '__len__') else float(probs)
            pred = 1 if prob >= 0.5 else 0
            result = "Diabetic" if pred == 1 else "Not Diabetic"
            return result, round(float(prob), 2)

        # If model follows scikit-learn API
        if hasattr(model, 'predict_proba'):
            prediction = model.predict(input_data)[0]
            probability = model.predict_proba(input_data)[0][1]
            result = "Diabetic" if prediction == 1 else "Not Diabetic"
            return result, round(float(probability), 2)

        # Fallback: try predict only
        prediction = model.predict(input_data)[0]
        prob = float(prediction)
        result = "Diabetic" if prediction == 1 else "Not Diabetic"
        return result, round(prob, 2)

    except Exception as e:
        return f"Error: {str(e)}", 0.0