# =============================================================
# PhishGuard Backend - app.py
# Run: python app.py  then visit  http://localhost:5000
# =============================================================

from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
import mysql.connector
import hashlib
import json
import base64
import re
import os
import time
import requests
from groq import Groq

app = Flask(__name__, template_folder='templates')
app.secret_key = 'phishguard_secret_key_do_not_share'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
CORS(app, supports_credentials=True, origins=['http://localhost:5000'])

# ── API SETUP ───────────────────────────────────────────────
GROQ_API_KEY = "" 
groq_client  = Groq(api_key=GROQ_API_KEY)
VT_API_KEY     = ""
VT_HEADERS     = {"x-apikey": VT_API_KEY}


# ── DATABASE CONFIG ────────────────────────────────────────────
# CHANGE these values to match your MySQL setup
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "tiger",          # your MySQL root password
    "database": "phishguard_db"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(password):
    """Simple SHA-256 password hashing with salt"""
    salt = "phishguard2025salt"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def call_ai(prompt):
    """Call Groq API and return cleaned text response"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048
    )
    text = response.choices[0].message.content
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()

# ── SERVE FRONTEND ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ── AUTH ROUTES ────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    name     = data.get('name', '').strip()

    if not username or not password or not name:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    if len(username) < 3:
        return jsonify({'success': False, 'error': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

    try:
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, name) VALUES (%s, %s, %s)",
            (username, hash_password(password), name)
        )
        db.commit()
        user_id = cur.lastrowid
        db.close()

        session['user_id']  = user_id
        session['username'] = username
        session['name']     = name

        return jsonify({'success': True, 'name': name, 'username': username})

    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'error': 'Username already taken. Try another one.'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data     = request.json
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()

    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT id, name, username FROM users WHERE username=%s AND password_hash=%s",
            (username, hash_password(password))
        )
        user = cur.fetchone()
        db.close()

        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['name']     = user['name']
            return jsonify({'success': True, 'name': user['name'], 'username': user['username']})
        else:
            return jsonify({'success': False, 'error': 'Wrong username or password'}), 401

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/me', methods=['GET'])
def me():
    if 'user_id' in session:
        return jsonify({'loggedIn': True, 'name': session['name'], 'username': session['username']})
    return jsonify({'loggedIn': False})

# ── SCORE ROUTES ───────────────────────────────────────────────

@app.route('/api/save-score', methods=['POST'])
def save_score():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.json
    try:
        accuracy = round((data['score'] / data['total']) * 100, 2)
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO scores (user_id, score, total_questions, difficulty, accuracy) VALUES (%s,%s,%s,%s,%s)",
            (session['user_id'], data['score'], data['total'], data['difficulty'], accuracy)
        )
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/my-scores', methods=['GET'])
def my_scores():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT score, total_questions, difficulty, accuracy,
                   DATE_FORMAT(created_at, '%d %b %Y %H:%i') AS date
            FROM scores
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (session['user_id'],))
        rows = cur.fetchall()
        db.close()
        return jsonify({'success': True, 'scores': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── QUIZ GENERATION ───────────────────────────────────

@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    data       = request.json
    difficulty = data.get('difficulty', 'medium')
    count      = min(max(int(data.get('count', 5)), 1), 20)  # clamp 1-20

    prompt = f"""You are creating a phishing detection quiz. Generate exactly {count} quiz questions at '{difficulty}' difficulty.

Return ONLY a raw JSON array — no markdown, no explanation, no code fences.

Each item must follow this exact schema:
{{
  "type": "email",
  "sender": "noreply@example.com",
  "senderName": "Example Bank",
  "subject": "Subject line",
  "body": "HTML message body. Wrap suspicious parts like <span class='red-flag'>bad link</span>",
  "answer": "phishing",
  "explanation": "One-sentence explanation",
  "clues": ["Clue 1", "Clue 2", "Clue 3"]
}}

Difficulty guidelines:
- easy: obvious lottery scams, bad grammar, clearly fake links, obvious red flags
- medium: typosquatting (paypa1.com), SMS spoofing, realistic-looking fakes with subtle issues
- hard: near-perfect fakes with very subtle domain differences or social engineering

