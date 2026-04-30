/**
 * Smart Farming Decision System — Frontend JS
 * GPS + Weather + Satellite + Gemini AI + ML Models
 */

// ━━━ STATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let currentMode = 'auto';
let userLocation = null;
let currentCharts = {};
let diseaseFile = null;
let lastPredictionData = null;
let lastNDVITimeline = null;
let currentLang = localStorage.getItem('lang') || 'en';
let isRecording = false;
let speechRecognition = null;

// ━━━ ASSAMESE TRANSLATIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const i18n = {
    // Header
    'app_title': { en: 'Smart Farming', as: 'স্মাৰ্ট কৃষি' },
    'app_subtitle': { en: 'AI Decision System for Marginal Farmers', as: 'ক্ষুদ্ৰ কৃষকৰ বাবে AI সিদ্ধান্ত ব্যৱস্থা' },
    'live': { en: 'Live', as: 'লাইভ' },
    'ml_models': { en: 'ML Models', as: 'ML মডেল' },
    'satellite': { en: 'Satellite', as: 'উপগ্ৰহ' },
    'weather': { en: 'Weather', as: 'বতৰ' },
    'gemini_ai': { en: 'Gemini AI', as: 'জেমিনি AI' },
    // Mode tabs
    'smart_mode': { en: 'Smart Mode', as: 'স্মাৰ্ট ম\'ড' },
    'smart_mode_desc': { en: 'GPS + Weather + Satellite', as: 'GPS + বতৰ + উপগ্ৰহ' },
    'sensor_mode': { en: 'Sensor Mode', as: 'চেন্সৰ ম\'ড' },
    'sensor_mode_desc': { en: 'Manual Input', as: 'হাতেৰে ভৰোৱা' },
    // Location
    'your_location': { en: '📍 Your Location', as: '📍 আপোনাৰ অৱস্থান' },
    'detect_location': { en: 'Detect My Location', as: 'মোৰ অৱস্থান ধৰা পেলাওক' },
    'detect_desc': { en: 'Uses GPS for weather & satellite data', as: 'বতৰ আৰু উপগ্ৰহ তথ্যৰ বাবে GPS ব্যৱহাৰ কৰে' },
    'detecting': { en: 'Detecting location...', as: 'অৱস্থান ধৰা পেলাই আছে...' },
    'location_detected': { en: 'Location Detected ✓', as: 'অৱস্থান পোৱা গ\'ল ✓' },
    'redetect': { en: 'Click to re-detect', as: 'পুনৰ ধৰা পেলাবলৈ ক্লিক কৰক' },
    'location_denied': { en: 'Location access denied', as: 'অৱস্থান অনুমতি অস্বীকাৰ' },
    'enable_gps': { en: 'Enable GPS and try again', as: 'GPS সক্ৰিয় কৰক আৰু পুনৰ চেষ্টা কৰক' },
    // Soil
    'soil_data': { en: '🧪 Soil Data (Sensor / Estimated)', as: '🧪 মাটিৰ তথ্য (চেন্সৰ / আনুমানিক)' },
    'soil_hint': { en: 'Enter if you have soil test data, or leave defaults', as: 'মাটি পৰীক্ষাৰ তথ্য থাকিলে ভৰাওক, নাইবা ডিফল্ট ৰাখক' },
    'soil_nutrients': { en: '🧪 Soil Nutrients', as: '🧪 মাটিৰ পুষ্টি' },
    'weather_soil': { en: '☁️ Weather & Soil', as: '☁️ বতৰ আৰু মাটি' },
    'nitrogen': { en: 'Nitrogen (N)', as: 'নাইট্ৰ\'জেন (N)' },
    'phosphorus': { en: 'Phosphorus (P)', as: 'ফচফৰাচ (P)' },
    'potassium': { en: 'Potassium (K)', as: 'পটাছিয়াম (K)' },
    'soil_ph': { en: 'Soil pH', as: 'মাটিৰ pH' },
    'temperature': { en: 'Temperature', as: 'তাপমাত্ৰা' },
    'humidity': { en: 'Humidity', as: 'আৰ্দ্ৰতা' },
    'rainfall': { en: 'Rainfall', as: 'বৰষুণ' },
    // Button
    'analyze_predict': { en: 'Analyze & Predict', as: 'বিশ্লেষণ আৰু পূৰ্বানুমান' },
    // Welcome
    'welcome_title': { en: 'AI-Based Crop Recommendation & Advisory', as: 'AI ভিত্তিক শস্য পৰামৰ্শ আৰু উপদেশ' },
    'welcome_desc': { en: 'Empowering marginal farmers with satellite imagery, real-time weather, soil sensor integration, and AI-driven advisory services.', as: 'উপগ্ৰহ চিত্ৰ, তাৎক্ষণিক বতৰ, মাটি চেন্সৰ সংহতি, আৰু AI চালিত উপদেশ সেৱাৰে ক্ষুদ্ৰ কৃষকক সৱলীকৰণ।' },
    'welcome_cta': { en: '👆 Select <strong>Smart Mode</strong> and click <strong>Detect My Location</strong> to start, or use <strong>Sensor Mode</strong> for manual input.', as: '👆 <strong>স্মাৰ্ট ম\'ড</strong> বাছক আৰু আৰম্ভ কৰিবলৈ <strong>অৱস্থান ধৰা পেলাওক</strong> ক্লিক কৰক, বা <strong>চেন্সৰ ম\'ড</strong> ব্যৱহাৰ কৰক।' },
    'planet_satellite': { en: 'Planet Satellite', as: 'প্লেনেট উপগ্ৰহ' },
    'live_weather': { en: 'Live Weather', as: 'লাইভ বতৰ' },
    'crop_ai': { en: 'Crop AI', as: 'শস্য AI' },
    'yield_price': { en: 'Yield & Price', as: 'উৎপাদন আৰু মূল্য' },
    'disease_ai': { en: 'Disease AI', as: 'ৰোগ AI' },
    'gemini_advisory': { en: 'Gemini Advisory', as: 'জেমিনি উপদেশ' },
    // Result cards
    'recommended_crop': { en: 'Recommended Crop', as: 'পৰামৰ্শিত শস্য' },
    'yield_prediction': { en: 'Yield Prediction', as: 'উৎপাদন পূৰ্বানুমান' },
    'market_price': { en: 'Market Price', as: 'বজাৰ মূল্য' },
    'expected_profit': { en: 'Expected Profit', as: 'আশানুৰূপ লাভ' },
    'market_timing': { en: 'Market Timing', as: 'বজাৰ সময়' },
    'risk_level': { en: 'Risk Level', as: 'বিপদৰ স্তৰ' },
    'confidence': { en: 'Confidence', as: 'বিশ্বাসযোগ্যতা' },
    // Sections
    'risk_analysis': { en: '⚡ Risk Analysis', as: '⚡ বিপদ বিশ্লেষণ' },
    'ndvi_timeline': { en: '📈 NDVI Crop Health Timeline', as: '📈 NDVI শস্য স্বাস্থ্য সময়ৰেখা' },
    'ndvi_satellite': { en: '📡 NDVI Satellite Crop Health', as: '📡 NDVI উপগ্ৰহ শস্য স্বাস্থ্য' },
    'disease_detection': { en: '🌿 Plant Disease Detection', as: '🌿 উদ্ভিদ ৰোগ চিনাক্তকৰণ' },
    'analytics': { en: '📊 Analytics & Visualizations', as: '📊 বিশ্লেষণ আৰু দৃশ্যায়ন' },
    'smart_advisory': { en: '🧠 Smart Advisory', as: '🧠 স্মাৰ্ট উপদেশ' },
    'mandi_prices': { en: '🏪 Live Mandi Prices', as: '🏪 লাইভ মাণ্ডিৰ মূল্য' },
    'disaster_engine': { en: '🌊 Disaster Decision Engine', as: '🌊 দুৰ্যোগ সিদ্ধান্ত ইঞ্জিন' },
    'ask_farming_ai': { en: '💬 Ask Farming AI', as: '💬 কৃষি AI ক সুধক' },
    'farmer_news': { en: '📰 Smart Farming News', as: '📰 স্মাৰ্ট কৃষি বাতৰি' },
    'agriculture_filter': { en: 'Agriculture', as: 'কৃষি' },
    'weather_filter': { en: 'Weather', as: 'বতৰ' },
    'prices_filter': { en: 'Market Prices', as: 'বজাৰ মূল্য' },
    'tech_filter': { en: 'Technology', as: 'প্রযুক্তি' },
    'all_filter': { en: 'All News', as: 'সকল বাতৰি' },
    'breaking': { en: '🔴 BREAKING', as: '🔴 সাম্প্রতিক' },
    'complete_report': { en: '📄 Complete Report', as: '📄 সম্পূৰ্ণ প্ৰতিবেদন' },
    'all_india': { en: '🇮🇳 All India', as: '🇮🇳 সকলো ভাৰত' },
    'assam': { en: '🏞️ Assam', as: '🏞️ অসম' },
    'subsidies': { en: '💰 Subsidies & Schemes', as: '💰 ভত্তা আৰু আঁচনি' },
    'schemes': { en: '📋 Government Schemes', as: '📋 চৰকাৰী আঁচনি' },
    'ag_news': { en: '📰 Agricultural News', as: '📰 কৃষি বাতৰি' },
    'fetch_news': { en: '🔍 Fetch News', as: '🔍 বাতৰি আনক' },
    'news_hint': { en: 'Select category and region, then click Fetch to see latest farmer-related news, subsidies, and schemes', as: 'বিভাগ আৰু অঞ্চল বাছক, তাৰ পিছত সৰ্বশেষ কৃষক সম্বন্ধীয় বাতৰি, ভত্তা আৰু আঁচনি চাবলৈ Fetch ক্লিক কৰক' },
    // Chatbot
    'chat_welcome': { en: 'Hi! I\'m your AI farming advisor. Ask me anything about crop suitability, farming techniques, soil management, or government schemes. For example:', as: 'নমস্কাৰ! মই আপোনাৰ AI কৃষি উপদেষ্টা। শস্যৰ উপযুক্ততা, কৃষি কৌশল, মাটি ব্যৱস্থাপনা, বা চৰকাৰী আঁচনিৰ বিষয়ে যিকোনো কথা সুধিব পাৰে। উদাহৰণ:' },
    'chat_ex1': { en: '"Is sugarcane suitable for my area?"', as: '"মোৰ অঞ্চলৰ বাবে কুঁহিয়াৰ উপযুক্ত নে?"' },
    'chat_ex2': { en: '"What fertilizer schedule for rice?"', as: '"ধানৰ বাবে সাৰৰ সময়সূচী কি?"' },
    'chat_ex3': { en: '"Best crop for sandy soil with low rainfall?"', as: '"কম বৰষুণ আৰু বালিচহীয়া মাটিত কি শস্য ভাল?"' },
    'chat_placeholder': { en: 'Ask about crop suitability, techniques, schemes...', as: 'শস্যৰ উপযুক্ততা, কৌশল, আঁচনিৰ বিষয়ে সুধক...' },
    // Disease
    'drop_leaf': { en: 'Drop leaf image or <strong>click to upload</strong>', as: 'পাতৰ ছবি দিয়ক বা <strong>আপল\'ড কৰিবলৈ ক্লিক কৰক</strong>' },
    'detect_disease': { en: '🔬 Detect Disease', as: '🔬 ৰোগ চিনাক্ত কৰক' },
    'treatment': { en: '💊 Treatment', as: '💊 চিকিৎসা' },
    // Mandi
    'commodity_placeholder': { en: 'Commodity (e.g. Rice, Wheat)', as: 'শস্য (যেনে ধান, গম)' },
    'state_placeholder': { en: 'State (optional)', as: 'ৰাজ্য (ঐচ্ছিক)' },
    'fetch_prices': { en: '🔍 Fetch Prices', as: '🔍 মূল্য আনক' },
    'mandi_hint': { en: 'Enter a commodity name and click Fetch to see live mandi prices across India', as: 'শস্যৰ নাম লিখক আৰু ভাৰতৰ মাণ্ডিৰ মূল্য চাবলৈ Fetch ক্লিক কৰক' },
    // Disaster
    'generate_plan': { en: '⚡ Generate Response Plan', as: '⚡ সঁহাৰি পৰিকল্পনা তৈয়াৰ কৰক' },
    // Buttons
    'download': { en: '📥 Download', as: '📥 ডাউনল\'ড' },
    'print': { en: '🖨️ Print', as: '🖨️ প্ৰিণ্ট' },
    'live_data': { en: '🛰️ Live Data', as: '🛰️ লাইভ তথ্য' },
    '12_months': { en: '12 Months', as: '১২ মাহ' },
    // Read aloud
    'read_aloud': { en: '🔊 Read Aloud', as: '🔊 পঢ়ুৱাওক' },
    'stop_reading': { en: '⏹ Stop', as: '⏹ থামাওক' },
    // Footer
    'footer': { en: '🌾 Smart Farming Decision System © 2026 | AI + Satellite + Weather + Sensors | Hackathon Project', as: '🌾 স্মাৰ্ট কৃষি সিদ্ধান্ত ব্যৱস্থা © ২০২৬ | AI + উপগ্ৰহ + বতৰ + চেন্সৰ | হেকাথন প্ৰকল্প' },
    // Voice
    'speak_now': { en: '🎤 Listening... speak now', as: '🎤 শুনি আছোঁ... এতিয়া কওক' },
    'voice_not_supported': { en: 'Voice input not supported in this browser', as: 'এই ব্ৰাউজাৰত মাইক সেৱা উপলব্ধ নহয়' },
};

