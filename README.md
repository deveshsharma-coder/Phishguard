# 🛡️ PhishGuard — Cyber Awareness Trainer v2.0
### Project

---

## 📌 What is PhishGuard?

PhishGuard is a full-stack web application that trains users to identify phishing scams and stay safe online. It uses **Groq AI** to generate unique quiz questions every session, **VirusTotal** to scan URLs and files for real threats, and **MySQL** to store user scores and login data.

---

## 🚀 Features

| Feature | Description | Powered By |
|---|---|---|
| 🎮 **AI Quiz** | Generates fresh phishing questions every session based on difficulty and count selected by user | Groq AI |
| 🔑 **Password Checker** | Analyzes password strength, crack time estimate, entropy, issues and suggestions | Groq AI |
| 🕵️ **Phishing Detector** | Paste any suspicious text message to check if it's phishing | Groq AI |
| 📎 **File Scanner** | Upload image, PDF or document to scan for malware and phishing | VirusTotal |
| 🌐 **URL Safety Checker** | Check any website URL against 90+ security engines | VirusTotal |
| 👤 **Login / Register** | Unique username and password based account system | MySQL |
| 📊 **Score History** | Saves quiz results per user, shows best accuracy and games played | MySQL |
| 🌍 **Multi-Language** | Translate entire UI to 14 languages including all major Indian languages | Groq AI |
| 🎉 **Celebration** | Canvas confetti animation when quiz completes, streak toast on 3+ in a row | JavaScript |

---

## 🗂️ Project Structure

```
phishguard/
├── app.py                  ← Flask backend (run this to start server)
├── schema.sql              ← MySQL database setup (run once)
├── requirements.txt        ← Python packages list
├── README.md               ← This file
└── templates/
    └── index.html          ← Complete frontend (HTML + CSS + JS)
```

---

## 🛠️ Tech Stack

**Frontend**
- HTML5, CSS3, JavaScript (ES5)
- Bootstrap 3.4.1
- Google Fonts (Rajdhani, Share Tech Mono, Inter)

**Backend**
- Python 3.x
- Flask 3.0.3
- Flask-CORS

**Database**
- MySQL 8.0
- mysql-connector-python

**AI / APIs**
- Groq API — `llama-3.3-70b-versatile` model
- VirusTotal API v3

---

## ⚙️ Setup Guide

### Step 1 — Install Python packages

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install Flask flask-cors mysql-connector-python groq requests Werkzeug
```

---

### Step 2 — Set up MySQL database

Open **MySQL Command Line Client** from Start Menu, enter your password, then run:

```sql
CREATE DATABASE phishguard_db;
USE phishguard_db;
```

Then create the tables:

```sql
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scores (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    score           INT NOT NULL,
    total_questions INT NOT NULL,
    difficulty      VARCHAR(20) NOT NULL,
    accuracy        DECIMAL(5,2) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Verify tables were created:
```sql
SHOW TABLES;
```

You should see:
```
+------------------------+
| Tables_in_phishguard_db|
+------------------------+
| scores                 |
| users                  |
+------------------------+
```

---

### Step 3 — Configure database password in app.py

Open `app.py` and find this section:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",      # ← put your MySQL password here
    "database": "phishguard_db"
}
```

If you set no password during MySQL install, leave it as `""`.

---

### Step 4 — Run the server

```bash
python app.py
```

You should see:
```
=======================================================
  PhishGuard Server Starting...
  Visit: http://localhost:5000
