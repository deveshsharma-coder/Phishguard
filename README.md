# PhishGuard - Setup Guide
## Capstone Project

---

## Project Structure
```
phishguard/
├── app.py              ← Flask backend (run this)
├── schema.sql          ← MySQL database setup
├── requirements.txt    ← Python packages to install
├── README.md           ← This file
└── templates/
    └── index.html      ← Frontend (served by Flask)
```

---

## Step 1 — Install Python packages
```bash
pip install -r requirements.txt
```

---

## Step 2 — Set up MySQL database
Open MySQL and run:
```bash
mysql -u root -p < schema.sql
```
OR open the file in phpMyAdmin/MySQL Workbench and execute it.

---

## Step 3 — Configure database in app.py
Open `app.py` and find this section near the top:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # ← put your MySQL password here
    "database": "phishguard_db"
}
```
Update the password to match your MySQL setup.

---

## Step 4 — Run the server
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

## Step 5 — Open in browser
Visit: **http://localhost:5000**

---

## Features
- 🎮 **Quiz** — AI-generated phishing questions via Gemini
- 🔑 **Password Checker** — Strength analysis + crack time estimate
- 🕵️ **Phishing Detector** — Analyze text/image/file for phishing
- 🌐 **URL Safety** — Check if a website is safe
- 👤 **Login/Register** — User accounts with MySQL
- 📊 **Score History** — Your quiz results saved per user

---

## Troubleshooting

**"Connection error" in browser?**
→ Make sure Flask is running: `python app.py`

**MySQL connection error?**
→ Check DB_CONFIG password in app.py
→ Make sure MySQL service is running
→ Make sure you ran schema.sql first

**Gemini API error?**
→ Check your internet connection
→ The API key is already set in app.py

---

*Built with: HTML, CSS, Bootstrap, JavaScript, Python Flask, MySQL, Gemini AI*