function t(key) {
    const entry = i18n[key];
    if (!entry) return key;
    return entry[currentLang] || entry['en'] || key;
}

// ━━━ INIT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
document.addEventListener('DOMContentLoaded', () => {
    setupModeToggle();
    setupSliderSync();
    setupThemeToggle();
    setupDiseaseUpload();
    setupForm();
    setupAlternativeCrops();
    setupMandiPrices();
    setupNews();
    setupDisasterEngine();
    setupChatbot();
    setupLanguageToggle();
    setupVoiceInput();
    applyLanguage();
    window.addEventListener('resize', () => {
        if (lastNDVITimeline) {
            const canvas = document.getElementById('ndviTimelineChart');
            if (canvas) drawNDVITimelineCanvas(canvas, lastNDVITimeline);
        }
    });
});

// ━━━ MODE TOGGLING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupModeToggle() {
    document.getElementById('tabAuto').addEventListener('click', () => switchMode('auto'));
    document.getElementById('tabManual').addEventListener('click', () => switchMode('manual'));
    document.getElementById('tabDisease').addEventListener('click', () => switchMode('disease'));
    document.getElementById('getLocationBtn').addEventListener('click', detectLocation);
}

function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
    
    if (mode === 'auto') document.getElementById('tabAuto').classList.add('active');
    else if (mode === 'manual') document.getElementById('tabManual').classList.add('active');
    else if (mode === 'disease') document.getElementById('tabDisease').classList.add('active');

    document.getElementById('autoSection').classList.toggle('hidden', mode !== 'auto');
    const manualSection = document.getElementById('manualSection');
    if (manualSection) manualSection.classList.toggle('hidden', mode !== 'manual');
    
    const diseaseUploadSidebar = document.getElementById('diseaseUploadSidebar');
    if (diseaseUploadSidebar) diseaseUploadSidebar.classList.toggle('hidden', mode !== 'disease');

    const predictBtn = document.getElementById('predictBtn');
    if (predictBtn) predictBtn.style.display = mode === 'disease' ? 'none' : 'flex';

    if (mode === 'disease') {
        document.getElementById('welcomeState').classList.add('hidden');
        document.getElementById('resultsState').classList.remove('hidden');
        
        ['resultsGrid', 'ndviTimelineSection', 'ndviSection', 'chartsSection', 'advisorySection'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add('hidden');
        });
        
        const diseaseSection = document.getElementById('diseaseSection');
        if (diseaseSection) diseaseSection.classList.remove('hidden');
    } else {
        ['resultsGrid', 'ndviTimelineSection', 'ndviSection', 'chartsSection', 'advisorySection'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.remove('hidden');
        });
    }
}

// ━━━ GPS LOCATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function detectLocation() {
    const btn = document.getElementById('getLocationBtn');
    const infoEl = document.getElementById('locationInfo');
    const badgeEl = document.getElementById('locBadge');
    const coordsEl = document.getElementById('locCoords');

    btn.querySelector('strong').textContent = t('detecting');
    btn.classList.remove('located');

    if (!navigator.geolocation) {
        btn.querySelector('strong').textContent = 'Geolocation not supported';
        return;
    }

    navigator.geolocation.getCurrentPosition(
        async (pos) => {
            userLocation = { lat: pos.coords.latitude, lon: pos.coords.longitude };
            btn.classList.add('located');
            btn.querySelector('strong').textContent = t('location_detected');
            btn.querySelector('small').textContent = t('redetect');

            infoEl.classList.remove('hidden');
            coordsEl.textContent = `${userLocation.lat.toFixed(4)}°N, ${userLocation.lon.toFixed(4)}°E`;
            badgeEl.textContent = '📍 Loading weather...';

            // Fetch weather
            try {
                const resp = await fetch('/api/weather', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ latitude: userLocation.lat, longitude: userLocation.lon })
                });
                const data = await resp.json();
                if (data.success) {
                    badgeEl.textContent = `📍 ${data.city}, ${data.country}`;
                    showWeatherPreview(data);
                } else {
                    badgeEl.textContent = '📍 Location set (weather unavailable)';
                }
            } catch (e) {
                badgeEl.textContent = '📍 Location set';
            }
        },
        (err) => {
            btn.querySelector('strong').textContent = t('location_denied');
            btn.querySelector('small').textContent = t('enable_gps');
            console.error('Geolocation error:', err);
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

function showWeatherPreview(data) {
    const el = document.getElementById('weatherPreview');
    el.classList.remove('hidden');
    document.getElementById('weatherIcon').src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
    document.getElementById('weatherTemp').textContent = `${data.temperature}°C`;
    document.getElementById('weatherDesc').textContent = data.description;
    document.getElementById('weatherDetails').innerHTML = `
        <div class="weather-detail-item">💧 Humidity: ${data.humidity}%</div>
        <div class="weather-detail-item">🌧️ Rain: ~${data.rainfall} mm/mo</div>
        <div class="weather-detail-item">💨 Wind: ${data.wind_speed} m/s</div>
        <div class="weather-detail-item">🔽 Pressure: ${data.pressure} hPa</div>
        <div class="weather-detail-item">☁️ Clouds: ${data.clouds}%</div>
        <div class="weather-detail-item">🌡️ Feels: ${data.feels_like}°C</div>
    `;
}

// ━━━ FORM SUBMISSION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupForm() {
    document.getElementById('sensorForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await runPrediction();
    });
}

async function runPrediction() {
    const btn = document.getElementById('predictBtn');
    btn.classList.add('loading');

    let payload;
    if (currentMode === 'auto') {
        if (!userLocation) {
            alert('Please detect your location first!');
            btn.classList.remove('loading');
            return;
        }
        payload = {
            mode: 'auto',
            latitude: userLocation.lat,
            longitude: userLocation.lon,
            N: parseFloat(document.getElementById('autoN').value),
            P: parseFloat(document.getElementById('autoP').value),
            K: parseFloat(document.getElementById('autoK').value),
            ph: parseFloat(document.getElementById('autoPH').value)
        };
    } else {
        payload = {
            mode: 'manual',
            N: parseFloat(document.getElementById('inputN').value),
            P: parseFloat(document.getElementById('inputP').value),
            K: parseFloat(document.getElementById('inputK').value),
            temperature: parseFloat(document.getElementById('inputTemp').value),
            humidity: parseFloat(document.getElementById('inputHumidity').value),
            ph: parseFloat(document.getElementById('inputPH').value),
            rainfall: parseFloat(document.getElementById('inputRainfall').value)
        };
    }

    try {
        const resp = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...payload, language: currentLang })
        });
        const data = await resp.json();

        if (data.success) {
            document.getElementById('welcomeState').classList.add('hidden');
            document.getElementById('resultsState').classList.remove('hidden');
            try {
                displayResults(data);
            } catch (renderError) {
                console.error('Dashboard render error:', renderError);
                alert(`Dashboard display error: ${renderError.message}`);
            }
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        alert('Network error. Is the server running?');
        console.error(e);
    } finally {
        btn.classList.remove('loading');
    }
}