Constraints:
- type is one of: email, sms, whatsapp
- answer is exactly: phishing OR legit
- ~60% phishing, ~40% legit per batch
- Use realistic Indian context: SBI, HDFC, ICICI, Amazon India, Paytm, UPI, Aadhaar, SSC, etc.
- clues: 3–5 items explaining the key indicators
- For phishing: mark suspicious URLs/text with <span class='red-flag'>text</span>
"""

    try:
        raw = call_ai(prompt)
        questions = json.loads(raw)
        return jsonify({'success': True, 'questions': questions})
    except json.JSONDecodeError:
        # try extracting JSON array from response as fallback
        try:
            match = re.search(r'\[.*?\]', response.text, re.DOTALL)
            if match:
                return jsonify({'success': True, 'questions': json.loads(match.group())})
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Gemini returned unexpected format. Try again.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── PASSWORD STRENGTH ─────────────────────────────────

@app.route('/api/check-password', methods=['POST'])
def check_password():
    data     = request.json
    password = data.get('password', '')

    if not password:
        return jsonify({'success': False, 'error': 'No password provided'}), 400

    prompt = f"""Analyze password strength for: "{password}"

Return ONLY a raw JSON object, no markdown, no explanation:
{{
  "score": 72,
  "rating": "Strong",
  "crackTimeOffline": "4 years",
  "crackTimeOnline": "centuries",
  "entropy": 48.2,
  "issues": ["No special characters", "Contains dictionary word"],
  "suggestions": ["Add symbols like !@#$", "Mix uppercase and lowercase"],
  "verdict": "Decent password but can be improved",
  "color": "orange"
}}

score: 0–100
rating: "Very Weak" | "Weak" | "Fair" | "Strong" | "Very Strong"
crackTimeOffline: time for fast offline GPU attack
crackTimeOnline: time for slow online attack (rate-limited)
entropy: Shannon entropy in bits
color: "red" (<30) | "orange" (30–59) | "yellow" (60–79) | "green" (80–89) | "cyan" (90+)
"""

    try:
        result = json.loads(call_ai(prompt))
        return jsonify({'success': True, **result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── PHISHING DETECTION ────────────────────────────────

@app.route('/api/check-phishing', methods=['POST'])
def check_phishing():
    text = request.form.get('text', '').strip()
    file = request.files.get('file')

    # ── FILE UPLOAD → VirusTotal file scan ───────────────────
    if file:
        try:
            file_bytes   = file.read()
            file_name    = file.filename
            file_size_kb = len(file_bytes) / 1024

            # submit file to VirusTotal
            upload_resp = requests.post(
                'https://www.virustotal.com/api/v3/files',
                headers=VT_HEADERS,
                files={'file': (file_name, file_bytes)},
                timeout=30
            )
            upload_data = upload_resp.json()

            if 'data' not in upload_data:
                return jsonify({'success': False, 'error': 'VirusTotal could not scan this file'}), 500

            analysis_id = upload_data['data']['id']

            # poll for result (max ~30s)
            analysis = {}
            for attempt in range(10):
                time.sleep(3)
                r = requests.get(
                    f'https://www.virustotal.com/api/v3/analyses/{analysis_id}',
                    headers=VT_HEADERS,
                    timeout=15
                )
                analysis = r.json()
                status = analysis.get('data', {}).get('attributes', {}).get('status', '')
                if status == 'completed':
                    break

            attrs      = analysis.get('data', {}).get('attributes', {})
            stats      = attrs.get('stats', {})
            results    = attrs.get('results', {})
            malicious  = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            undetected = stats.get('undetected', 0)
            harmless   = stats.get('harmless', 0)
            total      = malicious + suspicious + undetected + harmless

            # determine verdict
            if malicious >= 3:
                verdict    = 'PHISHING'
                risk_level = 'CRITICAL'
                confidence = min(95, 60 + malicious * 5)
            elif malicious >= 1 or suspicious >= 3:
                verdict    = 'SUSPICIOUS'
                risk_level = 'HIGH'
                confidence = min(80, 40 + (malicious + suspicious) * 5)
            elif suspicious >= 1:
                verdict    = 'SUSPICIOUS'
                risk_level = 'MEDIUM'
                confidence = 40
            else:
                verdict    = 'LEGITIMATE'
                risk_level = 'LOW'
                confidence = 90

            # collect flagged engines as red flags
            red_flags = []
            safe_indicators = []

            for engine, res in results.items():
                cat = res.get('category', '')
                if cat in ('malicious', 'suspicious'):
                    red_flags.append({
                        'flag':   engine,
                        'detail': f"Flagged as: {res.get('result', cat)}"
                    })

            red_flags = red_flags[:8]  # limit to 8

            if harmless > 0:
                safe_indicators.append(f'{harmless} engines found the file clean')
            if malicious == 0:
                safe_indicators.append('No malicious signatures detected')

            if verdict == 'PHISHING':
                recommendation = f'⛔ DO NOT open or share this file. {malicious} antivirus engines flagged it as malicious. Delete it immediately.'
            elif verdict == 'SUSPICIOUS':
                recommendation = f'⚠️ This file raised suspicion in {malicious + suspicious} engines. Avoid opening it unless you completely trust the source.'
            else:
                recommendation = f'✅ File appears clean. Scanned by {total} engines with no malicious detections. Always stay cautious.'

            return jsonify({
                'success':         True,
                'verdict':         verdict,
                'confidence':      confidence,
                'riskLevel':       risk_level,
                'isPhishing':      verdict == 'PHISHING',
                'category':        f'File scan · {file_name} ({file_size_kb:.1f} KB)',
                'summary':         f'{malicious} malicious · {suspicious} suspicious · {harmless + undetected} clean out of {total} engines',
                'redFlags':        red_flags,
                'safeIndicators':  safe_indicators,
                'recommendation':  recommendation
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ── TEXT INPUT → AI analysis ─────────────────────────
    elif text:
        analysis_prompt = """Analyze the provided text message for phishing indicators.
