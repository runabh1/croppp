"""
Smart Farming Decision System - Flask Backend
AI-Based Crop Recommendation & Advisory System for Marginal Farmers
Integrates: ML Models + Planet Satellite + OpenWeatherMap + Gemini AI
"""

import os
import sys
import io
import json
import base64
import time
import warnings
import numpy as np
import pandas as pd
import joblib
import requests as http_requests
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from PIL import Image
from dotenv import load_dotenv
from functools import wraps

# ── PyTorch / torchvision (optional — only needed for ConvNeXt-V2) ──────
try:
    import torch
    import torchvision.transforms as T
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch not installed — ConvNeXt-V2 disease model will be unavailable.")

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables from this app's .env file, regardless of launch directory.
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

warnings.filterwarnings("ignore")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION (All keys loaded from .env file)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = "smart_farming_secret_key_2024"  # For sessions

PLANET_API_KEY = os.environ.get("PLANET_API_KEY", "")
PLANET_API_URL = "https://api.planet.com/data/v1"
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")  # Support for custom model
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_API_URL = "https://api.thenewsapi.com/v1/news/top"
NEWS_CACHE = {}  # Per-category cache: {"category_name": {"data": [], "timestamp": time}}
NEWS_CACHE_DURATION = 300  # 5 minutes



def gemini_request(prompt, temperature=0.7, max_tokens=1500, retries=3):
    """Call Gemini API with automatic retry and model fallback."""
    # Try primary model first, then fallbacks
    models_to_try = [GEMINI_MODEL] + GEMINI_FALLBACK_MODELS
    models_to_try = list(dict.fromkeys(models_to_try))  # Remove duplicates while preserving order
    
    for model in models_to_try:
        for attempt in range(retries):
            try:
                url = f"{GEMINI_API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
                resp = http_requests.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_tokens
                        }
                    },
                    timeout=60
                )
                if resp.status_code == 200:
                    print(f"✅ Gemini API successful with model: {model}")
                    return resp
                
                if resp.status_code == 429:
                    if "quota" in resp.text.lower():
                        print(f"⚠️ Gemini quota exceeded for {model}. Using fallback logic.")
                        return resp
                    elif attempt < retries - 1:
                        wait = 2 ** (attempt + 1)
                        print(f"⏳ Gemini rate limited, retrying in {wait}s... (attempt {attempt+1}/{retries})")
                        time.sleep(wait)
                        continue
                
                if resp.status_code in (503, 500) and attempt < retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"⏳ Gemini returned {resp.status_code}, retrying in {wait}s... (attempt {attempt+1}/{retries})")
                    time.sleep(wait)
                    continue
                
                # If model not found, try next model
                if resp.status_code == 404:
                    print(f"⚠️ Model {model} not available, trying next...")
                    break
                
                # Other errors
                print(f"⚠️ Gemini API error with {model}: {resp.status_code}")
                if attempt == retries - 1:
                    break  # Try next model
                continue
                
            except Exception as e:
                print(f"⚠️ Gemini request error with {model}: {e}")
                if attempt == retries - 1:
                    break  # Try next model
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
    
    print(f"❌ All Gemini models failed. Falling back to rule-based logic.")
    return None
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD ML MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("🔄 Loading pre-trained models...")
crop_model_path = os.path.join(BASE_DIR, "crop_model_tuned.pkl")
if not os.path.exists(crop_model_path):
    crop_model_path = os.path.join(BASE_DIR, "crop_model.pkl")
crop_model = joblib.load(crop_model_path)
crop_encoder = joblib.load(os.path.join(BASE_DIR, "crop_encoder.pkl"))
yield_model = joblib.load(os.path.join(BASE_DIR, "yield_model.pkl"))
price_model = joblib.load(os.path.join(BASE_DIR, "price_model.pkl"))
price_encoder = joblib.load(os.path.join(BASE_DIR, "price_encoder.pkl"))

for model in (crop_model, yield_model, price_model):
    if hasattr(model, "n_jobs"):
        model.n_jobs = 1
print("✅ All models loaded successfully!")

# ─── ConvNeXt-V2 Disease Detection Model ─────────────────────────────────
# 30-class Plant Village label map (alphabetical order used during training)
DISEASE_CLASSES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
]

convnext_model = None
convnext_transform = None
NUM_DISEASE_CLASSES = len(DISEASE_CLASSES)   # 30
CONVNEXT_MODEL_PATH = os.path.join(BASE_DIR, "ConvNeXt-V2.pt")

# Standard ImageNet normalisation used during training
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD  = [0.229, 0.224, 0.225]

if TORCH_AVAILABLE and os.path.exists(CONVNEXT_MODEL_PATH):
    try:
        _device = torch.device("cpu")
        _ckpt   = torch.load(CONVNEXT_MODEL_PATH, map_location=_device, weights_only=False)

        if not isinstance(_ckpt, dict):
            # Checkpoint is already a full nn.Module — use directly
            convnext_model = _ckpt.to(_device)

        else:
            # ── State-dict checkpoint ─────────────────────────────────────────
            # Detect key prefix so we can reconstruct the exact wrapper used
            # during training.
            _sample_key = next(iter(_ckpt))

            if _sample_key.startswith("convnext."):
                # Keys like "convnext.stem.0.weight" → model was trained as:
                #   class Wrapper(nn.Module):
                #       self.convnext = timm.create_model("convnext_small", ...)
                # We rebuild the same wrapper so load_state_dict works 1-to-1.
                import timm as _timm

                class _ConvNeXtWrapper(torch.nn.Module):
                    def __init__(self):
                        super().__init__()
                        self.convnext = _timm.create_model(
                            "convnextv2_tiny",
                            pretrained=False,
                            num_classes=NUM_DISEASE_CLASSES,
                        )
                    def forward(self, x):
                        return self.convnext(x)

                _wrapper = _ConvNeXtWrapper()
                _wrapper.load_state_dict(_ckpt, strict=True)
                convnext_model = _wrapper.to(_device)

            elif _sample_key.startswith("features.") or _sample_key.startswith("classifier."):
                # Pure torchvision ConvNeXt state-dict (no wrapper prefix)
                import torchvision.models as _tvm
                _m = _tvm.convnext_small(weights=None)
                _m.classifier[2] = torch.nn.Linear(
                    _m.classifier[2].in_features, NUM_DISEASE_CLASSES
                )
                _m.load_state_dict(_ckpt, strict=False)
                convnext_model = _m.to(_device)

            elif _sample_key.startswith("stages.") or _sample_key.startswith("stem."):
                # Raw timm ConvNeXt state-dict (no wrapper)
                import timm as _timm
                _m = _timm.create_model(
                    "convnext_small", pretrained=False, num_classes=NUM_DISEASE_CLASSES
                )
                _m.load_state_dict(_ckpt, strict=False)
                convnext_model = _m.to(_device)

            elif "model" in _ckpt:
                convnext_model = _ckpt["model"].to(_device)

            elif "state_dict" in _ckpt:
                import timm as _timm
                _m = _timm.create_model(
                    "convnextv2_tiny", pretrained=False, num_classes=NUM_DISEASE_CLASSES
                )
                _m.load_state_dict(_ckpt["state_dict"], strict=False)
                convnext_model = _m.to(_device)

            else:
                raise ValueError(f"Unrecognised checkpoint format. First key: {_sample_key!r}")

        # ── Verify inference with a dummy tensor ──────────────────────────────
        convnext_model.eval()
        with torch.no_grad():
            _dummy = torch.zeros(1, 3, 224, 224)
            _out   = convnext_model(_dummy)
            assert _out.shape[-1] == NUM_DISEASE_CLASSES, (
                f"Model outputs {_out.shape[-1]} classes, expected {NUM_DISEASE_CLASSES}"
            )

        convnext_transform = T.Compose([
            T.Resize(256),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])
        print(f"✅ ConvNeXt-V2 disease model loaded ({NUM_DISEASE_CLASSES} classes)")

    except Exception as _e:
        print(f"⚠️  ConvNeXt-V2 load error: {_e} — falling back to pixel analysis")
        convnext_model = None

elif not TORCH_AVAILABLE:
    print("⚠️  ConvNeXt-V2 skipped (PyTorch not installed)")
else:
    print(f"⚠️  ConvNeXt-V2.pt not found at {CONVNEXT_MODEL_PATH} — falling back to pixel analysis")

# Validate model feature names at startup
try:
    print(f"   📊 Crop model expects: {list(crop_model.feature_names_in_)}")
    print(f"   📊 Yield model expects: {list(yield_model.feature_names_in_)}")
    print(f"   📊 Price model expects: {list(price_model.feature_names_in_)}")
except AttributeError:
    print("   ⚠️ Some models lack feature_names_in_ (trained without DataFrame)")

RECOMMENDATION_CROP_CLASSES = list(map(str, crop_model.classes_))
PIPELINE_CROP_CLASSES = list(map(str, getattr(crop_encoder, "classes_", [])))
CROP_CLASSES = RECOMMENDATION_CROP_CLASSES

# MSP Data (2023-24)
MSP_DATA = {
    'rice': 2183, 'wheat': 2275, 'maize': 2090, 'cotton': 6620,
    'jute': 5050, 'lentil': 6425, 'mungbean': 8558, 'mothbeans': 6035,
    'pigeonpeas': 7000, 'kidneybeans': 3000, 'chickpea': 5440,
    'blackgram': 6950, 'soybean': 4600, 'groundnut': 6377,
    'mustard': 5650, 'barley': 1735, 'coconut': 3200, 'sugarcane': 315,
    'banana': 2500, 'mango': 4500, 'apple': 8000, 'grapes': 5000,
    'orange': 4000, 'watermelon': 1500, 'papaya': 3000, 'pomegranate': 7000,
    'muskmelon': 2000, 'coffee': 9500, 'tea': 12000
}

DEFAULT_MARKET = {
    'kharif_arrival': 5000.0,
    'kharif_price': 2500.0,
    'rabi_arrival': 4000.0,
    'rabi_price': 2500.0,
}