// ━━━ DISPLAY RESULTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayResults(data) {
    // Weather banner
    if (data.weather) {
        const banner = document.getElementById('weatherBanner');
        banner.classList.remove('hidden');
        document.getElementById('bannerCity').textContent = `${data.weather.city}, ${data.weather.country}`;
        document.getElementById('bannerWeatherIcon').src = `https://openweathermap.org/img/wn/${data.weather.icon}.png`;
        document.getElementById('bannerTemp').textContent = `${data.weather.temperature}°C`;
        document.getElementById('bannerDesc').textContent = data.weather.description;
        document.getElementById('bannerHumidity').textContent = `${data.weather.humidity}%`;
        document.getElementById('bannerRainfall').textContent = `~${data.weather.rainfall} mm`;
        document.getElementById('bannerWind').textContent = `${data.weather.wind_speed} m/s`;
    } else {
        document.getElementById('weatherBanner').classList.add('hidden');
    }

    // Cards
    displayCards(data);
    // Alerts
    displayAlerts(data.alerts);
    // Market Timing & Risk
    displayMarketTiming(data.market_timing);
    displayRisk(data.risk);
    // NDVI Timeline
    displayNDVITimeline(data.ndvi_timeline);
    // NDVI
    displayNDVI(data.ndvi);
    // Charts
    displayCharts(data);
    // Advisory
    displayAdvisory(data.advisory);
    // Auto-fill mandi with recommended crop
    if (data.crop?.name) {
        document.getElementById('mandiCommodity').value = data.crop.name;
        document.getElementById('disasterLocation').value = data.weather?.city || '';
    }
    // Store for context
    lastPredictionData = data;
    // Report
    displayReport(data);
}

function displayCards(data) {
    document.getElementById('cropValue').textContent = data.crop.name;
    
    const score = data.crop.display_confidence ?? data.crop.confidence;
    const rawConfidence = data.crop.confidence;
    const confEl = document.getElementById('cropConfidence');
    if (data.crop.confidence_rating === 'Low') {
        confEl.innerHTML = `<span style="color:#f59e0b;">Recommendation score: ${score}%</span><br><small style="color:var(--text-secondary)">Raw model probability: ${rawConfidence}%</small>`;
    } else {
        confEl.innerHTML = `Recommendation score: ${score}%<br><small style="color:var(--text-secondary)">Raw model probability: ${rawConfidence}%</small>`;
    }
    
    const topCropsHTML = data.crop.top_crops.map(c =>
        `<div class="top-crop-item"><span>${c.name}</span><span style="font-family:var(--font-mono)">${c.score ?? c.probability}%</span></div>`
    ).join('');
    document.getElementById('topCrops').innerHTML = topCropsHTML;

    document.getElementById('yieldValue').textContent = `${data.yield.value} t/ha`;
    document.getElementById('priceValue').textContent = `₹${data.price.value.toLocaleString()}/q`;
    document.getElementById('mspInfo').innerHTML = `MSP: ₹${data.price.msp.toLocaleString()}/q`;
    document.getElementById('profitValue').textContent = `₹${data.profit.value.toLocaleString()}`;
}

// ━━━ MARKET TIMING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayMarketTiming(mt) {
    if (!mt) return;
    const el = document.getElementById('marketDecision');
    el.textContent = `${mt.badge} ${mt.decision}`;
    el.style.color = mt.color;
    document.getElementById('marketReason').textContent = mt.reason;
}

// ━━━ RISK ANALYSIS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayRisk(risk) {
    if (!risk) return;
    const el = document.getElementById('riskLevel');
    el.textContent = `${risk.badge} ${risk.level}`;
    el.style.color = risk.color;
    document.getElementById('riskScore').textContent = `Risk Score: ${risk.score}/100`;
    document.getElementById('riskReasons').innerHTML = risk.reasons.map(r => `<div style="margin:2px 0;">${r}</div>`).join('');

    // Risk factors breakdown
    const factorsEl = document.getElementById('riskFactors');
    factorsEl.innerHTML = risk.factors.map(f => `
        <div class="risk-factor-item">
            <div style="flex:1;">
                <div class="risk-factor-name">${f.factor}</div>
                <div class="risk-factor-bar"><div class="risk-factor-fill" style="width:${f.score}%;background:${f.color}"></div></div>
            </div>
            <span class="risk-factor-level" style="background:${f.color}">${f.level}</span>
        </div>
    `).join('');
}

// ━━━ ALERTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayAlerts(alerts) {
    const el = document.getElementById('alertsSection');
    if (!alerts || alerts.length === 0) {
        el.innerHTML = '';
        return;
    }
    el.innerHTML = alerts.map((a, i) => `
        <div class="alert-banner ${a.type}" style="animation-delay:${i * 0.1}s">
            <span class="alert-icon">${a.icon}</span>
            <div class="alert-content">
                <div class="alert-title">${a.title}</div>
                <div class="alert-message">${a.message}</div>
            </div>
        </div>
    `).join('');
}

// ━━━ NDVI TIMELINE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayNDVITimeline(timeline) {
    if (!timeline || timeline.length === 0) {
        const currentNdvi = lastPredictionData?.ndvi?.ndvi || 0.55;
        timeline = generateFallbackNDVITimeline(currentNdvi);
    }

    const canvas = document.getElementById('ndviTimelineChart');
    if (!canvas) return;

    const normalizedTimeline = timeline.map(t => ({
        month: t.month,
        ndvi: Math.max(0, Math.min(1, Number(t.ndvi) || 0))
    }));
    lastNDVITimeline = normalizedTimeline;

    requestAnimationFrame(() => drawNDVITimelineCanvas(canvas, normalizedTimeline));
}

function generateFallbackNDVITimeline(currentNdvi) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const value = Math.max(0.15, Math.min(0.9, Number(currentNdvi) || 0.55));
    return months.map((month, index) => {
        const seasonal = 0.08 * Math.sin((index / 11) * Math.PI);
        const earlyGrowth = (index / 11) * 0.14;
        return { month, ndvi: Number(Math.max(0.1, Math.min(0.95, value - 0.12 + earlyGrowth + seasonal)).toFixed(3)) };
    });
}