Return ONLY raw JSON, no markdown, no code fences:
{
  "verdict": "PHISHING",
  "confidence": 91,
  "riskLevel": "HIGH",
  "isPhishing": true,
  "category": "Banking Scam",
  "summary": "Brief one-line summary",
  "redFlags": [
    {"flag": "Urgency pressure", "detail": "Uses Act immediately or lose access"},
    {"flag": "Suspicious URL", "detail": "Link does not match official domain"}
  ],
  "safeIndicators": [],
  "recommendation": "Delete this message. Do NOT click any links."
}
verdict must be one of: PHISHING, LEGITIMATE, SUSPICIOUS, UNKNOWN
riskLevel must be one of: CRITICAL, HIGH, MEDIUM, LOW, SAFE
confidence: 0-100
"""
        try:
            result = json.loads(call_ai(
    f"Analyze this message for phishing:\n\n{text}\n\n{analysis_prompt}"
))
            return jsonify({'success': True, **result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    else:
        return jsonify({'success': False, 'error': 'Please provide text or a file to analyze'}), 400

# ── URL / WEBSITE SECURITY (VIRUS TOTAL) ────────────────────────────

@app.route('/api/check-url', methods=['POST'])
def check_url():
    data = request.json
    url  = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400

    try:
        # ── STEP 1: Submit URL to VirusTotal ──────────────────
        submit = requests.post(
            'https://www.virustotal.com/api/v3/urls',
            headers=VT_HEADERS,
            data={'url': url},
            timeout=15
        )
        submit_data = submit.json()

        if 'data' not in submit_data:
            return jsonify({'success': False, 'error': 'VirusTotal rejected the URL'}), 500

        analysis_id = submit_data['data']['id']

        # ── STEP 2: Poll for results (max 20s) ────────────────
        analysis = {}
        for attempt in range(8):
            time.sleep(3)
            r = requests.get(
                f'https://www.virustotal.com/api/v3/analyses/{analysis_id}',
                headers=VT_HEADERS,
                timeout=15
            )
            analysis = r.json()
            status = analysis.get('data', {}).get('attributes', {}).get('status', '')
            if status == 'completed':
                break

        # ── STEP 3: Parse results ─────────────────────────────
        attrs   = analysis.get('data', {}).get('attributes', {})
        stats   = attrs.get('stats', {})
        results = attrs.get('results', {})

        malicious   = stats.get('malicious', 0)
        suspicious  = stats.get('suspicious', 0)
        undetected  = stats.get('undetected', 0)
        harmless    = stats.get('harmless', 0)
        total_scans = malicious + suspicious + undetected + harmless

        # risk score out of 100
        if total_scans > 0:
            risk_score = round(((malicious * 3 + suspicious * 1) / (total_scans * 3)) * 100)
        else:
            risk_score = 0

        # verdict logic
        if malicious >= 3:
            verdict    = 'DANGEROUS'
            risk_level = 'CRITICAL'
        elif malicious >= 1 or suspicious >= 3:
            verdict    = 'SUSPICIOUS'
            risk_level = 'HIGH'
        elif suspicious >= 1:
            verdict    = 'SUSPICIOUS'
            risk_level = 'MEDIUM'
        else:
            verdict    = 'SAFE'
            risk_level = 'LOW'

        # build per-engine flagged list (top 10 that flagged it)
        flagged_engines = []
        for engine, res in results.items():
            if res.get('category') in ('malicious', 'suspicious'):
                flagged_engines.append({
                    'engine':   engine,
                    'category': res.get('category', ''),
                    'result':   res.get('result', '')
                })
        flagged_engines = flagged_engines[:10]

        # build checks list for the UI
        checks = [
            {
                'name':   'VirusTotal Scan',
                'icon':   '🔬',
                'status': 'fail' if malicious > 0 else ('warning' if suspicious > 0 else 'pass'),
                'detail': f'{malicious} engines flagged as malicious, {suspicious} suspicious out of {total_scans} scanners'
            },
            {
                'name':   'Malicious Detections',
                'icon':   '☠️',
                'status': 'fail' if malicious > 0 else 'pass',
                'detail': f'{malicious} security vendors flagged this URL as malicious'
            },
            {
                'name':   'Suspicious Signals',
                'icon':   '⚠️',
                'status': 'warning' if suspicious > 0 else 'pass',
                'detail': f'{suspicious} vendors found suspicious activity'
            },
            {
                'name':   'Clean Verdicts',
                'icon':   '✅',
                'status': 'pass',
                'detail': f'{harmless + undetected} out of {total_scans} engines found no issues'
            },
            {
                'name':   'HTTPS Check',
                'icon':   '🔒',
                'status': 'pass' if url.startswith('https') else 'warning',
                'detail': 'Uses HTTPS encryption' if url.startswith('https') else 'Does not use HTTPS — data is not encrypted'
            },
            {
                'name':   'Scan Coverage',
                'icon':   '🌐',
                'status': 'pass',
                'detail': f'Analyzed by {total_scans} security engines on VirusTotal'
            }
        ]

        # recommendation text
        if verdict == 'DANGEROUS':
            recommendation = f'⛔ DO NOT visit this website. {malicious} security engines flagged it as malicious. This URL is likely hosting malware, phishing content or scams.'
        elif verdict == 'SUSPICIOUS':
            recommendation = f'⚠️ Approach with caution. {malicious + suspicious} engines found issues. Avoid entering any personal information on this site.'
        else:
            recommendation = '✅ This URL appears clean across all VirusTotal scanners. Still, always be cautious before entering sensitive information on any website.'

        return jsonify({
            'success':        True,
            'url':            url,
            'verdict':        verdict,
            'riskScore':      risk_score,
            'riskLevel':      risk_level,
            'isSafe':         verdict == 'SAFE',
            'category':       f'Scanned by {total_scans} engines',
            'summary':        f'{malicious} malicious · {suspicious} suspicious · {harmless + undetected} clean',
            'checks':         checks,
            'flaggedEngines': flagged_engines,
            'stats':          stats,
            'recommendation': recommendation
        })

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'VirusTotal took too long to respond. Try again.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── TRANSLATION (GROQ) ─────────────────────────────────────────

@app.route('/api/translate', methods=['POST'])
def translate():
    data     = request.json
    texts    = data.get('texts', {})      # dict of key: text
    language = data.get('language', 'Hindi')

    if not texts:
        return jsonify({'success': False, 'error': 'No text provided'}), 400

    # build the prompt
    texts_json = json.dumps(texts, ensure_ascii=False)

    prompt = f"""Translate the following JSON object values into {language}.
Keep all JSON keys exactly as they are — only translate the values.
Keep emojis, HTML tags, and special characters exactly as they are.
Do not add explanations. Return ONLY the raw JSON object, no markdown, no code fences.

{texts_json}"""

    try:
        raw        = call_ai(prompt)
        translated = json.loads(raw)
        return jsonify({'success': True, 'translated': translated, 'language': language})
    except json.JSONDecodeError:
        # try to extract JSON from response as fallback
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                translated = json.loads(match.group())
                return jsonify({'success': True, 'translated': translated, 'language': language})
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Translation failed. Try again.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── RUN ────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*55)
    print("  PhishGuard Server Starting...")
    print("  Visit: http://localhost:5000")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)
