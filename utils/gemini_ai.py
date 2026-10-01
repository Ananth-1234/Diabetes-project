# ==========================================
# GEMINI AI INTEGRATION
# ==========================================

import google.generativeai as genai
from config import Config

# ------------------------------------------
# CONFIGURE GEMINI
# ------------------------------------------
try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel(Config.GEMINI_MODEL)
except Exception as e:
    print("⚠ Gemini configuration error:", e)
    model = None


# ==========================================
# GENERATE AI RECOMMENDATION
# ==========================================
def generate_recommendation(patient_data, prediction_result):
    """
    Generates short medical recommendation
    """

    if model is None:
        return "AI service unavailable."

    prompt = f"""
    You are a professional medical assistant.

    Patient Details:
    {patient_data}

    Prediction Result: {prediction_result}

    Give:
    - Short explanation of the result
    - 5 lifestyle recommendations
    - Keep response simple and medically safe
    - Do not provide extreme medical advice
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("⚠ Gemini error:", e)
        return "AI recommendation temporarily unavailable."


# ==========================================
# AI CHAT FUNCTION
# ==========================================
def chat_with_ai(user_message):
    """
    Handles diabetes AI chat
    """

    if model is None:
        return "AI service unavailable."

    prompt = f"""
    You are a helpful and safe diabetes assistant.

    Rules:
    - Answer clearly
    - Avoid dangerous medical advice
    - Encourage consulting doctor when needed

    Question: {user_message}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("⚠ Gemini chat error:", e)
        return "AI chat service temporarily unavailable."