function drawNDVITimelineCanvas(canvas, timeline) {
    const card = canvas.parentElement;
    const styles = getComputedStyle(document.body);
    const textColor = styles.getPropertyValue('--text-secondary').trim() || '#64748b';
    const titleColor = styles.getPropertyValue('--text-primary').trim() || '#0f172a';
    const accentColor = '#22c55e';
    const warningColor = '#f59e0b';
    const dangerColor = '#ef4444';
    const gridColor = 'rgba(100,120,150,.18)';
    const width = Math.max(640, Math.floor(card.clientWidth || canvas.clientWidth || 640));
    const height = Math.max(260, Math.floor(card.clientHeight || 320));
    const dpr = window.devicePixelRatio || 1;

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const pad = { top: 28, right: 24, bottom: 44, left: 48 };
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;
    const xFor = i => pad.left + (timeline.length === 1 ? chartW / 2 : (i / (timeline.length - 1)) * chartW);
    const yFor = value => pad.top + (1 - value) * chartH;

    ctx.font = '600 12px Inter, sans-serif';
    ctx.fillStyle = titleColor;
    ctx.fillText('NDVI Value', pad.left, 18);

    ctx.font = '10px Inter, sans-serif';
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    [0, 0.25, 0.5, 0.75, 1].forEach(value => {
        const y = yFor(value);
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(width - pad.right, y);
        ctx.stroke();
        ctx.fillStyle = textColor;
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(value.toFixed(2), pad.left - 10, y);
    });

    [
        { from: 0, to: 0.3, color: dangerColor },
        { from: 0.3, to: 0.6, color: warningColor },
        { from: 0.6, to: 1, color: accentColor },
    ].forEach(zone => {
        ctx.fillStyle = zone.color;
        ctx.globalAlpha = 0.05;
        ctx.fillRect(pad.left, yFor(zone.to), chartW, yFor(zone.from) - yFor(zone.to));
        ctx.globalAlpha = 1;
    });

    const gradient = ctx.createLinearGradient(0, pad.top, 0, height - pad.bottom);
    gradient.addColorStop(0, 'rgba(34,197,94,.28)');
    gradient.addColorStop(1, 'rgba(34,197,94,0)');

    ctx.beginPath();
    timeline.forEach((point, i) => {
        const x = xFor(i);
        const y = yFor(point.ndvi);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.lineTo(xFor(timeline.length - 1), height - pad.bottom);
    ctx.lineTo(xFor(0), height - pad.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    timeline.forEach((point, i) => {
        const x = xFor(i);
        const y = yFor(point.ndvi);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = accentColor;
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();

    timeline.forEach((point, i) => {
        const x = xFor(i);
        const y = yFor(point.ndvi);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = accentColor;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#fff';
        ctx.stroke();

        ctx.fillStyle = textColor;
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(point.month, x, height - pad.bottom + 14);
    });
}

// ━━━ NDVI ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayNDVI(ndviData) {
    document.getElementById('ndviNumber').textContent = ndviData.ndvi;
    document.getElementById('ndviNumber').style.color = ndviData.color;
    document.getElementById('ndviLabel').textContent = ndviData.health;
    document.getElementById('ndviLabel').style.color = ndviData.color;

    drawNDVIGauge(ndviData.ndvi, ndviData.color);

    const isReal = ndviData.source && ndviData.source.includes('Planet');
    const badge = document.getElementById('ndviSourceBadge');
    badge.textContent = isReal ? '🛰️ Live Satellite' : '📊 Simulated';
    badge.style.background = isReal ? 'rgba(34,197,94,.12)' : 'rgba(245,158,11,.12)';
    badge.style.color = isReal ? '#22c55e' : '#f59e0b';
    badge.style.borderColor = isReal ? 'rgba(34,197,94,.25)' : 'rgba(245,158,11,.25)';

    const satInfo = document.getElementById('ndviSatelliteInfo');
    if (isReal && ndviData.satellite_info) {
        const si = ndviData.satellite_info;
        const acq = si.acquired ? new Date(si.acquired).toLocaleDateString('en-IN', { year:'numeric', month:'short', day:'numeric' }) : '—';
        satInfo.innerHTML = `<div style="padding:10px;background:var(--bg-input);border-radius:8px;margin-bottom:10px;border:1px solid rgba(34,197,94,.15);">
            <div style="font-size:.7rem;font-weight:600;color:#22c55e;margin-bottom:6px;">🛰️ Planet Satellite Data</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:.68rem;">
                <div><span style="color:var(--text-muted);">Scene:</span> <span style="font-family:var(--font-mono);">${si.scene_id.substring(0,16)}…</span></div>
                <div><span style="color:var(--text-muted);">Date:</span> ${acq}</div>
                <div><span style="color:var(--text-muted);">Cloud:</span> ${si.cloud_cover}%</div>
                <div><span style="color:var(--text-muted);">Visible:</span> ${si.visible_percent}%</div>
            </div></div>`;
        satInfo.classList.remove('hidden');
    } else {
        satInfo.classList.add('hidden');
    }

    const factors = ndviData.details;
    const factorsEl = document.getElementById('ndviFactors');
    if (isReal) {
        factorsEl.innerHTML = `
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">✨ Clear Signal</span><span class="ndvi-factor-value">${(factors.clear_signal*100).toFixed(0)}%</span></div>
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">👁️ Visibility</span><span class="ndvi-factor-value">${(factors.visibility*100).toFixed(0)}%</span></div>
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">☁️ Cloud Free</span><span class="ndvi-factor-value">${(factors.cloud_free*100).toFixed(0)}%</span></div>
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">📊 Quality</span><span class="ndvi-factor-value">${(factors.data_quality*100).toFixed(0)}%</span></div>`;
    } else {
        factorsEl.innerHTML = `
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">🌡️ Temperature</span><span class="ndvi-factor-value">${(factors.temp_contribution*100).toFixed(0)}%</span></div>
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">💧 Humidity</span><span class="ndvi-factor-value">${(factors.humidity_contribution*100).toFixed(0)}%</span></div>
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">🌧️ Rainfall</span><span class="ndvi-factor-value">${(factors.rainfall_contribution*100).toFixed(0)}%</span></div>
            <div class="ndvi-factor-item"><span class="ndvi-factor-name">⚗️ pH</span><span class="ndvi-factor-value">${(factors.ph_contribution*100).toFixed(0)}%</span></div>`;
    }
}

function drawNDVIGauge(value, color) {
    const canvas = document.getElementById('ndviGauge');
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2, cy = h - 20, r = 100;
    const startAngle = Math.PI, endAngle = 2 * Math.PI;

    // Background arc
    ctx.beginPath(); ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.lineWidth = 16; ctx.strokeStyle = 'rgba(100,120,150,.1)'; ctx.lineCap = 'round'; ctx.stroke();

    // Gradient segments
    const segments = [
        { start: Math.PI, end: Math.PI + Math.PI * 0.3, color: '#ef4444' },
        { start: Math.PI + Math.PI * 0.3, end: Math.PI + Math.PI * 0.6, color: '#f59e0b' },
        { start: Math.PI + Math.PI * 0.6, end: 2 * Math.PI, color: '#22c55e' }
    ];
    segments.forEach(s => {
        ctx.beginPath(); ctx.arc(cx, cy, r, s.start, s.end);
        ctx.lineWidth = 16; ctx.strokeStyle = s.color + '33'; ctx.lineCap = 'butt'; ctx.stroke();
    });

    // Value arc
    const normalizedValue = Math.max(0, Math.min(1, value));
    const valueAngle = startAngle + normalizedValue * Math.PI;
    ctx.beginPath(); ctx.arc(cx, cy, r, startAngle, valueAngle);
    ctx.lineWidth = 16; ctx.strokeStyle = color; ctx.lineCap = 'round'; ctx.stroke();

    // Needle dot
    const dotX = cx + r * Math.cos(valueAngle), dotY = cy + r * Math.sin(valueAngle);
    ctx.beginPath(); ctx.arc(dotX, dotY, 6, 0, 2 * Math.PI);
    ctx.fillStyle = color; ctx.fill();
    ctx.beginPath(); ctx.arc(dotX, dotY, 10, 0, 2 * Math.PI);
    ctx.strokeStyle = color + '40'; ctx.lineWidth = 3; ctx.stroke();
}

// ━━━ ADVISORY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayAdvisory(advisory) {
    const isGemini = advisory.source === 'Gemini AI';
    const badge = document.getElementById('advisorySourceBadge');
    badge.textContent = isGemini ? '✨ Powered by Gemini AI' : '🔧 Rule-Based';
    badge.style.background = isGemini ? 'rgba(139,92,246,.12)' : 'rgba(245,158,11,.12)';
    badge.style.color = isGemini ? '#8b5cf6' : '#f59e0b';
    badge.style.borderColor = isGemini ? 'rgba(139,92,246,.25)' : 'rgba(245,158,11,.25)';

    if (advisory.overall_summary) {
        document.getElementById('advisorySummary').innerHTML = `<strong>📋 Summary:</strong> ${advisory.overall_summary}`;
        document.getElementById('advisorySummary').classList.remove('hidden');
    }

    const listEl = document.getElementById('advisoryList');
    listEl.innerHTML = advisory.advisories.map((a, i) => `
        <div class="advisory-item ${a.severity}" style="animation-delay:${i * 0.05}s">
            <span class="advisory-icon">${a.icon}</span>
            <div class="advisory-text">
                <div class="advisory-title">${a.title || ''}</div>
                <div class="advisory-message">${a.message}</div>
            </div>
        </div>
    `).join('');

    const extrasEl = document.getElementById('advisoryExtras');
    const extras = [];
    if (advisory.seasonal_tip) extras.push(`<div class="advisory-extra-card"><h4>🗓️ Seasonal Tip</h4><p>${advisory.seasonal_tip}</p></div>`);
    if (advisory.market_insight) extras.push(`<div class="advisory-extra-card"><h4>📈 Market Insight</h4><p>${advisory.market_insight}</p></div>`);
    extrasEl.innerHTML = extras.join('');
}

// ━━━ CHARTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayCharts(data) {
    Object.values(currentCharts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    currentCharts = {};

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded; skipping charts.');
        return;
    }

    const gridColor = 'rgba(100,120,150,.1)';
    const fontColor = getComputedStyle(document.body).getPropertyValue('--text-secondary').trim() || '#8899b0';
    const defaults = {
        plugins: { legend: { labels: { color: fontColor, padding: 10, font: { family: 'Inter', size: 11 } } } },
        scales: { x: { ticks: { color: fontColor, font: { size: 10 } }, grid: { color: gridColor } }, y: { ticks: { color: fontColor, font: { size: 10 } }, grid: { color: gridColor } } }
    };

    // Crop probabilities
    if (data.crop.top_crops) {
        const crops = data.crop.top_crops;
        currentCharts.crop = new Chart(document.getElementById('cropChart'), {
            type: 'bar', data: {
                labels: crops.map(c => c.name),
                datasets: [{ label: 'Recommendation Score', data: crops.map(c => c.score ?? c.probability),
                    backgroundColor: ['rgba(34,197,94,.6)', 'rgba(59,130,246,.5)', 'rgba(245,158,11,.4)'],
                    borderColor: ['#22c55e', '#3b82f6', '#f59e0b'], borderWidth: 1, borderRadius: 6, barPercentage: 0.6 }]
            }, options: { ...defaults, indexAxis: 'y' }
        });
    }

    // Feature importance
    if (data.feature_importance?.crop?.length) {
        const fi = data.feature_importance.crop;
        currentCharts.feature = new Chart(document.getElementById('featureChart'), {
            type: 'doughnut', data: {
                labels: fi.map(f => f.feature),
                datasets: [{ data: fi.map(f => f.importance),
                    backgroundColor: ['#22c55e','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899'],
                    borderWidth: 0 }]
            }, options: {
                plugins: {
                    legend: { position: 'bottom', labels: { color: fontColor, font: { size: 10 }, padding: 6 } }
                }
            }
        });
    }

    if (data.feature_importance?.yield?.length) {
        const yi = data.feature_importance.yield;
        currentCharts.yieldFeat = new Chart(document.getElementById('yieldFeatureChart'), {
            type: 'polarArea', data: {
                labels: yi.map(f => f.feature),
                datasets: [{ data: yi.map(f => f.importance),
                    backgroundColor: ['#22c55e44','#3b82f644','#f59e0b44','#ef444444','#8b5cf644','#06b6d444','#ec489944','#14b8a644'],
                    borderColor: ['#22c55e','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#14b8a6'],
                    borderWidth: 1 }]
            }, options: {
                plugins: {
                    legend: { position: 'bottom', labels: { color: fontColor, font: { size: 10 }, padding: 6 } }
                },
                scales: {
                    r: {
                        ticks: { display: false },
                        grid: { color: 'rgba(100,120,150,.12)' },
                        pointLabels: { display: false }
                    }
                }
            }
        });
    }

    // NDVI chart
    const ndviD = data.ndvi?.details;
    if (ndviD) {
        const isReal = data.ndvi.source?.includes('Planet');
        const labels = isReal ? ['Clear Signal','Visibility','Cloud Free','Data Quality'] : ['Temperature','Humidity','Rainfall','pH'];
        const values = isReal ? [ndviD.clear_signal, ndviD.visibility, ndviD.cloud_free, ndviD.data_quality]
                              : [ndviD.temp_contribution, ndviD.humidity_contribution, ndviD.rainfall_contribution, ndviD.ph_contribution];
        currentCharts.ndvi = new Chart(document.getElementById('ndviChart'), {
            type: 'radar', data: {
                labels,
                datasets: [{ label: 'NDVI Factors', data: values,
                    backgroundColor: 'rgba(34,197,94,.15)', borderColor: '#22c55e', pointBackgroundColor: '#22c55e', pointRadius: 4, borderWidth: 2 }]
            }, options: { scales: { r: { ticks: { color: fontColor, backdropColor: 'transparent', font: { size: 9 } }, grid: { color: gridColor }, pointLabels: { color: fontColor, font: { size: 10 } } } },
                plugins: { legend: { labels: { color: fontColor } } } }
        });
    }
}

// ━━━ REPORT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function displayReport(data) {
    const score = data.crop.display_confidence ?? data.crop.confidence;
    const rows = [
        ['🌾', 'Recommended Crop', data.crop.name],
        ['📊', 'Recommendation Score', `${score}%`],
        ['🧮', 'Raw Model Probability', `${data.crop.confidence}%`],
        ['📈', 'Yield Prediction', `${data.yield.value} ${data.yield.unit}`],
        ['💰', 'Market Price', `₹${data.price.value.toLocaleString()}/quintal`],
        ['📌', 'MSP', `₹${data.price.msp.toLocaleString()}/quintal`],
        ['🤑', 'Expected Profit', `₹${data.profit.value.toLocaleString()}/hectare`],
        ['📡', 'NDVI', `${data.ndvi.ndvi} (${data.ndvi.health})`],
        ['🛰️', 'NDVI Source', data.ndvi.source || '—'],
        ['🌡️', 'Temperature', `${data.inputs.temperature}°C`],
        ['💧', 'Humidity', `${data.inputs.humidity}%`],
        ['🌧️', 'Rainfall', `${data.inputs.rainfall} mm`],
        ['⚗️', 'Soil pH', data.inputs.ph],
        ['🧪', 'N / P / K', `${data.inputs.N} / ${data.inputs.P} / ${data.inputs.K} kg/ha`],
        ['🧠', 'Advisory Source', data.advisory?.source || '—']
    ];
    if (data.weather) {
        rows.splice(8, 0, ['🌤️', 'Weather', `${data.weather.description} (${data.weather.city})`]);
    }

    document.getElementById('reportContent').innerHTML = rows.map(([icon, label, value]) =>
        `<div class="report-row"><span class="report-icon">${icon}</span><span class="report-label">${label}</span><span class="report-value">${value}</span></div>`
    ).join('');

    document.getElementById('printReport').onclick = () => window.print();

    // Download report
    document.getElementById('downloadReport').onclick = async () => {
        try {
            const reportData = {
                crop: data.crop.name,
                confidence: data.crop.display_confidence ?? data.crop.confidence,
                yield: data.yield.value,
                price: data.price.value,
                msp: data.price.msp,
                profit: data.profit.value,
                market_timing: data.market_timing?.decision || 'N/A',
                ndvi: data.ndvi.ndvi,
                ndvi_source: data.ndvi.source || 'Simulated',
                risk_level: data.risk?.level || 'N/A',
                risk_score: data.risk?.score || 'N/A',
                temperature: data.inputs.temperature,
                humidity: data.inputs.humidity,
                rainfall: data.inputs.rainfall,
                ph: data.inputs.ph,
                npk: `${data.inputs.N} / ${data.inputs.P} / ${data.inputs.K}`,
                advisories: data.advisory?.advisories || [],
                alerts: data.alerts || []
            };
            const resp = await fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reportData)
            });
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Smart_Farming_Report.txt';
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error('Download error:', e);
            alert('Failed to download report');
        }
    };
}

