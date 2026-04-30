"""
API Key Validation Script
Tests each API endpoint to verify they're working correctly
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PLANET_API_KEY = os.environ.get("PLANET_API_KEY", "")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")

print("=" * 60)
print("API KEY VALIDATION TEST")
print("=" * 60)

# Test 1: OpenWeatherMap API
print("\n1️⃣  Testing OpenWeatherMap API...")
if WEATHER_API_KEY:
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=28.6139&lon=77.2090&units=metric&appid={WEATHER_API_KEY}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("   ✅ OpenWeatherMap API: WORKING")
            data = response.json()
            print(f"   📍 Location: {data.get('name', 'Unknown')}")
            print(f"   🌡️  Temperature: {data['main']['temp']}°C")
        else:
            print(f"   ❌ OpenWeatherMap API: FAILED - Status {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ OpenWeatherMap API: ERROR - {str(e)}")
else:
    print("   ⚠️  WEATHER_API_KEY not set")

# Test 2: Gemini API
print("\n2️⃣  Testing Gemini API...")
if GEMINI_API_KEY:
    try:
        # Try gemini-2.0-flash first, then fallback to other models
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
        
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": "Hello"}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 100}
            }
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Gemini API: WORKING (Model: {model})")
                break
            elif response.status_code in [400, 404]:
                print(f"   ⚠️  Model {model} not available (trying next...)")
                continue
            else:
                print(f"   ❌ Gemini API ({model}): Status {response.status_code}")
                print(f"   📝 Response: {response.text[:200]}")
                break
    except Exception as e:
        print(f"   ❌ Gemini API: ERROR - {str(e)}")
else:
    print("   ⚠️  GEMINI_API_KEY not set")

# Test 3: News API
print("\n3️⃣  Testing TheNewsAPI...")
if NEWS_API_KEY:
    try:
        url = f"https://api.thenewsapi.com/v1/news/top?domain=agriculture&limit=1&api_token={NEWS_API_KEY}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("   ✅ TheNewsAPI: WORKING")
            data = response.json()
            if data.get('data'):
                print(f"   📰 Latest news: {data['data'][0].get('title', 'Unknown')[:60]}...")
        else:
            print(f"   ❌ TheNewsAPI: FAILED - Status {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ TheNewsAPI: ERROR - {str(e)}")
else:
    print("   ⚠️  NEWS_API_KEY not set")

# Test 4: Planet API
print("\n4️⃣  Testing Planet API...")
if PLANET_API_KEY:
    try:
        url = "https://api.planet.com/data/v1/assets/search"
        headers = {"Authorization": f"api_key {PLANET_API_KEY}"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print("   ✅ Planet API: WORKING")
        elif response.status_code == 401:
            print("   ❌ Planet API: UNAUTHORIZED - Invalid API key")
        else:
            print(f"   ❌ Planet API: FAILED - Status {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Planet API: ERROR - {str(e)}")
else:
    print("   ⚠️  PLANET_API_KEY not set")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
Notes:
- Replace expired API keys with valid ones
- Ensure APIs are enabled in their respective dashboards
- Check for geographic/IP restrictions
""")