INPUT_DEFAULTS = {
    "N": 80.0,
    "P": 45.0,
    "K": 40.0,
    "Temperature": 26.0,
    "Humidity": 70.0,
    "pH": 6.5,
    "Rainfall": 150.0,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MOCK USER DATABASE & FARM DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOCK_USERS = {
    "abc@123": {
        "password": "1234",
        "farmer_name": "Ramesh Kumar",
        "phone": "9876543210",
        "state": "Maharashtra",
        "district": "Nashik",
        "village": "Nandgaon",
        "latitude": 19.8967,
        "longitude": 73.7754,
        "total_land": 5.0,  # hectares
        "land_type": "Irrigated"
    }
}

FARM_DATA = {
    "abc@123": {
        "total_land": 5.0,
        "crops": [
            {
                "id": "crop_1",
                "name": "Sugarcane",
                "area": 2.5,
                "planting_date": "2024-01-15",
                "expected_harvest": "2025-01-15",
                "nitrogen": 100,
                "phosphorus": 50,
                "potassium": 60,
                "soil_ph": 6.8,
                "status": "Growing"
            },
            {
                "id": "crop_2",
                "name": "Wheat",
                "area": 1.5,
                "planting_date": "2024-10-01",
                "expected_harvest": "2025-03-15",
                "nitrogen": 120,
                "phosphorus": 60,
                "potassium": 40,
                "soil_ph": 7.0,
                "status": "Harvesting"
            },
            {
                "id": "crop_3",
                "name": "Maize",
                "area": 1.0,
                "planting_date": "2024-04-01",
                "expected_harvest": "2024-09-15",
                "nitrogen": 90,
                "phosphorus": 45,
                "potassium": 35,
                "soil_ph": 6.5,
                "status": "Harvested"
            }
        ]
    }
}

PRICE_FEATURE_DEFAULTS = {
    "MSP": 2500.0,
    "Kharif_Arrival": DEFAULT_MARKET["kharif_arrival"],
    "Kharif_Price": DEFAULT_MARKET["kharif_price"],
    "Rabi_Arrival": DEFAULT_MARKET["rabi_arrival"],
    "Rabi_Price": DEFAULT_MARKET["rabi_price"],
}

EXTREME_WEATHER_LIMITS = {
    "high_temp": 40.0,
    "low_temp": 10.0,
    "high_humidity": 90.0,
    "low_rainfall": 50.0,
}

# Disease DB
DISEASE_DB = [
    {"name": "Leaf Blight", "confidence": 87.3, "treatment": "Apply Mancozeb 75% WP @ 2.5g/L water. Remove infected leaves. Ensure proper spacing for air circulation."},
    {"name": "Powdery Mildew", "confidence": 82.1, "treatment": "Spray Sulphur 80% WP @ 3g/L or Karathane @ 1ml/L. Avoid excess nitrogen fertilization."},
    {"name": "Bacterial Leaf Spot", "confidence": 79.5, "treatment": "Apply Copper Oxychloride 50% WP @ 3g/L. Practice crop rotation. Use disease-free seeds."},
    {"name": "Rust Disease", "confidence": 91.2, "treatment": "Spray Propiconazole 25% EC @ 1ml/L. Remove volunteer plants. Use resistant varieties."},
    {"name": "Anthracnose", "confidence": 84.6, "treatment": "Apply Carbendazim 50% WP @ 1g/L. Avoid overhead irrigation. Remove crop debris."},
    {"name": "Mosaic Virus", "confidence": 76.8, "treatment": "No chemical cure. Remove infected plants. Control aphid vectors with Imidacloprid. Use virus-free seeds."},
    {"name": "Fusarium Wilt", "confidence": 88.4, "treatment": "Apply Trichoderma viride @ 4g/kg seed. Practice crop rotation (3+ years). Use resistant varieties."},
    {"name": "Healthy Leaf", "confidence": 95.2, "treatment": "No treatment needed. Continue regular maintenance. Monitor for early signs of disease."}
]

DISEASE_TREATMENTS = {
    "healthy": "No disease detected. Continue regular monitoring, balanced irrigation, and field sanitation.",
    "bacterial": "Remove infected leaves where practical. Apply copper oxychloride/copper hydroxide as per label, avoid overhead irrigation, and use disease-free seed or seedlings.",
    "blight": "Remove infected foliage and improve spacing for airflow. Apply Mancozeb or Chlorothalonil as per label and avoid working in wet fields.",
    "rust": "Remove volunteer host plants and heavily infected leaves. Spray Propiconazole or Tebuconazole as per label when symptoms are active.",
    "mosaic": "There is no chemical cure for viral mosaic. Rogue infected plants early, control aphid/whitefly vectors, and use resistant or certified planting material.",
    "yellow": "Use resistant varieties where available, remove infected plants, and manage whitefly/aphid vectors with recommended integrated pest management.",
    "curl": "Manage whitefly vectors, remove infected plants, and use virus-free seedlings and resistant varieties where available.",
    "rot": "Improve drainage, remove infected plant debris, avoid replanting susceptible crops in the same field, and use recommended fungicide/biocontrol treatments.",
    "mold": "Improve ventilation and reduce leaf wetness. Apply a recommended fungicide such as Mancozeb/Chlorothalonil as per local extension guidance.",
    "spot": "Remove diseased leaves, avoid overhead irrigation, rotate crops, and apply copper or Mancozeb-based protection as per label.",
    "mites": "Spray water to reduce dust, conserve beneficial insects, and use a recommended miticide if infestation is severe.",
    "septoria": "Remove lower infected leaves, mulch to prevent soil splash, rotate crops, and apply Chlorothalonil/Mancozeb as per label.",
}


def normalize_disease_label(label):
    label = str(label).replace("___", " ").replace("__", " ").replace("_", " ")
    return " ".join(label.split()).title()


def treatment_for_disease(label):
    normalized = normalize_disease_label(label)
    lower = normalized.lower()
    for key, treatment in DISEASE_TREATMENTS.items():
        if key in lower:
            return treatment
    return (
        "Isolate affected plants if symptoms are spreading, remove infected leaves, "
        "avoid overhead irrigation, and consult the local agriculture extension office "
        "for a crop-specific spray schedule."
    )


def estimate_severity(confidence: float, is_healthy: bool) -> dict:
    """Map model confidence to a severity level for diseased plants."""
    if is_healthy:
        return {"level": "None", "color": "#22c55e", "badge": "✅",
                "description": "No disease detected. Plant appears healthy."}
    if confidence >= 85:
        return {"level": "High", "color": "#ef4444", "badge": "🔴",
                "description": "Severe infection likely. Immediate intervention required."}
    if confidence >= 65:
        return {"level": "Medium", "color": "#f59e0b", "badge": "🟡",
                "description": "Moderate infection detected. Treat promptly to prevent spread."}
    return {"level": "Low", "color": "#22c55e", "badge": "🟢",
            "description": "Early or mild infection. Monitor closely and apply preventive measures."}


def generate_disease_advisory(disease_name: str, confidence: float, severity: str) -> dict:
    """Ask Gemini to produce structured treatment and prevention advice."""
    prompt = f"""You are an expert plant pathologist and agricultural advisor for Indian farmers.

A leaf image was analysed and the following disease was identified:
- Disease: {disease_name}
- Confidence: {confidence:.1f}%
- Severity: {severity}

Provide detailed, practical advice in JSON format ONLY (no markdown, no extra text):
{{
    "remedies": [
        "<specific pesticide / fungicide / bactericide with dosage and application method>",
        "<second remedy — biological or cultural practice>",
        "<third remedy — chemical or organic treatment>"
    ],
    "pesticides": [
        {{"name": "<product name>", "dose": "<dose per litre>", "frequency": "<how often>"}}
    ],
    "preventive_measures": [
        "<prevention tip 1 — seed treatment / resistant varieties>",
        "<prevention tip 2 — field sanitation / crop rotation>",
        "<prevention tip 3 — irrigation / spacing / monitoring>",
        "<prevention tip 4 — biological controls or forecasting>"
    ],
    "urgency_note": "<one sentence on how quickly to act>"
}}

Keep advice practical, affordable, and suitable for small-scale Indian farmers. Include brand-agnostic chemical names."""
    try:
        resp = gemini_request(prompt, temperature=0.5, max_tokens=800)
        if resp is None or resp.status_code != 200:
            return {}
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as _e:
        print(f"⚠️  Disease advisory Gemini error: {_e}")
        return {}


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def safe_float(value, default):
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTHENTICATION HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def require_login(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_email" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_user_email():
    """Get current logged-in user email from session"""
    return session.get("user_email")


def feature_names_for(model, fallback):
    names = getattr(model, "feature_names_in_", None)
    if names is None:
        return fallback
    return [str(name) for name in names]


def build_feature_frame(feature_names, values, defaults=None):
    payload = {}
    defaults = defaults or {}
    for feature_name in feature_names:
        payload[feature_name] = safe_float(values.get(feature_name), defaults.get(feature_name, 0.0))
    return pd.DataFrame([payload], columns=feature_names)


def normalize_core_inputs(data, weather_info=None):
    source = weather_info or {}
    return {
        "N": safe_float(data.get("N"), INPUT_DEFAULTS["N"]),
        "P": safe_float(data.get("P"), INPUT_DEFAULTS["P"]),
        "K": safe_float(data.get("K"), INPUT_DEFAULTS["K"]),
        "Temperature": safe_float(source.get("temperature", data.get("temperature")), INPUT_DEFAULTS["Temperature"]),
        "Humidity": safe_float(source.get("humidity", data.get("humidity")), INPUT_DEFAULTS["Humidity"]),
        "pH": safe_float(data.get("ph", data.get("pH")), INPUT_DEFAULTS["pH"]),
        "Rainfall": safe_float(source.get("rainfall", data.get("rainfall")), INPUT_DEFAULTS["Rainfall"]),
    }


def normalize_price_inputs(data, crop_name, crop_index):
    normalized_crop = str(crop_name).lower()
    msp = safe_float(data.get("msp"), MSP_DATA.get(normalized_crop, PRICE_FEATURE_DEFAULTS["MSP"]))
    values = {
        "Crop_Index": crop_index,
        "MSP": msp,
        "Kharif_Arrival": safe_float(data.get("kharif_arrival"), PRICE_FEATURE_DEFAULTS["Kharif_Arrival"]),
        "Kharif_Price": safe_float(data.get("kharif_price"), PRICE_FEATURE_DEFAULTS["Kharif_Price"]),
        "Rabi_Arrival": safe_float(data.get("rabi_arrival"), PRICE_FEATURE_DEFAULTS["Rabi_Arrival"]),
        "Rabi_Price": safe_float(data.get("rabi_price"), PRICE_FEATURE_DEFAULTS["Rabi_Price"]),
    }
    return values, msp


def resolve_crop_index(crop_name):
    crop_name = str(crop_name)
    if crop_name in PIPELINE_CROP_CLASSES:
        return PIPELINE_CROP_CLASSES.index(crop_name)
    return None


def predict_crop_recommendation(core_inputs):
    feature_names = feature_names_for(
        crop_model,
        ["N", "P", "K", "Temperature", "Humidity", "pH", "Rainfall"]
    )
    feature_frame = build_feature_frame(feature_names, core_inputs, INPUT_DEFAULTS)

    crop_prediction = crop_model.predict(feature_frame)[0]
    probabilities = crop_model.predict_proba(feature_frame)[0]
    crop_name = str(crop_prediction)
    confidence = round(float(np.max(probabilities)) * 100, 1)

    top_indices = np.argsort(probabilities)[-3:][::-1]
    top_raw_scores = [float(probabilities[index]) * 100 for index in top_indices]
    top_score_total = sum(top_raw_scores) or 1.0
    display_confidence = round((top_raw_scores[0] / top_score_total) * 100, 1)
    confidence_gap = round(top_raw_scores[0] - top_raw_scores[1], 1) if len(top_raw_scores) > 1 else top_raw_scores[0]
    top_crops = [
        {
            "name": str(CROP_CLASSES[index]).title(),
            "probability": round(float(probabilities[index]) * 100, 1),
            "score": round((float(probabilities[index]) * 100 / top_score_total) * 100, 1),
        }
        for index in top_indices
    ]

    if display_confidence >= 45 and confidence_gap >= 3:
        confidence_rating = "Strong"
    elif display_confidence >= 35:
        confidence_rating = "Medium"
    else:
        confidence_rating = "Low"

    return {
        "name": crop_name,
        "confidence": confidence,
        "display_confidence": display_confidence,
        "confidence_rating": confidence_rating,
        "top_crops": top_crops,
        "confidence_gap": confidence_gap,
        "confidence_note": "Raw model probability is spread across 22 crops, so the recommendation score is more useful than the absolute probability.",
        "low_confidence": display_confidence < 35,
    }


def select_pipeline_crop(crop_result):
    recommended_name = str(crop_result["name"])
    if recommended_name in PIPELINE_CROP_CLASSES:
        return recommended_name, None

    for option in crop_result.get("top_crops", []):
        option_name = str(option["name"]).lower()
        if option_name in PIPELINE_CROP_CLASSES:
            return option_name, (
                f"{recommended_name.title()} is not supported by the yield/price models, "
                f"so {option_name.title()} is being used for economic estimates."
            )

    fallback_name = PIPELINE_CROP_CLASSES[0] if PIPELINE_CROP_CLASSES else recommended_name
    return fallback_name, (
        f"{recommended_name.title()} is not supported by the yield/price models, "
        f"so {fallback_name.title()} is being used for economic estimates."
    )


def predict_yield_tons(core_inputs, crop_index):
    values = dict(core_inputs)
    values["Crop_Index"] = crop_index

    feature_names = feature_names_for(
        yield_model,
        ["Crop_Index", "N", "P", "K", "Temperature", "Humidity", "pH", "Rainfall"]
    )
    defaults = dict(INPUT_DEFAULTS)
    defaults["Crop_Index"] = 0.0
    feature_frame = build_feature_frame(feature_names, values, defaults)

    yield_kg_per_ha = float(yield_model.predict(feature_frame)[0])
    if yield_kg_per_ha < 0:
        yield_kg_per_ha = 0.0

    yield_tons_per_ha = round(clamp(yield_kg_per_ha / 1000.0, 0.0, 15.0), 2)
    return yield_kg_per_ha, yield_tons_per_ha


def predict_price_per_quintal(data, crop_name, crop_index):
    values, msp = normalize_price_inputs(data, crop_name, crop_index)
    feature_names = feature_names_for(
        price_model,
        ["Crop_Index", "MSP", "Kharif_Arrival", "Kharif_Price", "Rabi_Arrival", "Rabi_Price"]
    )
    defaults = dict(PRICE_FEATURE_DEFAULTS)
    defaults["Crop_Index"] = 0.0
    feature_frame = build_feature_frame(feature_names, values, defaults)
    price_per_quintal = round(max(100.0, float(price_model.predict(feature_frame)[0])), 2)
    return price_per_quintal, msp, values


def calculate_profit(yield_tons_per_ha, price_per_quintal):
    price_per_ton = price_per_quintal * 10.0
    gross_profit = yield_tons_per_ha * price_per_ton
    return round(clamp(gross_profit, 0.0, 500000.0), 2), price_per_ton


def build_rule_based_advisory(crop_name, crop_result, yield_tons_per_ha, price_per_quintal, msp, profit, rainfall, ndvi_data, risk_data):
    advisories = []
    if crop_result["low_confidence"]:
        advisories.append({
            "icon": "info",
            "severity": "warning",
            "title": "Low confidence recommendation",
            "message": "Check one or two alternative crops before sowing because the crop model confidence is below 60%."
        })

    if rainfall < 50:
        advisories.append({
            "icon": "water",
            "severity": "critical",
            "title": "Urgent irrigation needed",
            "message": "Rainfall is very low. Start irrigation immediately and use mulching to reduce soil moisture loss."
        })
    elif rainfall < 100:
        advisories.append({
            "icon": "cloud",
            "severity": "warning",
            "title": "Moisture stress watch",
            "message": "Rainfall is below the safe range. Irrigate in smaller intervals and conserve field moisture."
        })

    if yield_tons_per_ha < 2.0:
        advisories.append({
            "icon": "leaf",
            "severity": "warning",
            "title": "Yield can be improved",
            "message": "Expected yield is on the lower side. Recheck soil nutrition and apply a balanced NPK dose with organic matter."
        })

    if price_per_quintal < msp:
        advisories.append({
            "icon": "market",
            "severity": "warning",
            "title": "Price below MSP",
            "message": "Market price is below MSP. Prefer government procurement or delay selling if storage is available."
        })
    else:
        advisories.append({
            "icon": "market",
            "severity": "good",
            "title": "Market is supportive",
            "message": "Current price is at or above MSP. Plan harvest and selling around local mandi demand."
        })

    if ndvi_data.get("ndvi", 0.5) < 0.35:
        advisories.append({
            "icon": "satellite",
            "severity": "warning",
            "title": "Low vegetation health",
            "message": "NDVI is weak. Inspect the field for stress, pests, or nutrient deficiency within the next few days."
        })

    if risk_data["level"] == "High":
        advisories.append({
            "icon": "alert",
            "severity": "critical",
            "title": "High risk conditions",
            "message": "Current farm conditions are risky. Prioritize water, field monitoring, and short-term protective actions."
        })

    if not advisories:
        advisories.append({
            "icon": "check",
            "severity": "good",
            "title": "Conditions look stable",
            "message": f"{crop_name.title()} is performing within a normal range. Continue routine irrigation, nutrition, and pest scouting."
        })

    market_insight = (
        "Sell through MSP channels or hold briefly if local market prices stay weak."
        if price_per_quintal < msp else
        "Market price is supporting the crop, so focus on harvest timing and clean grading."
    )
    seasonal_tip = (
        "Keep irrigation ready for the next 7 to 10 days."
        if rainfall < 100 else
        "Use the present weather window to maintain weed and nutrient management."
    )

    return {
        "advisories": advisories,
        "seasonal_tip": seasonal_tip,
        "market_insight": market_insight,
        "overall_summary": (
            f"{crop_name.title()} is the recommended crop with {crop_result['confidence']}% confidence. "
            f"Expected yield is {yield_tons_per_ha} t/ha and expected gross profit is INR {profit:,.0f} per hectare."
        ),
        "source": "Rule-Based System"
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEATHER API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_weather(lat, lon):
    """Fetch real-time weather from OpenWeatherMap API."""
    try:
        resp = http_requests.get(WEATHER_API_URL, params={
            "lat": lat, "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }, timeout=8)

        if resp.status_code != 200:
            print(f"Weather API error: {resp.status_code} - {resp.text[:200]}")
            return None

        data = resp.json()
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = data.get("weather", [{}])[0]
        rain = data.get("rain", {})
        clouds = data.get("clouds", {})

        return {
            "temperature": round(main.get("temp", 25), 1),
            "humidity": round(main.get("humidity", 60), 1),
            "pressure": main.get("pressure", 1013),
            "feels_like": round(main.get("feels_like", 25), 1),
            "wind_speed": round(wind.get("speed", 0), 1),
            "wind_deg": wind.get("deg", 0),
            "description": weather.get("description", "clear sky").title(),
            "icon": weather.get("icon", "01d"),
            "clouds": clouds.get("all", 0),
            "rainfall": round(rain.get("1h", rain.get("3h", 0)) * 30, 1),  # Estimate monthly
            "city": data.get("name", "Unknown"),
            "country": data.get("sys", {}).get("country", ""),
            "source": "OpenWeatherMap API (Live)"
        }
    except Exception as e:
        print(f"⚠️ Weather fetch error: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLANET SATELLITE NDVI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_planet_ndvi(lat, lon):
    """Query Planet Data API for satellite NDVI data."""
    try:
        delta = 0.005
        aoi = {
            "type": "Polygon",
            "coordinates": [[
                [lon - delta, lat - delta],
                [lon + delta, lat - delta],
                [lon + delta, lat + delta],
                [lon - delta, lat + delta],
                [lon - delta, lat - delta]
            ]]
        }

        search_payload = {
            "item_types": ["PSScene"],
            "filter": {
                "type": "AndFilter",
                "config": [
                    {"type": "GeometryFilter", "field_name": "geometry", "config": aoi},
                    {"type": "DateRangeFilter", "field_name": "acquired",
                     "config": {"gte": "2025-01-01T00:00:00Z"}},
                    {"type": "RangeFilter", "field_name": "cloud_cover",
                     "config": {"lte": 0.15}},
                    {"type": "RangeFilter", "field_name": "visible_percent",
                     "config": {"gte": 80}}
                ]
            }
        }

        resp = http_requests.post(
            f"{PLANET_API_URL}/quick-search",
            auth=(PLANET_API_KEY, ""),
            json=search_payload, timeout=10
        )

        if resp.status_code != 200:
            return None

        features = resp.json().get("features", [])
        if not features:
            return None

        scene = features[0]
        props = scene.get("properties", {})

        cloud_cover = props.get("cloud_cover", 0)
        clear_percent = props.get("clear_percent", 100)
        visible_percent = props.get("visible_percent", 100)
        anomalous_pixels = props.get("anomalous_pixels", 0)

        vegetation_signal = (
            (clear_percent / 100.0) * 0.45 +
            (visible_percent / 100.0) * 0.35 +
            (1.0 - cloud_cover) * 0.15 +
            (1.0 - anomalous_pixels) * 0.05
        )

        ndvi = round(0.1 + vegetation_signal * 0.75, 3)
        ndvi = max(-0.1, min(0.95, ndvi))

        if ndvi >= 0.6:
            health, color = "Healthy", "#22c55e"
        elif ndvi >= 0.3:
            health, color = "Moderate", "#f59e0b"
        else:
            health, color = "Poor", "#ef4444"

        return {
            "ndvi": ndvi, "health": health, "color": color,
            "source": "Planet Satellite (PlanetScope)",
            "satellite_info": {
                "scene_id": scene.get("id", "Unknown"),
                "acquired": props.get("acquired", "Unknown"),
                "cloud_cover": round(cloud_cover * 100, 1),
                "clear_percent": round(clear_percent, 1),
                "visible_percent": round(visible_percent, 1)
            },
            "details": {
                "clear_signal": round(clear_percent / 100.0, 3),
                "visibility": round(visible_percent / 100.0, 3),
                "cloud_free": round(1.0 - cloud_cover, 3),
                "data_quality": round(1.0 - anomalous_pixels, 3)
            }
        }
    except Exception as e:
        print(f"⚠️ Planet API error: {e}")
        return None


def compute_ndvi_simulated(temperature, humidity, rainfall, ph):
    """Fallback NDVI simulation."""
    temp_factor = 1.0 - abs(temperature - 28) / 30.0
    hum_factor = humidity / 100.0
    rain_factor = min(rainfall / 200.0, 1.0)
    ph_factor = 1.0 - abs(ph - 6.5) / 5.0

    ndvi = 0.3 * temp_factor + 0.25 * hum_factor + 0.25 * rain_factor + 0.2 * ph_factor
    ndvi = round(max(-0.1, min(0.95, ndvi)), 3)

    if ndvi >= 0.6:
        health, color = "Healthy", "#22c55e"
    elif ndvi >= 0.3:
        health, color = "Moderate", "#f59e0b"
    else:
        health, color = "Poor", "#ef4444"

    return {
        "ndvi": ndvi, "health": health, "color": color,
        "source": "Simulated (Environmental Model)",
        "details": {
            "temp_contribution": round(temp_factor, 3),
            "humidity_contribution": round(hum_factor, 3),
            "rainfall_contribution": round(rain_factor, 3),
            "ph_contribution": round(ph_factor, 3)
        }
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GEMINI AI ADVISORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_gemini_advisory(crop, yield_val, price_val, profit, ndvi_data,
                              temperature, humidity, ph, rainfall, n, p, k, weather_info=None, language='en'):
    """Use Gemini AI to generate personalized smart advisory for the farmer."""
    try:
        weather_desc = ""
        if weather_info:
            weather_desc = f"""
Live Weather: {weather_info.get('description', 'N/A')}
Wind Speed: {weather_info.get('wind_speed', 0)} m/s
Pressure: {weather_info.get('pressure', 1013)} hPa
Cloud Cover: {weather_info.get('clouds', 0)}%
Location: {weather_info.get('city', 'Unknown')}, {weather_info.get('country', '')}"""

        lang_instruction = ""
        if language == 'as':
            lang_instruction = "\n\nIMPORTANT: You MUST respond ENTIRELY in Assamese language (অসমীয়া ভাষা). Use proper Assamese script. Do NOT use Bengali. All text including titles, messages, tips, and summaries must be in accurate Assamese."

        prompt = f"""You are an expert agricultural advisor for marginal farmers in India. Based on the following data, provide actionable, practical farming advice in a structured format.{lang_instruction}

CROP DATA:
- Recommended Crop: {crop}
- Predicted Yield: {yield_val} tons/hectare
- Market Price: ₹{price_val}/quintal
- Expected Profit: ₹{profit}/hectare

SOIL DATA:
- Nitrogen (N): {n} kg/ha
- Phosphorus (P): {p} kg/ha
- Potassium (K): {k} kg/ha
- Soil pH: {ph}

WEATHER DATA:
- Temperature: {temperature}°C
- Humidity: {humidity}%
- Rainfall: {rainfall} mm/month
{weather_desc}

SATELLITE DATA:
- NDVI: {ndvi_data.get('ndvi', 'N/A')}
- Crop Health: {ndvi_data.get('health', 'N/A')}
- Data Source: {ndvi_data.get('source', 'N/A')}

Provide your advisory in the following JSON format (return ONLY the JSON, no markdown):
{{
    "advisories": [
        {{
            "icon": "<emoji>",
            "severity": "critical|warning|good|info",
            "title": "<short title>",
            "message": "<detailed practical advice, 1-2 sentences>"
        }}
    ],
    "seasonal_tip": "<one key seasonal recommendation>",
    "market_insight": "<one market-related insight>",
    "overall_summary": "<2-3 sentence summary of the farming recommendation>"
}}

Provide 5-8 actionable advisories covering: soil health, water management, pest/disease prevention, fertilizer schedule, market timing, and crop management. Keep advice practical for small/marginal farmers with limited resources."""

        resp = gemini_request(prompt, temperature=0.7, max_tokens=1500)

        if resp is None or resp.status_code != 200:
            return None

        result = resp.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]

        # Clean up JSON from potential markdown
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        advisory_data = json.loads(text)
        advisory_data["source"] = "Gemini AI"
        return advisory_data

    except json.JSONDecodeError as e:
        print(f"⚠️ Gemini response parse error: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        return None


def generate_fallback_advisory(crop, ndvi_data, temperature, humidity, ph, rainfall, n, p, k):
    """Fallback advisory when Gemini is unavailable."""
    advisories = []

    if ndvi_data["ndvi"] < 0.3:
        advisories.append({"icon": "🔴", "severity": "critical", "title": "Low NDVI Alert",
            "message": f"NDVI is {ndvi_data['ndvi']}. Apply foliar spray with micronutrients (Zinc 0.5% + Boron 0.2%) immediately."})
    elif ndvi_data["ndvi"] < 0.6:
        advisories.append({"icon": "🟡", "severity": "warning", "title": "Moderate Vegetation",
            "message": f"NDVI is {ndvi_data['ndvi']}. Consider balanced NPK fertilizer to boost growth."})
    else:
        advisories.append({"icon": "🟢", "severity": "good", "title": "Healthy Vegetation",
            "message": f"NDVI is {ndvi_data['ndvi']}. Crop is healthy. Maintain current practices."})

    if rainfall < 50:
        advisories.append({"icon": "💧", "severity": "critical", "title": "Water Deficit",
            "message": "Very low rainfall. Set up drip irrigation. Consider mulching to retain moisture."})
    elif rainfall > 250:
        advisories.append({"icon": "🌊", "severity": "warning", "title": "Excess Rainfall",
            "message": "Excessive rainfall. Ensure drainage. Watch for waterlogging and fungal diseases."})

    if ph < 5.5:
        advisories.append({"icon": "⚗️", "severity": "warning", "title": "Acidic Soil",
            "message": f"Soil pH is {ph}. Apply lime @ 2-4 tonnes/ha."})
    elif ph > 7.5:
        advisories.append({"icon": "⚗️", "severity": "warning", "title": "Alkaline Soil",
            "message": f"Soil pH is {ph}. Apply gypsum @ 2-5 tonnes/ha."})

    if n < 30:
        advisories.append({"icon": "🧪", "severity": "warning", "title": "Low Nitrogen",
            "message": f"N is {n} kg/ha. Apply Urea @ 50-100 kg/ha."})
    if p < 20:
        advisories.append({"icon": "🧪", "severity": "warning", "title": "Low Phosphorus",
            "message": f"P is {p} kg/ha. Apply DAP @ 50-75 kg/ha."})
    if k < 20:
        advisories.append({"icon": "🧪", "severity": "warning", "title": "Low Potassium",
            "message": f"K is {k} kg/ha. Apply MOP @ 40-60 kg/ha."})

    if temperature > 38:
        advisories.append({"icon": "🌡️", "severity": "critical", "title": "Heat Stress",
            "message": f"Temperature is {temperature}°C. Use shade nets and increase irrigation."})
    if humidity > 85:
        advisories.append({"icon": "💨", "severity": "warning", "title": "High Humidity",
            "message": f"Humidity is {humidity}%. Risk of fungal diseases. Apply preventive fungicide."})

    return {
        "advisories": advisories,
        "seasonal_tip": "Plan your sowing based on local monsoon forecasts.",
        "market_insight": "Check local mandi prices before harvesting.",
        "overall_summary": f"Based on your conditions, {crop.title()} is recommended. Monitor soil nutrients and weather closely.",
        "source": "Rule-Based System"
    }


def get_feature_importance(model, feature_names):
    if hasattr(model, 'feature_importances_'):
        return [{"feature": name, "importance": round(float(imp), 4)}
                for name, imp in zip(feature_names, model.feature_importances_)]
    return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ═════════════════════ AUTHENTICATION ROUTES ═════════════════════
@app.route("/api/login", methods=["POST"])
def login():
    """User login endpoint"""
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if email in MOCK_USERS and MOCK_USERS[email]["password"] == password:
        session["user_email"] = email
        user_info = MOCK_USERS[email].copy()
        user_info.pop("password", None)
        return jsonify({
            "success": True,
            "message": f"Welcome, {user_info['farmer_name']}!",
            "user": user_info
        }), 200
    
    return jsonify({
        "success": False,
        "message": "Invalid email or password"
    }), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    """User logout endpoint"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@app.route("/api/check-session", methods=["GET"])
def check_session():
    """Check if user is logged in"""
    if "user_email" in session:
        user_email = session["user_email"]
        user_info = MOCK_USERS[user_email].copy()
        user_info.pop("password", None)
        return jsonify({
            "logged_in": True,
            "user": user_info
        }), 200
    return jsonify({"logged_in": False}), 200


# ═════════════════════ FARM DATA ROUTES ═════════════════════
@app.route("/api/farm/info", methods=["GET"])
@require_login
def get_farm_info():
    """Get farmer's farm information"""
    user_email = get_user_email()
    if user_email not in FARM_DATA:
        return jsonify({"error": "Farm data not found"}), 404
    
    farm_data = FARM_DATA[user_email]
    user_info = MOCK_USERS[user_email].copy()
    user_info.pop("password", None)
    
    return jsonify({
        "farmer": user_info,
        "farm": farm_data
    }), 200


@app.route("/api/farm/crops", methods=["GET"])
@require_login
def get_farm_crops():
    """Get all crops on the farm"""
    user_email = get_user_email()
    if user_email not in FARM_DATA:
        return jsonify({"error": "Farm data not found"}), 404
    
    crops = FARM_DATA[user_email].get("crops", [])
    return jsonify({
        "total_crops": len(crops),
        "crops": crops
    }), 200


@app.route("/api/farm/crop/<crop_id>", methods=["GET"])
@require_login
def get_crop_detail(crop_id):
    """Get detailed information about a specific crop"""
    user_email = get_user_email()
    if user_email not in FARM_DATA:
        return jsonify({"error": "Farm data not found"}), 404
    
    crops = FARM_DATA[user_email].get("crops", [])
    crop = next((c for c in crops if c["id"] == crop_id), None)
    
    if not crop:
        return jsonify({"error": "Crop not found"}), 404
    
    return jsonify(crop), 200


@app.route("/api/farm/crop/add", methods=["POST"])
@require_login
def add_crop():
    """Add a new crop to the farm"""
    user_email = get_user_email()
    if user_email not in FARM_DATA:
        return jsonify({"error": "Farm data not found"}), 404
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["name", "area", "planting_date", "expected_harvest", "nitrogen", "phosphorus", "potassium", "soil_ph"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Create new crop entry
    crop_id = f"crop_{int(time.time() * 1000)}"
    new_crop = {
        "id": crop_id,
        "name": data.get("name"),
        "area": float(data.get("area")),
        "planting_date": data.get("planting_date"),
        "expected_harvest": data.get("expected_harvest"),
        "nitrogen": float(data.get("nitrogen")),
        "phosphorus": float(data.get("phosphorus")),
        "potassium": float(data.get("potassium")),
        "soil_ph": float(data.get("soil_ph")),
        "status": "Just Added"
    }
    
    # Add to farm data
    FARM_DATA[user_email]["crops"].append(new_crop)
    
    # Check if total area exceeds available land
    total_area = sum(c["area"] for c in FARM_DATA[user_email]["crops"])
    available_land = FARM_DATA[user_email]["total_land"]
    
    if total_area > available_land:
        FARM_DATA[user_email]["crops"].pop()  # Remove the crop we just added
        return jsonify({
            "error": f"Total area ({total_area}ha) exceeds available land ({available_land}ha)"
        }), 400
    
    return jsonify({
        "success": True,
        "message": f"{new_crop['name']} added successfully!",
        "crop": new_crop
    }), 201


@app.route("/api/farm/crop/<crop_id>/delete", methods=["DELETE"])
@require_login
def delete_crop(crop_id):
    """Delete a crop from the farm"""
    user_email = get_user_email()
    if user_email not in FARM_DATA:
        return jsonify({"error": "Farm data not found"}), 404
    
    crops = FARM_DATA[user_email].get("crops", [])
    crop_index = next((i for i, c in enumerate(crops) if c["id"] == crop_id), None)
    
    if crop_index is None:
        return jsonify({"error": "Crop not found"}), 404
    
    deleted_crop = crops.pop(crop_index)
    return jsonify({
        "success": True,
        "message": f"{deleted_crop['name']} deleted successfully!",
        "deleted_crop": deleted_crop
    }), 200


@app.route("/api/farm/crop/<crop_id>/analyze", methods=["POST"])
@require_login
def analyze_crop(crop_id):
    """Run analysis on a specific crop - This is where the agent/analysis will be used"""
    user_email = get_user_email()
    if user_email not in FARM_DATA:
        return jsonify({"error": "Farm data not found"}), 404
    
    crops = FARM_DATA[user_email].get("crops", [])
    crop = next((c for c in crops if c["id"] == crop_id), None)
    
    if not crop:
        return jsonify({"error": "Crop not found"}), 404
    
    # Get location for weather and satellite data
    user_info = MOCK_USERS[user_email]
    lat = user_info.get("latitude", 19.8967)
    lon = user_info.get("longitude", 73.7754)
    
    # Fetch weather data
    weather_data = fetch_weather(lat, lon)
    
    # Prepare core inputs from crop data
    core_inputs = {
        "N": crop.get("nitrogen", INPUT_DEFAULTS["N"]),
        "P": crop.get("phosphorus", INPUT_DEFAULTS["P"]),
        "K": crop.get("potassium", INPUT_DEFAULTS["K"]),
        "Temperature": weather_data.get("temperature", INPUT_DEFAULTS["Temperature"]) if weather_data else INPUT_DEFAULTS["Temperature"],
        "Humidity": weather_data.get("humidity", INPUT_DEFAULTS["Humidity"]) if weather_data else INPUT_DEFAULTS["Humidity"],
        "pH": crop.get("soil_ph", INPUT_DEFAULTS["pH"]),
        "Rainfall": weather_data.get("rainfall", INPUT_DEFAULTS["Rainfall"]) if weather_data else INPUT_DEFAULTS["Rainfall"],
    }
    
    # Get NDVI data
    ndvi_data = fetch_planet_ndvi(lat, lon)
    if not ndvi_data:
        ndvi_data = compute_ndvi_simulated(
            core_inputs["Temperature"],
            core_inputs["Humidity"],
            core_inputs["Rainfall"],
            core_inputs["pH"]
        )
    
    # Make predictions for the current crop
    crop_result = predict_crop_recommendation(core_inputs)
    pipeline_crop, fallback_msg = select_pipeline_crop(crop_result)
    crop_index = resolve_crop_index(pipeline_crop)
    
    yield_kg_per_ha, yield_tons_per_ha = predict_yield_tons(core_inputs, crop_index or 0)
    price_per_quintal, msp, price_data = predict_price_per_quintal(
        {},
        crop.get("name"),
        crop_index or 0
    )
    profit, price_per_ton = calculate_profit(yield_tons_per_ha, price_per_quintal)
    
    # Get advisory (Gemini or rule-based)
    advisory = generate_gemini_advisory(
        crop.get("name"),
        yield_tons_per_ha,
        price_per_quintal,
        profit,
        ndvi_data,
        core_inputs["Temperature"],
        core_inputs["Humidity"],
        core_inputs["pH"],
        core_inputs["Rainfall"],
        core_inputs["N"],
        core_inputs["P"],
        core_inputs["K"],
        weather_data,
        'en'
    )
    
    if not advisory:
        advisory = generate_fallback_advisory(
            crop.get("name"),
            ndvi_data,
            core_inputs["Temperature"],
            core_inputs["Humidity"],
            core_inputs["pH"],
            core_inputs["Rainfall"],
            core_inputs["N"],
            core_inputs["P"],
            core_inputs["K"]
        )
    
    return jsonify({
        "crop": crop,
        "analysis": {
            "crop_recommendation": crop_result,
            "yield": {
                "kg_per_ha": yield_kg_per_ha,
                "tons_per_ha": yield_tons_per_ha
            },
            "pricing": {
                "price_per_quintal": price_per_quintal,
                "price_per_ton": price_per_ton,
                "msp": msp,
                "profit": profit
            },
            "satellite": ndvi_data,
            "weather": weather_data,
            "advisory": advisory
        }
    }), 200

@app.route("/")
def home():
    """Home — redirect to dashboard if logged in, otherwise show login."""
    from flask import redirect, url_for
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return send_from_directory(app.template_folder, "login.html")


@app.route("/login")
def login_page():
    """Login page"""
    return send_from_directory(app.template_folder, "login.html")


@app.route("/dashboard")
def dashboard():
    """Farm dashboard"""
    if "user_email" not in session:
        return send_from_directory(app.template_folder, "login.html")
    return send_from_directory(app.template_folder, "dashboard.html")

@app.route("/analysis")
def analysis():
    """Comprehensive analysis page"""
    if "user_email" not in session:
        return send_from_directory(app.template_folder, "login.html")
    return send_from_directory(app.template_folder, "index.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/api/crops", methods=["GET"])
def get_crops():
    return jsonify({"crops": CROP_CLASSES})


@app.route("/api/weather", methods=["POST"])
def weather_endpoint():
    """Fetch live weather for given coordinates."""
    try:
        data = request.get_json(silent=True) or {}
        lat_value = data.get("latitude", data.get("lat"))
        lon_value = data.get("longitude", data.get("lon"))
        if lat_value is None or lon_value is None:
            return jsonify({
                "success": False,
                "error": "Latitude and longitude are required"
            }), 400

        lat = float(lat_value)
        lon = float(lon_value)
        weather = fetch_weather(lat, lon)
        if weather:
            return jsonify({"success": True, **weather})
        return jsonify({"success": False, "error": "Could not fetch weather"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/predict", methods=["POST"])
def predict():
    """Main prediction endpoint with standardized feature flow and units."""
    try:
        data = request.get_json(silent=True) or {}
        mode = str(data.get("mode", "manual")).lower()

        lat = data.get("latitude")
        lon = data.get("longitude")
        lat = None if lat in (None, "") else safe_float(lat, 0.0)
        lon = None if lon in (None, "") else safe_float(lon, 0.0)

        weather_info = None
        if mode == "auto" and lat is not None and lon is not None:
            weather_info = fetch_weather(lat, lon)
            if not weather_info:
                return jsonify({"success": False, "error": "Could not fetch weather data"}), 500

        core_inputs = normalize_core_inputs(data, weather_info)
        crop_result = predict_crop_recommendation(core_inputs)
        crop_name = crop_result["name"]
        pipeline_crop_name, pipeline_note = select_pipeline_crop(crop_result)
        crop_index = resolve_crop_index(pipeline_crop_name)

        yield_kg_per_ha, yield_tons_per_ha = predict_yield_tons(core_inputs, crop_index)
        price_per_quintal, msp, market_inputs = predict_price_per_quintal(data, pipeline_crop_name, crop_index)
        profit, price_per_ton = calculate_profit(yield_tons_per_ha, price_per_quintal)

        if lat is not None and lon is not None:
            ndvi_data = fetch_planet_ndvi(lat, lon) or compute_ndvi_simulated(
                core_inputs["Temperature"], core_inputs["Humidity"], core_inputs["Rainfall"], core_inputs["pH"]
            )
        else:
            ndvi_data = compute_ndvi_simulated(
                core_inputs["Temperature"], core_inputs["Humidity"], core_inputs["Rainfall"], core_inputs["pH"]
            )

        risk_data = calculate_risk(
            ndvi_data,
            core_inputs["Rainfall"],
            price_per_quintal,
            msp,
            core_inputs["Temperature"],
            core_inputs["Humidity"],
        )

        advisory_data = build_rule_based_advisory(
            pipeline_crop_name,
            crop_result,
            yield_tons_per_ha,
            price_per_quintal,
            msp,
            profit,
            core_inputs["Rainfall"],
            ndvi_data,
            risk_data,
        )

        language = data.get("language", "en")
        ai_advisory = generate_gemini_advisory(
            pipeline_crop_name,
            yield_tons_per_ha,
            price_per_quintal,
            profit,
            ndvi_data,
            core_inputs["Temperature"],
            core_inputs["Humidity"],
            core_inputs["pH"],
            core_inputs["Rainfall"],
            core_inputs["N"],
            core_inputs["P"],
            core_inputs["K"],
            weather_info,
            language=language,
        )
        if ai_advisory:
            merged_advisories = list(advisory_data["advisories"])
            for item in ai_advisory.get("advisories", []):
                if len(merged_advisories) >= 8:
                    break
                merged_advisories.append(item)
            advisory_data["advisories"] = merged_advisories
            advisory_data["seasonal_tip"] = ai_advisory.get("seasonal_tip", advisory_data["seasonal_tip"])
            advisory_data["market_insight"] = ai_advisory.get("market_insight", advisory_data["market_insight"])
            advisory_data["overall_summary"] = ai_advisory.get("overall_summary", advisory_data["overall_summary"])
            advisory_data["source"] = "Rule-Based + Gemini AI"

        crop_importance = get_feature_importance(
            crop_model,
            feature_names_for(crop_model, ["N", "P", "K", "Temperature", "Humidity", "pH", "Rainfall"]),
        )
        yield_importance = get_feature_importance(
            yield_model,
            feature_names_for(yield_model, ["Crop_Index", "N", "P", "K", "Temperature", "Humidity", "pH", "Rainfall"]),
        )

        market_timing = market_decision(price_per_quintal, msp, pipeline_crop_name)
        ndvi_timeline = generate_ndvi_timeline(ndvi_data["ndvi"], core_inputs["Temperature"], core_inputs["Rainfall"])
        alerts = generate_alerts(
            ndvi_data,
            core_inputs["Rainfall"],
            price_per_quintal,
            msp,
            core_inputs["Temperature"],
            core_inputs["Humidity"],
            core_inputs["pH"],
            risk_data,
        )

        response = {
            "success": True,
            "mode": mode,
            "crop": {
                "name": crop_name.title(),
                "confidence": crop_result["confidence"],
                "display_confidence": crop_result["display_confidence"],
                "confidence_rating": crop_result["confidence_rating"],
                "low_confidence_message": "Low confidence recommendation" if crop_result["low_confidence"] else None,
                "pipeline_crop_name": pipeline_crop_name.title(),
                "pipeline_note": pipeline_note,
                "top_crops": crop_result["top_crops"],
            },
            "yield": {
                "value": yield_tons_per_ha,
                "unit": "tons/hectare",
                "raw_kg_per_hectare": round(yield_kg_per_ha, 2),
            },
            "price": {
                "value": price_per_quintal,
                "unit": "INR/quintal",
                "msp": round(msp, 2),
                "price_per_ton": round(price_per_ton, 2),
            },
            "profit": {"value": profit, "unit": "INR/hectare"},
            "ndvi": ndvi_data,
            "risk": risk_data,
            "advisory": advisory_data,
            "feature_importance": {"crop": crop_importance, "yield": yield_importance},
            "weather": weather_info,
            "inputs": {
                "N": core_inputs["N"],
                "P": core_inputs["P"],
                "K": core_inputs["K"],
                "temperature": core_inputs["Temperature"],
                "humidity": core_inputs["Humidity"],
                "ph": core_inputs["pH"],
                "rainfall": core_inputs["Rainfall"],
            },
            "market_inputs": market_inputs,
            "location": {"latitude": lat, "longitude": lon} if lat is not None and lon is not None else None,
            "market_timing": market_timing,
            "ndvi_timeline": ndvi_timeline,
            "alerts": alerts,
            "summary": {
                "crop": crop_name.title(),
                "confidence": round(crop_result["confidence"] / 100.0, 4),
                "recommendation_score": round(crop_result["display_confidence"] / 100.0, 4),
                "yield_t_per_ha": yield_tons_per_ha,
                "price_per_quintal": price_per_quintal,
                "profit": profit,
                "risk": risk_data["level"],
                "advisory": advisory_data["advisories"],
            },
        }
        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


def market_decision(price, msp, crop):
    """Determine market timing — Sell Now / Hold / Neutral."""
    ratio = price / msp if msp > 0 else 1.0

    if ratio >= 1.25:
        return {
            "decision": "Hold",
            "badge": "🟢",
            "color": "#22c55e",
            "reason": f"Price (₹{price:,.0f}) is {((ratio-1)*100):.0f}% above MSP (₹{msp:,.0f}). Market is favorable — hold for even better prices.",
            "confidence": min(95, int(50 + ratio * 20))
        }
    elif ratio >= 1.0:
        return {
            "decision": "Neutral",
            "badge": "🟡",
            "color": "#f59e0b",
            "reason": f"Price (₹{price:,.0f}) is near MSP (₹{msp:,.0f}). Monitor market trends before deciding.",
            "confidence": min(85, int(40 + ratio * 20))
        }
    elif ratio >= 0.85:
        return {
            "decision": "Sell Now",
            "badge": "🔴",
            "color": "#ef4444",
            "reason": f"Price (₹{price:,.0f}) is {((1-ratio)*100):.0f}% below MSP (₹{msp:,.0f}). Sell at MSP via government procurement to avoid losses.",
            "confidence": min(90, int(60 + (1-ratio) * 100))
        }
    else:
        return {
            "decision": "Sell Now",
            "badge": "🔴",
            "color": "#ef4444",
            "reason": f"Price (₹{price:,.0f}) is significantly below MSP (₹{msp:,.0f}). Sell immediately at MSP or store if possible.",
            "confidence": min(95, int(70 + (1-ratio) * 80))
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RISK ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calculate_risk(ndvi_data, rainfall, price, msp, temperature, humidity):
    """Calculate farming risk with fixed rainfall bands and NDVI override."""
    reasons = []
    factors = []
    extreme_condition = False
    ndvi_val = safe_float(ndvi_data.get("ndvi"), 0.5)
    price_ratio = price / msp if msp > 0 else 1.0

    if rainfall < 50:
        rainfall_level = "High"
        rainfall_score = 75
        extreme_condition = True
        reasons.append("Rainfall below 50 mm indicates drought risk.")
        factors.append({"factor": "Water Supply", "level": "Critical", "score": rainfall_score, "color": "#ef4444"})
    elif rainfall <= 100:
        rainfall_level = "Medium"
        rainfall_score = 45
        reasons.append("Rainfall is between 50 and 100 mm, so irrigation planning is important.")
        factors.append({"factor": "Water Supply", "level": "Warning", "score": rainfall_score, "color": "#f59e0b"})
    else:
        rainfall_level = "Low"
        rainfall_score = 20
        factors.append({"factor": "Water Supply", "level": "Good", "score": rainfall_score, "color": "#22c55e"})

    ndvi_penalty = 0
    if ndvi_val < 0.3:
        ndvi_penalty = 20
        extreme_condition = True
        reasons.append("NDVI is very low, showing crop stress.")
        factors.append({"factor": "Crop Health", "level": "Critical", "score": 20, "color": "#ef4444"})
    elif ndvi_val < 0.5:
        ndvi_penalty = 10
        reasons.append("NDVI is below the healthy range.")
        factors.append({"factor": "Crop Health", "level": "Warning", "score": 10, "color": "#f59e0b"})
    else:
        factors.append({"factor": "Crop Health", "level": "Good", "score": 0, "color": "#22c55e"})

    market_penalty = 0
    if price_ratio < 0.85:
        market_penalty = 15
        reasons.append("Market price is well below MSP.")
        factors.append({"factor": "Market Price", "level": "Critical", "score": 15, "color": "#ef4444"})
    elif price_ratio < 1.0:
        market_penalty = 8
        reasons.append("Market price is slightly below MSP.")
        factors.append({"factor": "Market Price", "level": "Warning", "score": 8, "color": "#f59e0b"})
    else:
        factors.append({"factor": "Market Price", "level": "Good", "score": 0, "color": "#22c55e"})

    weather_penalty = 0
    if temperature >= EXTREME_WEATHER_LIMITS["high_temp"] or temperature <= EXTREME_WEATHER_LIMITS["low_temp"]:
        weather_penalty += 10
        extreme_condition = True
        reasons.append("Temperature is in an extreme range for crop growth.")
        factors.append({"factor": "Temperature", "level": "Critical", "score": 10, "color": "#ef4444"})
    else:
        factors.append({"factor": "Temperature", "level": "Good", "score": 0, "color": "#22c55e"})

    if humidity >= EXTREME_WEATHER_LIMITS["high_humidity"]:
        weather_penalty += 5
        reasons.append("Humidity is high, which may increase disease pressure.")
        factors.append({"factor": "Humidity", "level": "Warning", "score": 5, "color": "#f59e0b"})
    else:
        factors.append({"factor": "Humidity", "level": "Good", "score": 0, "color": "#22c55e"})

    risk_score = int(clamp(rainfall_score + ndvi_penalty + market_penalty + weather_penalty, 0, 100))
    if risk_score >= 65 or extreme_condition:
        level = "High"
    elif risk_score >= 35 or rainfall_level == "Medium":
        level = "Medium"
    else:
        level = "Low"

    if not reasons:
        reasons.append("All primary conditions are within the normal range.")

    return {
        "level": level,
        "score": risk_score,
        "badge": {"High": "red", "Medium": "amber", "Low": "green"}[level],
        "color": {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}[level],
        "reasons": reasons,
        "factors": factors
    }


def generate_ndvi_timeline(current_ndvi, temperature, rainfall):
    """Generate a realistic 12-month NDVI timeline for crop health trend."""
    import random
    random.seed(int(current_ndvi * 1000 + temperature))

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    base = max(0.15, current_ndvi - 0.25)

    # Simulate seasonal growth pattern
    seasonal = [0.75, 0.70, 0.78, 0.85, 0.90, 0.82, 0.88, 0.92, 0.85, 0.80, 0.72, 0.68]
    timeline = []
    for i, month in enumerate(months):
        val = base + (current_ndvi - base) * seasonal[i] + random.uniform(-0.05, 0.05)
        val = round(max(0.05, min(0.98, val)), 3)
        timeline.append({"month": month, "ndvi": val})

    return timeline


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALERT SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_alerts(ndvi_data, rainfall, price, msp, temperature, humidity, ph, risk_data):
    """Generate real-time alerts based on thresholds."""
    alerts = []

    ndvi_val = ndvi_data.get("ndvi", 0.5)
    if ndvi_val < 0.3:
        alerts.append({"type": "critical", "icon": "🚨", "title": "Low Crop Health Detected",
            "message": f"NDVI is {ndvi_val} (critical). Immediate intervention required — apply foliar spray and micronutrients."})
    elif ndvi_val < 0.5:
        alerts.append({"type": "warning", "icon": "⚠️", "title": "Declining Crop Health",
            "message": f"NDVI is {ndvi_val}. Monitor closely and consider nutrient supplementation."})

    if rainfall < 50:
        alerts.append({"type": "critical", "icon": "🏜️", "title": "Severe Drought Conditions",
            "message": f"Rainfall is only {rainfall}mm. Set up emergency irrigation immediately."})
    elif rainfall > 300:
        alerts.append({"type": "warning", "icon": "🌊", "title": "Flood Risk — Excess Rainfall",
            "message": f"Rainfall is {rainfall}mm. Ensure drainage. Watch for waterlogging."})

    if price < msp * 0.9:
        alerts.append({"type": "warning", "icon": "📉", "title": "Price Below MSP",
            "message": f"Market price (₹{price:,.0f}) is below MSP (₹{msp:,.0f}). Consider selling through government procurement."})

    if temperature > 40:
        alerts.append({"type": "critical", "icon": "🌡️", "title": "Extreme Heat Alert",
            "message": f"Temperature is {temperature}°C. Provide shade and increase irrigation frequency."})
    elif temperature < 5:
        alerts.append({"type": "critical", "icon": "❄️", "title": "Frost Warning",
            "message": f"Temperature is {temperature}°C. Cover crops with mulch or plastic sheets."})

    if ph < 5.5:
        alerts.append({"type": "warning", "icon": "⚗️", "title": "Acidic Soil Alert",
            "message": f"Soil pH is {ph}. Apply lime @ 2-4 tonnes/hectare to correct acidity."})
    elif ph > 7.5:
        alerts.append({"type": "warning", "icon": "⚗️", "title": "Alkaline Soil Alert",
            "message": f"Soil pH is {ph}. Apply gypsum @ 2-5 tonnes/hectare."})

    if risk_data["level"] == "High":
        alerts.append({"type": "critical", "icon": "🔴", "title": "High Risk Farming Conditions",
            "message": f"Overall risk score: {risk_data['score']}/100. {'; '.join(risk_data['reasons'][:2])}"})

    if not alerts:
        alerts.append({"type": "info", "icon": "✅", "title": "All Systems Normal",
            "message": "No critical alerts. All farming parameters are within acceptable ranges."})

    return alerts


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF REPORT DOWNLOAD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/api/report", methods=["POST"])
def generate_report():
    """Generate a downloadable text report."""
    try:
        data = request.get_json()
        lines = []
        lines.append("=" * 60)
        lines.append("   SMART FARMING DECISION SYSTEM — ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"   Generated: {__import__('datetime').datetime.now().strftime('%d-%b-%Y %H:%M')}")
        lines.append("")
        lines.append("── CROP RECOMMENDATION ──────────────────────────────")
        lines.append(f"   Recommended Crop     : {data.get('crop', 'N/A')}")
        lines.append(f"   Confidence           : {data.get('confidence', 'N/A')}%")
        lines.append("")
        lines.append("── YIELD & MARKET ──────────────────────────────────")
        lines.append(f"   Yield Prediction     : {data.get('yield', 'N/A')} tons/hectare")
        lines.append(f"   Market Price         : ₹{data.get('price', 'N/A')}/quintal")
        lines.append(f"   MSP                  : ₹{data.get('msp', 'N/A')}/quintal")
        lines.append(f"   Expected Profit      : ₹{data.get('profit', 'N/A')}/hectare")
        lines.append(f"   Market Timing        : {data.get('market_timing', 'N/A')}")
        lines.append("")
        lines.append("── CROP HEALTH ─────────────────────────────────────")
        lines.append(f"   NDVI                 : {data.get('ndvi', 'N/A')}")
        lines.append(f"   NDVI Source          : {data.get('ndvi_source', 'N/A')}")
        lines.append(f"   Risk Level           : {data.get('risk_level', 'N/A')}")
        lines.append(f"   Risk Score           : {data.get('risk_score', 'N/A')}/100")
        lines.append("")
        lines.append("── ENVIRONMENTAL DATA ──────────────────────────────")
        lines.append(f"   Temperature          : {data.get('temperature', 'N/A')}°C")
        lines.append(f"   Humidity             : {data.get('humidity', 'N/A')}%")
        lines.append(f"   Rainfall             : {data.get('rainfall', 'N/A')} mm")
        lines.append(f"   Soil pH              : {data.get('ph', 'N/A')}")
        lines.append(f"   N / P / K            : {data.get('npk', 'N/A')} kg/ha")
        lines.append("")
        lines.append("── ADVISORIES ──────────────────────────────────────")
        for adv in data.get("advisories", []):
            lines.append(f"   {adv.get('icon','')} {adv.get('title','')}: {adv.get('message','')}")
        lines.append("")
        lines.append("── ALERTS ──────────────────────────────────────────")
        for alert in data.get("alerts", []):
            lines.append(f"   {alert.get('icon','')} {alert.get('title','')}: {alert.get('message','')}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("   © 2026 Smart Farming AI | Hackathon Project")
        lines.append("=" * 60)

        report_text = "\n".join(lines)

        return app.response_class(
            response=report_text,
            status=200,
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment; filename=Smart_Farming_Report.txt"}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ndvi", methods=["POST"])
def ndvi_endpoint():
    """NDVI endpoint — tries Planet satellite, falls back to simulation."""
    try:
        data = request.get_json()
        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat and lon:
            ndvi = fetch_planet_ndvi(float(lat), float(lon))
            if ndvi:
                return jsonify({"success": True, **ndvi})

        temperature = float(data.get("temperature", 26))
        humidity = float(data.get("humidity", 70))
        rainfall = float(data.get("rainfall", 150))
        ph = float(data.get("ph", 6.5))
        ndvi = compute_ndvi_simulated(temperature, humidity, rainfall, ph)
        return jsonify({"success": True, **ndvi})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/disease", methods=["POST"])
def disease_endpoint():
    """Plant disease detection from leaf image.

    Primary path : ConvNeXt-V2 (30-class deep learning model)
    Fallback path : colour-channel pixel analysis

    Returns:
        disease         – human-readable disease name
        confidence      – model confidence (0-100)
        severity        – dict with level/color/badge/description
        treatment       – rule-based baseline treatment string
        remedies        – list of specific pesticide / treatment steps (Gemini)
        pesticides      – list of {name, dose, frequency} dicts (Gemini)
        preventive_measures – list of prevention tips (Gemini)
        urgency_note    – how quickly to act (Gemini)
        model           – model name used
        image_preview   – base-64 thumbnail
    """
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image file provided"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        img = Image.open(file.stream).convert("RGB")

        # ── ConvNeXt-V2 inference ──────────────────────────────────────────
        if convnext_model is not None and convnext_transform is not None:
            tensor = convnext_transform(img).unsqueeze(0)  # (1, 3, 224, 224)
            with torch.no_grad():
                logits = convnext_model(tensor)             # (1, num_classes)
                probs  = torch.softmax(logits, dim=1)[0]   # (num_classes,)

            top_idx    = int(probs.argmax().item())
            confidence = round(float(probs[top_idx].item()) * 100, 1)

            # Map index → label (guard against index out of range)
            if top_idx < len(DISEASE_CLASSES):
                raw_label = DISEASE_CLASSES[top_idx]
            else:
                raw_label = f"Class_{top_idx}"

            disease_name = normalize_disease_label(raw_label)
            model_used   = "ConvNeXt-V2 (Deep Learning)"
        else:
            # ── Pixel-analysis fallback ────────────────────────────────────
            img_array = np.array(img)
            r_mean = float(np.mean(img_array[:, :, 0]))
            g_mean = float(np.mean(img_array[:, :, 1]))
            b_mean = float(np.mean(img_array[:, :, 2]))
            green_ratio = g_mean / (r_mean + g_mean + b_mean + 1e-6)
            brown_ratio = r_mean / (g_mean + 1e-6)
            brightness  = (r_mean + g_mean + b_mean) / 3.0

            if green_ratio > 0.38 and brown_ratio < 1.1:
                disease_name = "Healthy Leaf"
                confidence   = round(min(85 + green_ratio * 20, 97.5), 1)
            elif brown_ratio > 1.5:
                disease_name = "Rust Disease" if brightness > 150 else "Leaf Blight"
                confidence   = round(min(70 + brown_ratio * 5, 97.5), 1)
            elif r_mean > g_mean * 1.2:
                disease_name = "Anthracnose"
                confidence   = round(min(72 + (r_mean / g_mean) * 5, 97.5), 1)
            elif brightness < 100:
                disease_name = "Fusarium Wilt"
                confidence   = round(min(68 + (100 - brightness) * 0.2, 97.5), 1)
            elif g_mean < 100:
                disease_name = "Powdery Mildew" if b_mean > g_mean else "Bacterial Leaf Spot"
                confidence   = round(min(65 + (100 - g_mean) * 0.3, 97.5), 1)
            else:
                disease_name = "Mosaic Virus"
                confidence   = round(min(60 + abs(r_mean - g_mean) * 0.5, 97.5), 1)

            model_used = "Pixel Analysis (Fallback)"

        # ── Severity ───────────────────────────────────────────────────────
        is_healthy = "healthy" in disease_name.lower()
        severity   = estimate_severity(confidence, is_healthy)

        # ── Baseline treatment ─────────────────────────────────────────────
        baseline_treatment = treatment_for_disease(disease_name)

        # ── Gemini AI advisory (remedies + preventive measures) ────────────
        gemini_advice = {}
        if not is_healthy:
            gemini_advice = generate_disease_advisory(disease_name, confidence, severity["level"])

        # ── Image thumbnail ────────────────────────────────────────────────
        img_thumbnail = img.copy()
        img_thumbnail.thumbnail((400, 400))
        buffered = io.BytesIO()
        img_thumbnail.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return jsonify({
            "success": True,
            "disease": disease_name,
            "confidence": confidence,
            "severity": severity,
            "treatment": baseline_treatment,
            "remedies": gemini_advice.get("remedies", []),
            "pesticides": gemini_advice.get("pesticides", []),
            "preventive_measures": gemini_advice.get("preventive_measures", []),
            "urgency_note": gemini_advice.get("urgency_note", ""),
            "image_preview": f"data:image/jpeg;base64,{img_base64}",
            "model": model_used,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIVE MANDI PRICES (data.gov.in)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDI_API_KEY = "579b464db66ec23bdd000001857093021f5041a25572411fe89dcd3d"
MANDI_API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# Mapping of our crop names to mandi commodity names
CROP_TO_COMMODITY = {
    'rice': 'Paddy(Dhan)(Common)', 'wheat': 'Wheat', 'maize': 'Maize',
    'cotton': 'Cotton', 'jute': 'Jute', 'lentil': 'Masur Dal',
    'mungbean': 'Green Gram (Moong)(Whole)', 'mothbeans': 'Moth',
    'pigeonpeas': 'Arhar (Tur/Red Gram)(Whole)', 'kidneybeans': 'Rajma',
    'chickpea': 'Bengal Gram(Gram)(Whole)', 'blackgram': 'Black Gram (Urd Beans)(Whole)',
    'coconut': 'Coconut', 'banana': 'Banana', 'mango': 'Mango(Raw-Ripe)',
    'apple': 'Apple', 'grapes': 'Grapes', 'orange': 'Orange',
    'watermelon': 'Water Melon', 'papaya': 'Papaya', 'pomegranate': 'Pomegranate',
    'coffee': 'Coffee', 'muskmelon': 'Musk Melon', 'sugarcane': 'Sugarcane'
}


@app.route("/api/mandi", methods=["POST"])
def mandi_prices():
    """Fetch live mandi prices from data.gov.in API — client-side filtering to avoid API timeout."""
    try:
        data = request.get_json()
        commodity = data.get("commodity", "Rice").strip()
        state = data.get("state", "").strip()
        limit = int(data.get("limit", 15))

        # Map crop name to commodity name
        mapped = CROP_TO_COMMODITY.get(commodity.lower())
        search_terms = [mapped.lower()] if mapped else []
        search_terms.append(commodity.lower())

        params = {
            "api-key": MANDI_API_KEY,
            "format": "json",
            "limit": 500,
            "offset": 0
        }

        # Only use state filter (fast) — skip commodity filter (slow/timeout)
        if state:
            params["filters[state]"] = state

        resp = http_requests.get(MANDI_API_URL, params=params, timeout=25)

        if resp.status_code != 200:
            print(f"⚠️ Mandi API error: {resp.status_code}")
            return jsonify({"success": False, "error": f"Mandi API error: {resp.status_code}"}), 500

        result = resp.json()
        records = result.get("records", [])

        # Client-side commodity filtering (fuzzy match)
        filtered = []
        for rec in records:
            rec_commodity = rec.get("commodity", "").lower()
            if any(term in rec_commodity or rec_commodity in term for term in search_terms):
                filtered.append(rec)

        # If no exact matches, try partial word match
        if not filtered:
            for rec in records:
                rec_commodity = rec.get("commodity", "").lower()
                words = commodity.lower().split()
                if any(w in rec_commodity for w in words if len(w) > 2):
                    filtered.append(rec)

        # Limit results
        filtered = filtered[:limit]

        prices = []
        for rec in filtered:
            prices.append({
                "state": rec.get("state", "—"),
                "district": rec.get("district", "—"),
                "market": rec.get("market", "—"),
                "commodity": rec.get("commodity", "—"),
                "variety": rec.get("variety", "—"),
                "arrival_date": rec.get("arrival_date", "—"),
                "min_price": rec.get("min_price", "—"),
                "max_price": rec.get("max_price", "—"),
                "modal_price": rec.get("modal_price", "—"),
            })

        return jsonify({
            "success": True,
            "total": result.get("total", 0),
            "count": len(prices),
            "prices": prices,
            "commodity_searched": commodity,
            "source": "data.gov.in (National Mandi Portal)"
        })

    except Exception as e:
        print(f"⚠️ Mandi API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DISASTER DECISION ENGINE (Gemini-powered)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/api/disaster", methods=["POST"])
def disaster_engine():
    """Disaster preparedness and response advisory using Gemini AI."""
    try:
        data = request.get_json()
        disaster_type = data.get("disaster_type", "flood")
        crop = data.get("crop", "rice")
        location = data.get("location", "India")
        severity = data.get("severity", "moderate")

        prompt = f"""You are an emergency agricultural disaster response advisor for Indian farmers. A {severity} {disaster_type} is expected or occurring.

CONTEXT:
- Disaster: {disaster_type.upper()} ({severity} severity)
- Current/Planned Crop: {crop}
- Location: {location}

Provide a comprehensive disaster response plan in JSON format (return ONLY the JSON, no markdown):
{{
    "disaster_type": "{disaster_type}",
    "severity": "{severity}",
    "immediate_actions": [
        {{
            "icon": "<emoji>",
            "priority": "immediate|within_24h|within_week",
            "action": "<specific action to take>",
            "detail": "<practical detail>"
        }}
    ],
    "crop_protection": {{
        "can_save": true/false,
        "measures": ["<list of crop protection measures>"],
        "alternative_crops": ["<crops that can be planted after disaster>"],
        "recovery_timeline": "<expected recovery period>"
    }},
    "financial_advisory": {{
        "insurance_claim": "<how to file PMFBY crop insurance claim>",
        "govt_schemes": ["<relevant government disaster relief schemes>"],
        "compensation": "<expected compensation info>"
    }},
    "water_management": "<specific water management advice>",
    "post_disaster": ["<list of post-disaster recovery steps>"],
    "warning_signs": ["<signs to watch for to assess damage>"],
    "helpline": "<relevant helpline numbers>"
}}

Provide 5-8 immediate actions, 3-4 crop protection measures, 2-3 government schemes, and 3-4 post-disaster steps. Keep advice practical, specific for Indian marginal farmers. Include specific quantities, timings, and method names.
"""

        resp = gemini_request(prompt, temperature=0.6, max_tokens=2000)

        if resp is None or resp.status_code != 200:
            return jsonify({"success": False, "error": f"Gemini API error: {resp.status_code if resp else 'no response'}"}), 500

        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()

        disaster_plan = json.loads(text)
        disaster_plan["source"] = "Gemini AI Disaster Engine"
        return jsonify({"success": True, **disaster_plan})

    except json.JSONDecodeError:
        # Return a basic fallback plan
        return jsonify({
            "success": True,
            "disaster_type": disaster_type,
            "severity": severity,
            "source": "Fallback Engine",
            "immediate_actions": [
                {"icon": "🚨", "priority": "immediate", "action": "Evacuate if life-threatening", "detail": "Move to higher ground for floods, shelter for cyclones."},
                {"icon": "📱", "priority": "immediate", "action": "Contact NDRF helpline 011-26107953", "detail": "Report damage for relief coordination."},
                {"icon": "🌾", "priority": "within_24h", "action": "Drain standing water from fields", "detail": "Use pumps if available. Create drainage channels."},
                {"icon": "📋", "priority": "within_24h", "action": "Document crop damage with photos", "detail": "Needed for PMFBY insurance claims."},
                {"icon": "🏦", "priority": "within_week", "action": "Visit nearest agriculture office", "detail": "Apply for crop loss compensation."}
            ],
            "crop_protection": {
                "can_save": severity != "severe",
                "measures": ["Drain excess water immediately", "Apply fungicide after water recedes", "Provide nutrient boost with urea spray"],
                "alternative_crops": ["Short-duration rice", "Vegetables", "Green gram"],
                "recovery_timeline": "2-4 weeks for moderate damage"
            },
            "financial_advisory": {
                "insurance_claim": "File PMFBY claim within 72 hours via crop insurance portal or helpline 1800-200-7710",
                "govt_schemes": ["PM Fasal Bima Yojana", "NDRF Relief", "State Disaster Relief Fund"],
                "compensation": "Compensation varies by state. Contact Block Development Officer."
            },
            "water_management": "Drain fields within 48 hours. Re-level land after water recedes.",
            "post_disaster": ["Assess and document all damage", "Apply lime to neutralize soil acidity", "Re-sow quick-maturing varieties", "Apply foliar fertilizer for recovery"],
            "warning_signs": ["Yellowing of leaves (waterlogging)", "Root rot smell", "Wilting despite wet soil"],
            "helpline": "NDRF: 011-26107953 | Kisan Call Center: 1800-180-1551"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CROP SUITABILITY CHATBOT (Gemini-powered)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/api/chat", methods=["POST"])
def crop_chatbot():
    """AI chatbot for crop suitability and farming questions."""
    try:
        data = request.get_json()
        mode = str(data.get("mode", "manual")).lower()

        lat = data.get("latitude")
        lon = data.get("longitude")
        lat = None if lat in (None, "") else safe_float(lat, 0.0)
        lon = None if lon in (None, "") else safe_float(lon, 0.0)

        weather_info = None
        if mode == "auto" and lat is not None and lon is not None:
            weather_info = fetch_weather(lat, lon)
            if not weather_info:
                return jsonify({"success": False, "error": "Could not fetch weather data"}), 500

        core_inputs = normalize_core_inputs(data, weather_info)
        crop_result = predict_crop_recommendation(core_inputs)
        crop_name = crop_result["name"]
        pipeline_crop_name, pipeline_note = select_pipeline_crop(crop_result)
        crop_index = resolve_crop_index(pipeline_crop_name)

        yield_kg_per_ha, yield_tons_per_ha = predict_yield_tons(core_inputs, crop_index)
        price_per_quintal, msp, market_inputs = predict_price_per_quintal(data, pipeline_crop_name, crop_index)
        profit, price_per_ton = calculate_profit(yield_tons_per_ha, price_per_quintal)

        if lat is not None and lon is not None:
            ndvi_data = fetch_planet_ndvi(lat, lon) or compute_ndvi_simulated(
                core_inputs["Temperature"], core_inputs["Humidity"], core_inputs["Rainfall"], core_inputs["pH"]
            )
        else:
            ndvi_data = compute_ndvi_simulated(
                core_inputs["Temperature"], core_inputs["Humidity"], core_inputs["Rainfall"], core_inputs["pH"]
            )



        return jsonify({
            "success": True,
            "crop": crop_name,
            "yield": {
                "kg_per_ha": yield_kg_per_ha,
                "tons_per_ha": yield_tons_per_ha
            },
            "price": {
                "per_quintal": price_per_quintal,
                "per_ton": price_per_ton,
                "msp": msp,
                "profit": profit
            },
            "ndvi": ndvi_data
        })
    
    except Exception as e:
        print(f"Prediction Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/news", methods=["POST", "GET"])
def get_news():
    """Fetch agricultural news from external API with caching."""
    try:
        # Get parameters from POST body or GET query
        if request.method == "POST":
            data = request.get_json() or {}
        else:
            data = request.args.to_dict()
        
        search_type = data.get("type", "agriculture").lower()  # agriculture, weather, prices, technology, all, assam
        requested_limit = int(data.get("limit", 12))
        limit = max(1, min(requested_limit, 12))
        provider_limit = min(limit, 3)
        use_cache = data.get("cache", True)
        
        # Check cache first (per category)
        import time
        current_time = time.time()
        cache_key = f"{search_type}_news"  # Different cache for each category
        
        if use_cache and cache_key in NEWS_CACHE and (current_time - NEWS_CACHE[cache_key].get("timestamp", 0)) < NEWS_CACHE_DURATION:
            print(f"✅ Returning cached {search_type} news ({current_time - NEWS_CACHE[cache_key]['timestamp']:.0f}s old)")
            articles = NEWS_CACHE[cache_key]["data"]
        else:
            # Define search queries for each category
            search_queries = {
                "agriculture": "agriculture farming crops agriculture news",
                "weather": "weather climate forecasting meteorology",
                "prices": "crop prices commodity market agricultural",
                "technology": "agricultural technology farming innovation AI robotics",
                "assam": "Assam agriculture farming crops weather news kisaan Assamese",
                "all": "agriculture farming crops weather prices technology news"
            }
            
            search_query = search_queries.get(search_type, search_queries["agriculture"])
            
            # Call TheNewsAPI /top endpoint
            params = {
                "api_token": NEWS_API_KEY,
                "language": "en",
                "categories": "business,tech,science,general",
                "search": search_query,
                "limit": provider_limit
            }
            
            print(f"🔍 Fetching {search_type} news from TheNewsAPI...")
            resp = http_requests.get(NEWS_API_URL, params=params, timeout=15)
            
            if resp.status_code != 200:
                error_msg = resp.json().get("error", {}).get("message", f"API Error {resp.status_code}")
                print(f"❌ TheNewsAPI Error: {error_msg}")
                
                return get_mock_news(search_type, limit)
            
            news_data = resp.json()
            articles = news_data.get("data", [])
            
            if not articles:
                return get_mock_news(search_type, limit)
            
            # Cache the results (per category)
            NEWS_CACHE[cache_key] = {"data": articles, "timestamp": current_time}
            print(f"💾 Cached {len(articles)} {search_type} articles")
        
        # Format articles for frontend
        formatted_articles = []
        for article in articles[:limit]:
            # Safely extract fields
            title = article.get("title", "No Title")
            description = article.get("description", article.get("snippet", ""))
            
            # Truncate description to 150 chars
            if description and len(description) > 150:
                description = description[:150] + "..."
            
            formatted_articles.append({
                "title": title,
                "description": description,
                "image": article.get("image_url", ""),
                "link": article.get("url", ""),
                "source": article.get("source", "News"),
                "date": article.get("published_at", ""),
                "category": search_type
            })
        
        print(f"✅ Returning {len(formatted_articles)} formatted articles")
        
        return jsonify({
            "success": True,
            "type": search_type,
            "total": len(formatted_articles),
            "articles": formatted_articles,
            "cached": use_cache and (cache_key in NEWS_CACHE and (current_time - NEWS_CACHE[cache_key].get("timestamp", 0)) < NEWS_CACHE_DURATION)
        })
        
    except Exception as e:
        print(f"❌ News API Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return get_mock_news("agriculture", 12)


@app.route("/api/alternative-crops", methods=["POST"])
def get_alternative_crops():
    """
    Recommend alternative crops based on current conditions.
    Useful when the farmer does not want the primary recommended crop.
    """
    try:
        data = request.get_json(silent=True) or {}
        core_inputs = normalize_core_inputs(data)
        season = data.get("season", "Kharif").lower()
        exclude_crop = data.get("exclude", "").lower()

        feature_names = feature_names_for(
            crop_model,
            ["N", "P", "K", "Temperature", "Humidity", "pH", "Rainfall"]
        )
        features = build_feature_frame(feature_names, core_inputs, INPUT_DEFAULTS)
        probabilities = crop_model.predict_proba(features)[0]

        crop_prob_pairs = list(zip(crop_model.classes_, probabilities))
        crop_prob_pairs.sort(key=lambda item: item[1], reverse=True)

        alternatives = []
        for crop_name, confidence in crop_prob_pairs:
            if str(crop_name).lower() == exclude_crop or len(alternatives) >= 5:
                continue

            pipeline_crop_name = str(crop_name).lower()
            if pipeline_crop_name not in PIPELINE_CROP_CLASSES:
                continue

            crop_index = resolve_crop_index(pipeline_crop_name)
            _, yield_pred = predict_yield_tons(core_inputs, crop_index)
            price_pred, _, _ = predict_price_per_quintal(data, pipeline_crop_name, crop_index)
            estimated_profit, _ = calculate_profit(yield_pred, price_pred)

            alternatives.append({
                "crop": str(crop_name).title(),
                "confidence": f"{confidence*100:.1f}%",
                "confidence_strength": "Strong" if confidence >= 0.70 else "Medium" if confidence >= 0.50 else "Low",
                "estimated_yield": f"{yield_pred:.2f} tons/ha",
                "market_price": f"INR {price_pred:.2f}/quintal",
                "estimated_profit": f"INR {estimated_profit:.0f}/ha",
                "season": season,
                "suitability_score": f"{confidence*100:.0f}/100"
            })

        return jsonify({
            "success": True,
            "alternatives": alternatives,
            "message": f"Found {len(alternatives)} suitable alternatives"
        })

    except Exception as e:
        print(f"Alternative Crops Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Error fetching alternatives"
        }), 500


def get_mock_news(category, limit, region="all"):
    """Return mock agricultural news for demo when API limit is reached."""
    mock_articles = {
        "agriculture": [
            {
                "title": "New Crop Variety Increases Yield by 30%",
                "description": "Scientists develop disease-resistant wheat variant",
                "image": "",
                "link": "#",
                "source": "Agriculture Today",
                "date": "2026-04-28",
                "category": "agriculture"
            },
            {
                "title": "Smart Farming Technology Reduces Water Usage",
                "description": "IoT sensors optimize irrigation in Indian farms",
                "image": "",
                "link": "#",
                "source": "Farm Tech News",
                "date": "2026-04-27",
                "category": "agriculture"
            }
        ],
        "weather": [
            {
                "title": "Monsoon Forecast: Expect Above-Normal Rainfall",
                "description": "IMD predicts good monsoon season for agriculture",
                "image": "",
                "link": "#",
                "source": "Weather Bureau",
                "date": "2026-04-28",
                "category": "weather"
            }
        ],
        "prices": [
            {
                "title": "Rice Prices Rise Amid Global Demand",
                "description": "MSP increase benefits Indian farmers",
                "image": "",
                "link": "#",
                "source": "Market Report",
                "date": "2026-04-28",
                "category": "prices"
            }
        ],
        "technology": [
            {
                "title": "AI Drones for Crop Monitoring Go Mainstream",
                "description": "Affordable drone technology transforms farm management",
                "image": "",
                "link": "#",
                "source": "Tech Innovation",
                "date": "2026-04-26",
                "category": "technology"
            }
        ]
    }
    
    articles = mock_articles.get(category, mock_articles.get("agriculture", []))
    return jsonify({
        "success": True,
        "type": category,
        "total": len(articles),
        "articles": articles[:limit],
        "note": "Demo data - API subscription upgrade required for live news"
    })


if __name__ == "__main__":
    print("\n🌾 Smart Farming Decision System — Hackathon Edition")
    print("━" * 55)
    print(f"📊 ML Models: crop, yield, price ({len(CROP_CLASSES)} crops)")
    print(f"🌿 Disease Detection: {'ConvNeXt-V2 (' + str(len(DISEASE_CLASSES)) + ' classes)' if convnext_model else 'Pixel Analysis fallback'}")
    print(f"🛰️  Planet Satellite API: Active")
    print(f"🌤️  OpenWeatherMap API: Active")
    print(f"🧠 Gemini AI Advisory: Active")
    print(f"🏪 Mandi Prices API: Active")
    print(f"💬 Crop Chatbot: Active")
    print(f"🌊 Disaster Engine: Active")
    print(f"🌐 Server: http://localhost:5000")
    print("━" * 55)
    app.run(debug=False, host="0.0.0.0", port=5000)