=======================================================
```

---

### Step 5 — Open in browser

Visit: **http://localhost:5000**

---

## 🔑 API Keys (already configured in app.py)

| API | Variable | Free Limit |
|---|---|---|
| **Groq** | `GROQ_API_KEY` | 14,400 requests/day |
| **VirusTotal** | `VT_API_KEY` | 4 requests/minute |

> To get a new Groq key: `console.groq.com` → Sign up → API Keys
>
> To get a new VirusTotal key: `virustotal.com` → Profile → API Key

---

## 🌍 Supported Languages

| Language | Flag | Direction |
|---|---|---|
| English | 🇬🇧 | LTR |
| Hindi | 🇮🇳 | LTR |
| Tamil | 🇮🇳 | LTR |
| Telugu | 🇮🇳 | LTR |
| Bengali | 🇮🇳 | LTR |
| Marathi | 🇮🇳 | LTR |
| Gujarati | 🇮🇳 | LTR |
| Punjabi | 🇮🇳 | LTR |
| Spanish | 🇪🇸 | LTR |
| French | 🇫🇷 | LTR |
| German | 🇩🇪 | LTR |
| Arabic | 🇸🇦 | **RTL** (auto) |
| Chinese | 🇨🇳 | LTR |
| Japanese | 🇯🇵 | LTR |

> Translations are **cached in browser memory** — each language only calls the API once per session.

---

## 🌐 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serve frontend |
| `POST` | `/api/register` | Create new account |
| `POST` | `/api/login` | Login with username + password |
| `POST` | `/api/logout` | Logout current user |
| `GET` | `/api/me` | Check if user is logged in |
| `POST` | `/api/save-score` | Save quiz result to database |
| `GET` | `/api/my-scores` | Fetch user's score history |
| `POST` | `/api/generate-questions` | Generate quiz questions via Groq |
| `POST` | `/api/check-password` | Analyze password strength via Groq |
| `POST` | `/api/check-phishing` | Check text (Groq) or file (VirusTotal) |
| `POST` | `/api/check-url` | Scan URL via VirusTotal |
| `POST` | `/api/translate` | Translate UI strings via Groq |

---

## 📝 How Each Feature Works

### 🎮 Quiz
1. User enters name, selects number of questions (1–20) and difficulty (Easy / Medium / Hard)
2. Frontend sends request to `/api/generate-questions`
3. Groq AI generates realistic Indian-context phishing messages — email, SMS, WhatsApp
4. User identifies each message as PHISHING or LEGITIMATE
5. Clues and explanation shown after each answer
6. Confetti celebration fires on completion
7. Score saved to MySQL if user is logged in

### 🔑 Password Checker
1. User types a password into the input field
2. Live 5-segment strength bar updates instantly (client-side, no API)
3. On clicking Analyze, Groq AI returns:
   - Score out of 100 with animated arc
   - Crack time for offline GPU attack and online rate-limited attack
   - Shannon entropy in bits
   - List of issues found and improvement suggestions

### 🕵️ Phishing Detector
- **Text tab** → paste any message → Groq AI analyzes for phishing patterns, returns verdict, confidence, red flags and recommendation
- **File tab** → upload image/PDF/document → VirusTotal scans across 70+ antivirus engines, returns per-engine results

### 🌐 URL Safety
1. User enters any URL
2. URL submitted to VirusTotal scan endpoint
3. Backend polls VirusTotal every 3 seconds until scan completes (max 30s)
4. Returns overall verdict, risk score 0–100, 6 security checks, and a table of flagged engines

### 👤 Login / Register
- Passwords hashed with SHA-256 + salt before storing in MySQL
- Sessions managed by Flask signed cookies
- Login persists across page reloads (session check on load)

### 📊 Score History
- Every completed quiz saves: score, total questions, difficulty, accuracy, timestamp
- Profile page shows last 10 games and best accuracy ever

### 🌍 Multi-Language
1. User picks a language from the 🌐 dropdown in the header
2. All UI text strings (buttons, labels, headings) sent as JSON to `/api/translate`
3. Groq translates entire batch in one API call
4. DOM updated with translated text instantly
5. Result cached in browser — no API call if same language is selected again
6. Arabic automatically switches to RTL layout

---

## ❗ Troubleshooting

| Problem | Fix |
|---|---|
| `TemplateNotFound: index.html` | Make sure `index.html` is inside a folder named `templates` right next to `app.py` |
| `Connection error` in browser | Make sure Flask is running: `python app.py` |
| `Access denied` MySQL error | Wrong password in `DB_CONFIG` in app.py |
| `Table doesn't exist` error | Run the `CREATE TABLE` SQL commands from Step 2 |
| `Can't connect to MySQL` | MySQL service not running → open Services.msc → start MySQL80 |
| Login greys screen, no response | You must open `http://localhost:5000` — do NOT open the HTML file directly |
| Groq API limit hit | Free tier: 14,400 requests/day. Wait till next day or create new key at `console.groq.com` |
| VirusTotal rate limit | Free tier: 4 requests/minute. Wait 60 seconds and try again |
| Translation not working | Check that `/api/translate` route is in `app.py` and Groq key is valid |
| Quiz generation fails | Check Groq API key in `app.py` and internet connection |

---

## 🔒 Security Notes

- Passwords stored as **SHA-256 hash with salt** — never plain text
- All API keys live **only in `app.py`** (server-side) — never sent to browser
- Sessions use Flask's signed cookie with a secret key
- VirusTotal and Groq calls are all made server-side

---

## 📦 requirements.txt

```
Flask==3.0.3
flask-cors==4.0.1
mysql-connector-python==8.4.0
groq==0.9.0
requests==2.32.3
Werkzeug==3.0.3
```

---

## 👨‍💻 Built With

```
Frontend  →  HTML + CSS + Bootstrap 3 + JavaScript
Backend   →  Python + Flask + MySQL
AI        →  Groq API (llama-3.3-70b-versatile)
Security  →  VirusTotal API v3
```

---

*PhishGuard © 2026 | Never share your OTP, PIN or passwords with anyone.*