// ━━━ ALTERNATIVE CROPS RECOMMENDATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupAlternativeCrops() {
    const altBtn = document.getElementById('altCropsBtn');
    const modal = document.getElementById('altCropsModal');
    const closeBtn = document.getElementById('closeAltCrops');
    
    if (altBtn) altBtn.addEventListener('click', showAlternativeCrops);
    if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });
}

async function showAlternativeCrops() {
    if (!lastPredictionData) {
        alert('Run a prediction first to see alternatives');
        return;
    }
    
    const modal = document.getElementById('altCropsModal');
    const list = document.getElementById('alternativesList');
    const mainCrop = lastPredictionData.crop?.name || '';
    
    modal.classList.remove('hidden');
    list.innerHTML = '<p class="loading">⏳ Loading alternatives...</p>';
    
    try {
        const inputs = lastPredictionData.inputs || {};
        const resp = await fetch('/api/alternative-crops', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                temperature: inputs.temperature || 25,
                humidity: inputs.humidity || 60,
                rainfall: inputs.rainfall || 100,
                ph: inputs.ph || 6.5,
                N: inputs.N || 60,
                P: inputs.P || 40,
                K: inputs.K || 40,
                season: inputs.season || 'Kharif',
                exclude: mainCrop
            })
        });
        
        const data = await resp.json();
        
        if (!data.success || !data.alternatives || data.alternatives.length === 0) {
            list.innerHTML = '<p style="color: var(--text-muted);">No alternatives found</p>';
            return;
        }
        
        let html = '';
        data.alternatives.forEach((alt, idx) => {
            const confNum = parseFloat(alt.confidence);
            const confClass = confNum >= 70 ? 'confidence-high' : confNum >= 50 ? 'confidence-medium' : 'confidence-low';
            
            html += `
                <div class="alt-crop-card">
                    <div class="alt-crop-name">${idx + 1}. ${alt.crop} <span class="${confClass}">${alt.confidence}</span></div>
                    <div class="alt-crop-stats">
                        <div class="stat-item">
                            <div class="stat-label">Suitability</div>
                            <div class="stat-value">${alt.suitability_score}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Est. Yield</div>
                            <div class="stat-value">${alt.estimated_yield}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Market Price</div>
                            <div class="stat-value">${alt.market_price}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Est. Profit</div>
                            <div class="stat-value">${alt.estimated_profit}</div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        list.innerHTML = html;
        console.log(`✅ Showing ${data.alternatives.length} alternative crops`);
        
    } catch (e) {
        list.innerHTML = `<p style="color: var(--accent-4);">⚠️ Error: ${e.message}</p>`;
    }
}


function setupDiseaseUpload() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('diseaseImageInput');
    const detectBtn = document.getElementById('detectBtn');

    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', (e) => { e.preventDefault(); zone.classList.remove('drag-over'); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); });
    input.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

    document.getElementById('removeImage').addEventListener('click', (e) => {
        e.stopPropagation();
        diseaseFile = null;
        document.getElementById('uploadContent').classList.remove('hidden');
        document.getElementById('uploadPreview').classList.add('hidden');
        detectBtn.disabled = true;
        document.getElementById('diseaseResult').classList.add('hidden');
    });

    detectBtn.addEventListener('click', async () => {
        if (!diseaseFile) return;
        detectBtn.disabled = true;
        detectBtn.innerHTML = '<span>🔄 Analyzing...</span>';

        const formData = new FormData();
        formData.append('image', diseaseFile);

        try {
            const resp = await fetch('/api/disease', { method: 'POST', body: formData });
            const data = await resp.json();
            if (data.success) {
                const result = document.getElementById('diseaseResult');
                result.classList.remove('hidden');

                // ── Basic info ──────────────────────────────────────────────
                const isHealthy = data.disease.toLowerCase().includes('healthy');
                document.getElementById('diseaseIcon').textContent = isHealthy ? '✅' : '🦠';
                document.getElementById('diseaseName').textContent = data.disease;
                document.getElementById('diseaseConfidence').textContent =
                    `Confidence: ${data.confidence}% (${data.model || 'Image analysis'})`;

                // ── Severity badge ──────────────────────────────────────────
                const sev = data.severity || {};
                const sevBadge = document.getElementById('diseaseSeverityBadge');
                const sevDesc  = document.getElementById('diseaseSeverityDesc');
                if (sev.level) {
                    sevBadge.textContent  = `${sev.badge || ''} Severity: ${sev.level}`;
                    sevBadge.style.background  = (sev.color || '#22c55e') + '22';
                    sevBadge.style.color        = sev.color || '#22c55e';
                    sevBadge.style.border       = `1px solid ${(sev.color || '#22c55e')}55`;
                    sevDesc.textContent = sev.description || '';
                }

                // ── Urgency note ────────────────────────────────────────────
                const urgEl = document.getElementById('diseaseUrgencyNote');
                if (data.urgency_note) {
                    urgEl.textContent = `⚡ ${data.urgency_note}`;
                    urgEl.classList.remove('hidden');
                } else {
                    urgEl.classList.add('hidden');
                }

                // ── Baseline treatment ──────────────────────────────────────
                document.getElementById('treatmentText').textContent = data.treatment;

                // ── Remedies list ───────────────────────────────────────────
                const remWrap = document.getElementById('diseaseRemediesWrapper');
                const remList = document.getElementById('diseaseRemediesList');
                if (data.remedies && data.remedies.length > 0) {
                    remList.innerHTML = data.remedies
                        .map(r => `<li style="line-height:1.5;">${r}</li>`)
                        .join('');
                    remWrap.classList.remove('hidden');
                } else {
                    remWrap.classList.add('hidden');
                }

                // ── Pesticides table ────────────────────────────────────────
                const pestWrap = document.getElementById('diseasePesticidesWrapper');
                const pestBody = document.getElementById('diseasePesticidesBody');
                if (data.pesticides && data.pesticides.length > 0) {
                    pestBody.innerHTML = data.pesticides.map(p => `
                        <tr style="border-top:1px solid rgba(100,120,150,.12);">
                            <td style="padding:5px 10px;font-weight:600;color:var(--text-primary);">${p.name || '—'}</td>
                            <td style="padding:5px 10px;color:var(--text-secondary);">${p.dose || '—'}</td>
                            <td style="padding:5px 10px;color:var(--text-secondary);">${p.frequency || '—'}</td>
                        </tr>`).join('');
                    pestWrap.classList.remove('hidden');
                } else {
                    pestWrap.classList.add('hidden');
                }

                // ── Preventive measures ─────────────────────────────────────
                const prevWrap = document.getElementById('diseasePreventionWrapper');
                const prevList = document.getElementById('diseasePreventionList');
                if (data.preventive_measures && data.preventive_measures.length > 0) {
                    prevList.innerHTML = data.preventive_measures
                        .map(m => `<li style="line-height:1.5;">${m}</li>`)
                        .join('');
                    prevWrap.classList.remove('hidden');
                } else {
                    prevWrap.classList.add('hidden');
                }

            } else {
                alert(data.error || 'Disease detection failed');
            }
        } catch(e) {
            console.error(e);
            alert('Disease detection failed. Please try again.');
        }

        detectBtn.disabled = false;
        detectBtn.innerHTML = '<span>🔬 Detect Disease</span>';
    });
}

function handleFile(file) {
    diseaseFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('previewImage').src = e.target.result;
        document.getElementById('uploadContent').classList.add('hidden');
        document.getElementById('uploadPreview').classList.remove('hidden');
        document.getElementById('detectBtn').disabled = false;
    };
    reader.readAsDataURL(file);
}

// ━━━ SLIDER SYNC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupSliderSync() {
    const pairs = [['inputN','sliderN'],['inputP','sliderP'],['inputK','sliderK'],
                   ['inputTemp','sliderTemp'],['inputHumidity','sliderHumidity'],
                   ['inputPH','sliderPH'],['inputRainfall','sliderRainfall']];
    pairs.forEach(([inp, sld]) => {
        const inputEl = document.getElementById(inp);
        const sliderEl = document.getElementById(sld);
        if (!inputEl || !sliderEl) return;
        inputEl.addEventListener('input', () => { sliderEl.value = inputEl.value; });
        sliderEl.addEventListener('input', () => { inputEl.value = sliderEl.value; });
    });
}

// ━━━ THEME ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupThemeToggle() {
    const html = document.documentElement;
    const saved = localStorage.getItem('theme') || 'dark';
    // Apply saved theme
    if (saved === 'light') {
        html.classList.remove('dark');
    } else {
        html.classList.add('dark');
    }
    _updateThemeIcon(saved);

    document.getElementById('themeToggle').addEventListener('click', () => {
        const isDark = html.classList.contains('dark');
        if (isDark) {
            html.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            _updateThemeIcon('light');
        } else {
            html.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            _updateThemeIcon('dark');
        }
    });
}

function _updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    // Use material symbol text names
    icon.textContent = theme === 'dark' ? 'dark_mode' : 'light_mode';
}

// ━━━ MANDI PRICES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupMandiPrices() {
    document.getElementById('fetchMandiBtn').addEventListener('click', fetchMandiPrices);
    document.getElementById('mandiCommodity').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') fetchMandiPrices();
    });
}

async function fetchMandiPrices() {
    const commodity = document.getElementById('mandiCommodity').value.trim();
    const state = document.getElementById('mandiState').value.trim();
    const resultsEl = document.getElementById('mandiResults');
    const btn = document.getElementById('fetchMandiBtn');

    if (!commodity) {
        resultsEl.innerHTML = '<p class="mandi-hint">⚠️ Please enter a commodity name</p>';
        return;
    }

    btn.textContent = '🔄 Loading...';
    btn.disabled = true;

    try {
        const resp = await fetch('/api/mandi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ commodity, state, limit: 15 })
        });
        const data = await resp.json();

        if (data.success && data.prices.length > 0) {
            let html = `<div style="max-height:350px;overflow:auto;">
                <table class="mandi-table">
                    <thead><tr>
                        <th>State</th><th>Market</th><th>Variety</th>
                        <th>Min ₹</th><th>Max ₹</th><th>Modal ₹</th><th>Date</th>
                    </tr></thead>
                    <tbody>`;

            data.prices.forEach(p => {
                html += `<tr>
                    <td>${p.state}</td><td>${p.market}</td><td>${p.variety}</td>
                    <td class="price-cell">${Number(p.min_price).toLocaleString()}</td>
                    <td class="price-cell">${Number(p.max_price).toLocaleString()}</td>
                    <td class="modal-price">₹${Number(p.modal_price).toLocaleString()}</td>
                    <td>${p.arrival_date}</td>
                </tr>`;
            });

            html += `</tbody></table></div>
                <div class="mandi-total">
                    <span>Showing ${data.count} of ${data.total} results for "${data.commodity_searched}"</span>
                    <span class="mandi-source">Source: ${data.source}</span>
                </div>`;
            resultsEl.innerHTML = html;
        } else if (data.success) {
            resultsEl.innerHTML = '<p class="mandi-hint">No prices found for this commodity. Try a different name like "Wheat", "Paddy", "Onion".</p>';
        } else {
            resultsEl.innerHTML = `<p class="mandi-hint">⚠️ ${data.error || 'Error fetching prices'}</p>`;
        }
    } catch (e) {
        resultsEl.innerHTML = '<p class="mandi-hint">⚠️ Network error. Please try again.</p>';
    } finally {
        btn.textContent = '🔍 Fetch Prices';
        btn.disabled = false;
    }
}

// ━━━ AGRICULTURAL NEWS & SUBSIDIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let newsAutoRefreshInterval = null;
let currentNewsType = "agriculture";

function setupNews() {
    // Setup filter buttons
    document.querySelectorAll('.news-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.news-filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentNewsType = btn.dataset.type;
            fetchSmartNews();
        });
    });
    
    // Setup search button
    document.getElementById('newsSearchBtn').addEventListener('click', searchNews);
    document.getElementById('newsSearchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchNews();
    });
    
    // Setup auto-refresh toggle
    document.getElementById('autoRefreshNews').addEventListener('change', (e) => {
        if (e.target.checked) {
            startNewsAutoRefresh();
        } else {
            stopNewsAutoRefresh();
        }
    });
    
    // Initial fetch
    fetchSmartNews();
}

async function fetchSmartNews() {
    const feedEl = document.getElementById('newsFeed');
    feedEl.innerHTML = '<p class="news-loading">📡 Loading farming news...</p>';
    
    try {
        const resp = await fetch(`/api/news?type=${currentNewsType}&limit=3`, {
            method: 'GET'
        });
        
        const data = await resp.json();
        
        if (!data.success) {
            feedEl.innerHTML = `<p class="news-error">⚠️ ${data.error || 'Error fetching news'}</p>`;
            return;
        }
        
        if (!data.articles || data.articles.length === 0) {
            feedEl.innerHTML = '<p class="news-hint">📰 No news found for this category. Try another filter.</p>';
            return;
        }
        
        // Display news cards
        let html = '';
        data.articles.forEach((article, idx) => {
            const isBreaking = idx === 0;  // First article is "breaking"
            const date = new Date(article.date).toLocaleDateString('en-IN', {
                month: 'short',
                day: 'numeric'
            });
            
            html += `
                <div class="news-card ${isBreaking ? 'news-breaking' : ''}">
                    ${article.image ? `<img src="${article.image}" alt="${article.title}" class="news-card-image" onerror="this.classList.add('placeholder');this.textContent='📰'">` : '<div class="news-card-image placeholder">📰</div>'}
                    <div class="news-card-content">
                        <h3 class="news-card-title">${article.title}</h3>
                        <p class="news-card-description">${article.description}</p>
                        <div class="news-card-meta">
                            <span class="news-card-source">${article.source}</span>
                            <span class="news-card-date">${date}</span>
                        </div>
                        <a href="${article.link}" target="_blank" class="news-card-link">Read More →</a>
                    </div>
                </div>
            `;
        });
        
        feedEl.innerHTML = html;
        console.log(`✅ Loaded ${data.articles.length} ${currentNewsType} articles`);
        
    } catch (e) {
        feedEl.innerHTML = `<p class="news-error">⚠️ Network error: ${e.message}</p>`;
    }
}

async function searchNews() {
    const searchTerm = document.getElementById('newsSearchInput').value.trim();
    if (!searchTerm) {
        fetchSmartNews();
        return;
    }
    
    const feedEl = document.getElementById('newsFeed');
    feedEl.innerHTML = '<p class="news-loading">🔍 Searching...</p>';
    
    try {
        // For custom search, we'll fetch all and filter client-side
        const resp = await fetch(`/api/news?type=all&limit=12`, { method: 'GET' });
        const data = await resp.json();
        
        if (!data.success || !data.articles) {
            feedEl.innerHTML = '<p class="news-error">⚠️ Search failed</p>';
            return;
        }
        
        // Filter articles by search term
        const filtered = data.articles.filter(article => 
            article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            article.description.toLowerCase().includes(searchTerm.toLowerCase())
        );
        
        if (filtered.length === 0) {
            feedEl.innerHTML = `<p class="news-hint">📰 No results for "${searchTerm}"</p>`;
            return;
        }
        
        // Display results
        let html = '';
        filtered.slice(0, 12).forEach(article => {
            const date = new Date(article.date).toLocaleDateString('en-IN', {
                month: 'short',
                day: 'numeric'
            });
            
            html += `
                <div class="news-card">
                    ${article.image ? `<img src="${article.image}" alt="${article.title}" class="news-card-image" onerror="this.classList.add('placeholder');this.textContent='📰'">` : '<div class="news-card-image placeholder">📰</div>'}
                    <div class="news-card-content">
                        <h3 class="news-card-title">${article.title}</h3>
                        <p class="news-card-description">${article.description}</p>
                        <div class="news-card-meta">
                            <span class="news-card-source">${article.source}</span>
                            <span class="news-card-date">${date}</span>
                        </div>
                        <a href="${article.link}" target="_blank" class="news-card-link">Read More →</a>
                    </div>
                </div>
            `;
        });
        
        feedEl.innerHTML = html;
        console.log(`✅ Found ${filtered.length} matching articles`);
        
    } catch (e) {
        feedEl.innerHTML = `<p class="news-error">⚠️ Error: ${e.message}</p>`;
    }
}

function startNewsAutoRefresh() {
    if (newsAutoRefreshInterval) clearInterval(newsAutoRefreshInterval);
    
    // Refresh every 10 minutes
    newsAutoRefreshInterval = setInterval(() => {
        console.log("🔄 Auto-refreshing news...");
        fetchSmartNews();
    }, 10 * 60 * 1000);
    
    console.log("✅ News auto-refresh enabled (every 10 min)");
}

function stopNewsAutoRefresh() {
    if (newsAutoRefreshInterval) {
        clearInterval(newsAutoRefreshInterval);
        newsAutoRefreshInterval = null;
        console.log("⏹ News auto-refresh disabled");
    }
}

// ━━━ DISASTER DECISION ENGINE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let disasterLang = 'en';

function setupDisasterEngine() {
    document.getElementById('runDisasterBtn').addEventListener('click', runDisasterEngine);
    
    // Setup language buttons
    document.getElementById('disasterLangEn').addEventListener('click', () => {
        disasterLang = 'en';
        document.getElementById('disasterLangEn').classList.add('active');
        document.getElementById('disasterLangAs').classList.remove('active');
    });
    
    document.getElementById('disasterLangAs').addEventListener('click', () => {
        disasterLang = 'as';
        document.getElementById('disasterLangAs').classList.add('active');
        document.getElementById('disasterLangEn').classList.remove('active');
    });
}

async function runDisasterEngine() {
    const disasterType = document.getElementById('disasterType').value;
    const severity = document.getElementById('disasterSeverity').value;
    const location = document.getElementById('disasterLocation').value || 'India';
    const resultsEl = document.getElementById('disasterResults');
    const btn = document.getElementById('runDisasterBtn');
    const crop = lastPredictionData?.crop?.name || 'rice';

    btn.textContent = '🔄 Generating...';
    btn.disabled = true;
    resultsEl.classList.remove('hidden');
    resultsEl.innerHTML = '<p style="text-align:center;padding:20px;color:var(--text-muted);">🧠 AI is generating a disaster response plan...</p>';

    try {
        const resp = await fetch('/api/disaster', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ disaster_type: disasterType, severity, location, crop, language: disasterLang })
        });
        const data = await resp.json();

        if (data.success) {
            renderDisasterPlan(data);
        } else {
            resultsEl.innerHTML = `<p class="mandi-hint">⚠️ ${data.error || 'Error generating plan'}</p>`;
        }
    } catch (e) {
        resultsEl.innerHTML = '<p class="mandi-hint">⚠️ Network error. Please try again.</p>';
    } finally {
        btn.textContent = '⚡ Generate Response Plan';
        btn.disabled = false;
    }
}

function renderDisasterPlan(data) {
    const el = document.getElementById('disasterResults');
    const typeIcons = { flood:'🌊', drought:'☀️', cyclone:'🌀', heatwave:'🔥', frost:'❄️', hailstorm:'🧊', pest_outbreak:'🦗' };
    const icon = typeIcons[data.disaster_type] || '⚠️';

    let html = `
        <div class="disaster-header-banner">
            <span class="dh-icon">${icon}</span>
            <div>
                <div class="dh-title">${data.disaster_type?.toUpperCase()} Response Plan</div>
                <div class="dh-subtitle">Severity: ${data.severity?.toUpperCase()} | Source: ${data.source}</div>
            </div>
        </div>
        <h4 style="font-size:.85rem;margin-bottom:8px;">🚨 Immediate Actions</h4>
        <div class="disaster-actions">`;

    if (data.immediate_actions) {
        data.immediate_actions.forEach(a => {
            html += `<div class="disaster-action ${a.priority}">
                <span class="da-icon">${a.icon}</span>
                <div class="da-content">
                    <div class="da-action">${a.action} <span class="da-priority ${a.priority}">${a.priority?.replace('_',' ')}</span></div>
                    <div class="da-detail">${a.detail}</div>
                </div>
            </div>`;
        });
    }
    html += '</div>';

    html += '<div class="disaster-grid">';

    if (data.crop_protection) {
        const cp = data.crop_protection;
        html += `<div class="disaster-card">
            <h4>🌾 Crop Protection ${cp.can_save ? '(Salvageable ✅)' : '(Likely Lost ❌)'}</h4>
            <ul>${(cp.measures||[]).map(m => `<li>${m}</li>`).join('')}</ul>
            <p style="margin-top:6px;"><strong>Alternative crops:</strong> ${(cp.alternative_crops||[]).join(', ')}</p>
            <p><strong>Recovery:</strong> ${cp.recovery_timeline || 'N/A'}</p>
        </div>`;
    }

    if (data.financial_advisory) {
        const fa = data.financial_advisory;
        html += `<div class="disaster-card">
            <h4>💰 Financial & Insurance</h4>
            <p><strong>Insurance:</strong> ${fa.insurance_claim || 'N/A'}</p>
            <ul>${(fa.govt_schemes||[]).map(s => `<li>${s}</li>`).join('')}</ul>
            <p><strong>Compensation:</strong> ${fa.compensation || 'N/A'}</p>
        </div>`;
    }

    if (data.water_management) {
        html += `<div class="disaster-card"><h4>💧 Water Management</h4><p>${data.water_management}</p></div>`;
    }

    if (data.post_disaster) {
        html += `<div class="disaster-card"><h4>🔄 Post-Disaster Recovery</h4><ul>${data.post_disaster.map(s => `<li>${s}</li>`).join('')}</ul></div>`;
    }

    html += '</div>';

    if (data.helpline) {
        html += `<div class="disaster-helpline">📞 ${data.helpline}</div>`;
    }

    el.innerHTML = html;
}

// ━━━ AI CHATBOT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupChatbot() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSendBtn');

    sendBtn.addEventListener('click', () => sendChatMessage());
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    if (!question) return;

    const messages = document.getElementById('chatMessages');
    input.value = '';

    // Add user message
    messages.innerHTML += `<div class="chat-msg user"><div class="msg-avatar">👤</div><div class="msg-content"><p>${escapeHTML(question)}</p></div></div>`;

    // Typing indicator
    const typingId = 'typing-' + Date.now();
    messages.innerHTML += `<div class="chat-msg bot" id="${typingId}"><div class="msg-avatar">🧠</div><div class="msg-content"><div class="chat-typing"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div></div></div>`;
    messages.scrollTop = messages.scrollHeight;

    // Build context from last prediction
    const context = {};
    if (lastPredictionData) {
        context.crop = lastPredictionData.crop?.name;
        context.temperature = lastPredictionData.inputs?.temperature;
        context.humidity = lastPredictionData.inputs?.humidity;
        context.rainfall = lastPredictionData.inputs?.rainfall;
        context.ph = lastPredictionData.inputs?.ph;
        context.N = lastPredictionData.inputs?.N;
        context.P = lastPredictionData.inputs?.P;
        context.K = lastPredictionData.inputs?.K;
        context.ndvi = lastPredictionData.ndvi?.ndvi;
        context.location = lastPredictionData.weather?.city || '';
    }

    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, context, language: currentLang })
        });
        const data = await resp.json();

        // Remove typing
        document.getElementById(typingId)?.remove();

        if (data.success) {
            const msgId = 'msg-' + Date.now();
            let botHTML = `<div class="chat-msg bot" id="${msgId}"><div class="msg-avatar">🧠</div><div class="msg-content">`;
            botHTML += `<p>${formatAnswer(data.answer)}</p>`;

            if (data.tips && data.tips.length > 0) {
                botHTML += `<div class="msg-tips"><h5>💡 ${currentLang === 'as' ? 'দ্ৰুত পৰামৰ্শ' : 'Quick Tips'}</h5><ul>${data.tips.map(t => `<li>${t}</li>`).join('')}</ul></div>`;
            }

            botHTML += `<div class="msg-confidence">${currentLang === 'as' ? 'বিশ্বাসযোগ্যতা' : 'Confidence'}: ${data.confidence} | ${currentLang === 'as' ? 'উৎস' : 'Source'}: ${data.source}</div>`;
            botHTML += `<button class="btn-read-aloud" onclick="readAloud(this, '${msgId}')">${t('read_aloud')}</button>`;
            botHTML += '</div></div>';
            messages.innerHTML += botHTML;
        } else {
            messages.innerHTML += `<div class="chat-msg bot"><div class="msg-avatar">🧠</div><div class="msg-content"><p>⚠️ ${data.error || 'Sorry, I could not process that.'}</p></div></div>`;
        }
    } catch (e) {
        document.getElementById(typingId)?.remove();
        messages.innerHTML += `<div class="chat-msg bot"><div class="msg-avatar">🧠</div><div class="msg-content"><p>⚠️ Network error. Please try again.</p></div></div>`;
    }

    messages.scrollTop = messages.scrollHeight;
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatAnswer(text) {
    return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// ━━━ LANGUAGE TOGGLE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupLanguageToggle() {
    document.getElementById('langToggle').addEventListener('click', () => {
        currentLang = currentLang === 'en' ? 'as' : 'en';
        localStorage.setItem('lang', currentLang);
        applyLanguage();
    });
}

function applyLanguage() {
    const isAs = currentLang === 'as';
    document.documentElement.setAttribute('data-lang', currentLang);

    // ── Toggle button label ──────────────────────────────────────────────
    document.getElementById('langText').textContent = isAs ? 'English' : 'অসমীয়া';
    document.getElementById('langToggle').classList.toggle('active', isAs);

    // ── Header nav & badges ──────────────────────────────────────────────
    const aiAnalysisLink = document.querySelector('header nav a[href="/analysis"]');
    if (aiAnalysisLink) aiAnalysisLink.textContent = isAs ? 'AI বিশ্লেষণ' : 'AI Analysis';
    const dashLink = document.querySelector('header nav a[href="/dashboard"]');
    if (dashLink) dashLink.textContent = isAs ? 'ডেচব\'ৰ্ড' : 'Dashboard';

    // Header status pills
    const headerPills = document.querySelectorAll('header .font-data-mono');
    const pillKeys = ['live', 'ml_models', 'satellite', 'gemini_ai'];
    headerPills.forEach((pill, i) => {
        const span = pill.querySelector('span:not(.material-symbols-outlined)');
        if (span && pillKeys[i]) {
            const txt = t(pillKeys[i]);
            // Pill may have icon span; only update text node
            const textNodes = [...pill.childNodes].filter(n => n.nodeType === 3);
            if (textNodes.length) textNodes[textNodes.length-1].textContent = txt;
            else if (span) span.textContent = txt;
        }
    });

    // ── Sidebar header ──────────────────────────────────────────────────
    const sidebarH2 = document.querySelector('#inputPanel h2');
    if (sidebarH2) sidebarH2.textContent = isAs ? 'তথ্য ইনপুট' : 'Data Input';
    const sidebarSub = document.querySelector('#inputPanel p.text-slate-400');
    if (sidebarSub) sidebarSub.textContent = isAs ? 'নিখুঁত কৃষি' : 'Precision Agriculture';

    // ── Mode tabs ────────────────────────────────────────────────────────
    const tabAuto = document.getElementById('tabAuto');
    if (tabAuto) {
        const div = tabAuto.querySelector('div');
        if (div) {
            const spanLabel = div.querySelector('span');
            if (spanLabel) spanLabel.textContent = t('smart_mode');
            const small = div.querySelector('small');
            if (small) small.textContent = t('smart_mode_desc');
        }
    }
    const tabManual = document.getElementById('tabManual');
    if (tabManual) {
        const div = tabManual.querySelector('div');
        if (div) {
            const spanLabel = div.querySelector('span');
            if (spanLabel) spanLabel.textContent = t('sensor_mode');
            const small = div.querySelector('small');
            if (small) small.textContent = t('sensor_mode_desc');
        }
    }
    const tabDisease = document.getElementById('tabDisease');
    if (tabDisease) {
        const div = tabDisease.querySelector('div');
        if (div) {
            const spanLabel = div.querySelector('span');
            if (spanLabel) spanLabel.textContent = isAs ? 'ৰোগ স্কেন' : 'Disease Scan';
            const small = div.querySelector('small');
            if (small) small.textContent = isAs ? 'পাত আপল\'ড কৰক' : 'Upload Leaf';
        }
    }

    // ── Location button ──────────────────────────────────────────────────
    const locBtn = document.getElementById('getLocationBtn');
    if (locBtn && !locBtn.classList.contains('located')) {
        const strong = locBtn.querySelector('strong');
        if (strong) strong.textContent = t('detect_location');
        const small = locBtn.querySelector('small');
        if (small) small.textContent = t('detect_desc');
    }

    // ── Soil group titles (auto section) ────────────────────────────────
    const autoGroupTitles = document.querySelectorAll('#autoSection h3');
    if (autoGroupTitles[0]) autoGroupTitles[0].textContent = isAs ? '📍 আপোনাৰ অৱস্থান' : '📍 Your Location';
    if (autoGroupTitles[1]) autoGroupTitles[1].textContent = t('soil_data');
    const autoGroupHint = document.querySelector('#autoSection p.group-hint');
    if (autoGroupHint) autoGroupHint.textContent = t('soil_hint');

    // ── Manual section titles ────────────────────────────────────────────
    const manualTitles = document.querySelectorAll('#manualSection h3');
    if (manualTitles[0]) manualTitles[0].textContent = t('soil_nutrients');
    if (manualTitles[1]) manualTitles[1].textContent = t('weather_soil');

    // ── Input labels ─────────────────────────────────────────────────────
    const labelMap = {
        'autoN': 'nitrogen', 'autoP': 'phosphorus', 'autoK': 'potassium', 'autoPH': 'soil_ph',
        'inputN': 'nitrogen', 'inputP': 'phosphorus', 'inputK': 'potassium', 'inputPH': 'soil_ph',
        'inputTemp': 'temperature', 'inputHumidity': 'humidity', 'inputRainfall': 'rainfall'
    };
    Object.entries(labelMap).forEach(([id, key]) => {
        const el = document.getElementById(id);
        if (el) {
            const label = el.closest('.input-field')?.querySelector('label');
            if (label) label.textContent = t(key);
        }
    });

    // ── Predict button ───────────────────────────────────────────────────
    const btnText = document.querySelector('#predictBtn .btn-text');
    if (btnText) btnText.textContent = t('analyze_predict');

    // ── Disease upload sidebar ───────────────────────────────────────────
    const detectBtn = document.getElementById('detectBtn');
    if (detectBtn) {
        const span = detectBtn.querySelector('span:not(.material-symbols-outlined)');
        if (!span) detectBtn.childNodes.forEach(n => { if (n.nodeType === 3 && n.textContent.trim()) n.textContent = ' ' + t('detect_disease'); });
    }

    // ── Welcome section ──────────────────────────────────────────────────
    const welH1 = document.querySelector('#welcomeState h1');
    if (welH1) welH1.textContent = t('welcome_title');
    const welDesc = document.querySelector('#welcomeState > .flex + p, #welcomeState p.text-on-surface-variant');
    if (welDesc) welDesc.textContent = t('welcome_desc');
    // Feature card labels under welcome
    const welFeatures = document.querySelectorAll('#welcomeState .glass-card p');
    const featureKeys = ['planet_satellite', 'live_weather', 'crop_ai', 'yield_price', 'disease_ai', 'gemini_advisory'];
    welFeatures.forEach((el, i) => { if (featureKeys[i]) el.textContent = t(featureKeys[i]); });
    // CTA hint
    const welCta = document.querySelector('#welcomeState .glass-card:last-of-type p');
    if (welCta) welCta.innerHTML = t('welcome_cta');

    // ── Section headings ─────────────────────────────────────────────────
    const sectionMap = [
        ['#resultsState > section:nth-of-type(1) h2', isAs ? 'বিশ্লেষণ ফলাফল' : 'Analysis Results'],
        ['#ndviTimelineSection h2', isAs ? t('ndvi_timeline') : '📈 NDVI Crop Health Timeline'],
        ['#ndviSection h2', isAs ? t('ndvi_satellite') : '📡 NDVI Satellite Crop Health'],
        ['#diseaseSection h2', isAs ? t('disease_detection') + ' ফলাফল' : '🌿 Plant Disease Detection Results'],
        ['#chartsSection h2', isAs ? t('analytics') : '📊 Analytics & Visualizations'],
        ['#advisorySection h2', isAs ? t('smart_advisory') : '🧠 Smart Advisory'],
        ['#mandiSection h2', isAs ? t('mandi_prices') : '🏪 Live Mandi Prices'],
        ['#disasterSection h2', isAs ? t('disaster_engine') : '🌊 Disaster Decision Engine'],
        ['#chatSection h2', isAs ? t('ask_farming_ai') : '💬 Ask Farming AI'],
        ['#newsSection h2', isAs ? t('farmer_news') : '📰 Smart Farming News'],
        ['#reportSection h2', isAs ? t('complete_report') : '📄 Complete Report'],
        ['#riskSection h2', isAs ? t('risk_analysis') : '⚡ Risk Analysis'],
    ];
    sectionMap.forEach(([sel, text]) => {
        const el = document.querySelector(sel);
        if (el) el.textContent = text;
    });

    // ── Result card headers ───────────────────────────────────────────────
    const cardHeaders = document.querySelectorAll('.result-card .card-header h3');
    const cardKeys = ['recommended_crop', 'yield_prediction', 'market_price', 'expected_profit', 'market_timing', 'risk_level'];
    cardHeaders.forEach((el, i) => { if (cardKeys[i]) el.textContent = t(cardKeys[i]); });

    // ── Mandi placeholders ────────────────────────────────────────────────
    const mandiCom = document.getElementById('mandiCommodity');
    if (mandiCom) mandiCom.placeholder = t('commodity_placeholder');
    const mandiState = document.getElementById('mandiState');
    if (mandiState) mandiState.placeholder = t('state_placeholder');
    const mandiBtn = document.getElementById('fetchMandiBtn');
    if (mandiBtn) mandiBtn.textContent = t('fetch_prices');

    // ── Disaster button ───────────────────────────────────────────────────
    const disBtn = document.getElementById('runDisasterBtn');
    if (disBtn) disBtn.textContent = t('generate_plan');

    // ── Chat placeholder ──────────────────────────────────────────────────
    const chatInp = document.getElementById('chatInput');
    if (chatInp) chatInp.placeholder = t('chat_placeholder');

    // ── News filter buttons ───────────────────────────────────────────────
    const newsFilters = document.querySelectorAll('.news-filter-btn');
    const newsFilterKeys = ['agriculture_filter', 'weather_filter', 'prices_filter', 'tech_filter', 'assam', 'all_filter'];
    newsFilters.forEach((btn, i) => {
        if (!newsFilterKeys[i]) return;
        const icon = btn.querySelector('span');
        const iconText = icon ? icon.outerHTML : '';
        btn.innerHTML = iconText + ' ' + t(newsFilterKeys[i]);
    });

    // ── Report buttons ────────────────────────────────────────────────────
    const dlBtn = document.getElementById('downloadReport');
    if (dlBtn) dlBtn.textContent = t('download');
    const prBtn = document.getElementById('printReport');
    if (prBtn) prBtn.textContent = t('print');

    // ── Footer ────────────────────────────────────────────────────────────
    const footer = document.querySelector('footer p.text-slate-500.text-xs');
    if (footer) footer.textContent = isAs
        ? '© ২০২৬ AgriPulse AI · স্মাৰ্ট কৃষি সিদ্ধান্ত ব্যৱস্থা · AI + উপগ্ৰহ + বতৰ + চেন্সৰ'
        : '© 2026 AgriPulse AI · Smart Farming Decision System · AI + Satellite + Weather + Sensors';

    // ── data-i18n elements (generic) ─────────────────────────────────────
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (i18n[key]) el.innerHTML = t(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (i18n[key]) el.placeholder = t(key);
    });
}


// ━━━ VOICE INPUT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setupVoiceInput() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (!voiceBtn) {
        console.warn('Voice button not found in DOM');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        voiceBtn.setAttribute('title', t('voice_not_supported'));
        voiceBtn.style.opacity = '0.4';
        voiceBtn.style.cursor = 'not-allowed';
        voiceBtn.disabled = true;
        return;
    }

    // Ensure button is enabled and has proper cursor
    voiceBtn.style.opacity = '1';
    voiceBtn.style.cursor = 'pointer';
    voiceBtn.disabled = false;

    voiceBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (isRecording) {
            stopVoice();
        } else {
            startVoice();
        }
    });
}

function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert('Voice input not supported in your browser');
        return;
    }

    try {
        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = true;
        
        // Try to use appropriate locale for speech recognition
        // Most browsers don't support 'as-IN', so we'll use 'en-IN' for Assamese with fallback
        speechRecognition.lang = currentLang === 'as' ? 'en-IN' : 'en-IN';

        const voiceBtn = document.getElementById('voiceBtn');
        const voiceIcon = document.getElementById('voiceIcon');
        const chatInput = document.getElementById('chatInput');

        if (voiceBtn) voiceBtn.classList.add('recording');
        if (voiceIcon) voiceIcon.textContent = '⏹';
        if (chatInput) chatInput.placeholder = t('speak_now');
        isRecording = true;

        speechRecognition.onstart = () => {
            console.log('🎤 Speech recognition started');
        };

        speechRecognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const isFinal = event.results[i].isFinal;
                transcript += event.results[i][0].transcript;
                if (isFinal) {
                    console.log('📝 Recognized text:', transcript);
                }
            }
            if (transcript && chatInput) chatInput.value = transcript;
        };

        speechRecognition.onerror = (event) => {
            console.error('❌ Speech recognition error:', event.error);
            stopVoice();
            
            // Show user-friendly error message
            let errorMsg = 'Microphone error. Please try again.';
            if (event.error === 'network-error') errorMsg = 'Network error. Check your connection.';
            if (event.error === 'no-speech') errorMsg = 'No speech detected. Please try again.';
            if (event.error === 'audio-capture') errorMsg = 'Microphone not accessible. Check permissions.';
            
            if (chatInput) chatInput.placeholder = errorMsg;
        };

        speechRecognition.onend = () => {
            console.log('🎤 Speech recognition ended');
            stopVoice();
            // DO NOT auto-send - user must click send button
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.focus();
                chatInput.placeholder = t('chat_placeholder');
            }
        };

        speechRecognition.start();
    } catch (error) {
        console.error('Failed to initialize speech recognition:', error);
        stopVoice();
    }
}

function stopVoice() {
    if (speechRecognition) {
        try { speechRecognition.stop(); } catch(e) {}
    }
    isRecording = false;
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceIcon = document.getElementById('voiceIcon');
    const chatInput = document.getElementById('chatInput');
    if (voiceBtn) voiceBtn.classList.remove('recording');
    if (voiceIcon) voiceIcon.textContent = '🎤';
    if (chatInput) chatInput.placeholder = t('chat_placeholder');
}

// ━━━ READ ALOUD (TTS) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function readAloud(btn, msgId) {
    if (!window.speechSynthesis) {
        alert('Text-to-speech not supported in this browser');
        return;
    }

    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        btn.classList.remove('speaking');
        btn.textContent = t('read_aloud');
        return;
    }

    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;

    // Get text content from the message, excluding the button itself
    const content = msgEl.querySelector('.msg-content');
    if (!content) return;

    let textToRead = '';
    content.querySelectorAll('p, li, .msg-confidence').forEach(el => {
        if (!el.classList.contains('btn-read-aloud')) {
            textToRead += el.textContent + '. ';
        }
    });

    if (!textToRead.trim()) {
        console.warn('No text content to read');
        return;
    }

    const utterance = new SpeechSynthesisUtterance(textToRead);
    
    // Set language and voice based on current language
    if (currentLang === 'as') {
        utterance.lang = 'en-IN';  // Use English Indian for Assamese (better support)
    } else {
        utterance.lang = 'en-IN';
    }
    
    // Try to find a suitable voice
    const voices = window.speechSynthesis.getVoices();
    console.log('Available voices:', voices.length, voices.map(v => v.name).slice(0, 5));
    
    if (currentLang === 'as') {
        // For Assamese: try to find India-based voice that can handle regional content
        const preferredVoice = voices.find(v => v.lang.startsWith('en') && v.lang.includes('IN')) ||
                               voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('female')) ||
                               voices.find(v => v.lang.startsWith('en'));
        if (preferredVoice) {
            utterance.voice = preferredVoice;
            console.log('Using voice:', preferredVoice.name);
        }
    } else {
        // For English: use Indian English voice if available
        const enVoice = voices.find(v => v.lang.includes('IN')) ||
                        voices.find(v => v.lang.startsWith('en'));
        if (enVoice) utterance.voice = enVoice;
    }
    
    // Adjust speech parameters for better readability
    utterance.rate = 0.85;    // Slightly slower for clarity
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    btn.classList.add('speaking');
    btn.textContent = t('stop_reading');

    utterance.onstart = () => {
        console.log('🔊 Started reading aloud');
    };

    utterance.onend = () => {
        console.log('🔊 Finished reading');
        btn.classList.remove('speaking');
        btn.textContent = t('read_aloud');
    };

    utterance.onerror = (event) => {
        console.error('❌ Speech synthesis error:', event.error);
        btn.classList.remove('speaking');
        btn.textContent = t('read_aloud');
    };

    window.speechSynthesis.speak(utterance);
}

// Pre-load voices
if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}
