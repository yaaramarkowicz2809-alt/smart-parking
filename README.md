# 🛸 Galactic Spaceport – Smart Parking License Plate Tracker

![CI](../../actions/workflows/ci.yml/badge.svg)

מערכת לניהול חניון חלליות חכם (Track 2 – Full Stack DevOps).
מצלמת IoT מפענחת לוחית רישוי ושולחת `HTTP POST` לשרת ה-API, הנתונים נשמרים ב-Redis,
ולוח בקרה (Nginx + JavaScript) מציג בזמן אמת את הספינות בחניון – בלי לרענן את העמוד.

## ארכיטקטורה

```
 📷 Camera (camera.ps1 / camera.sh)
        │  POST /api/entry  (port 5000)
        ▼
 ┌──────────────┐  /api/*  ┌──────────────┐        ┌──────────────────┐
 │  web (Nginx) │ ───────► │ api (Flask)  │ ─────► │ redis (AOF)      │
 │  :8080 → 80  │  proxy   │  :5000       │        │  volume: /data   │
 └──────────────┘          └──────────────┘        └──────────────────┘
        ▲
        │ fetch() every 3s
   🖥️ Browser – http://localhost:8080
```

| שירות | Image | תפקיד |
|---|---|---|
| `web` | `nginx:1.27-alpine` + קבצים שלנו | מגיש את `index.html` ומעביר (reverse proxy) את `/api/` לשרת ה-API |
| `api` | `python:3.12-slim` + Flask + gunicorn | `POST /api/entry`, `GET /api/cars`, `POST /api/exit/<plate>`, `GET /api/history`, `GET /api/health` |
| `redis` | `redis:7-alpine` | מסד נתונים, שמירה לדיסק עם AOF בתוך Volume בשם `redis-data` |

## ✨ התוספת האישית שלנו
- **נושא: חניון חלליות** – כל רכב מקבל "סוג ספינה" והודעת נחיתה מצחיקה.
- **חישוב מחיר חנייה** – 15 דקות ראשונות חינם, אחר כך 12 קרדיטים לכל שעה שהתחילה.
- **Full Capacity Alert** – באנר אדום מהבהב כשהחניון מלא (10 מקומות), וה-API מחזיר `409`.
- **כפתור "שחרור ספינה"** – מחשב תשלום, מוחק מהחניון ומוסיף להכנסות.
- **Dark Mode** – נשמר ב-localStorage.
- **Easter Eggs** 🥚 – לוחית `42-424-24`, ו-Konami code (↑↑↓↓←→←→BA) בלוח הבקרה.

## 🧰 התקנה מאפס (Windows)
1. **Docker Desktop** – הורדה מ-https://www.docker.com/products/docker-desktop , התקנה, אתחול מחשב.
   בהפעלה הראשונה הוא עשוי לבקש להתקין **WSL 2** – לאשר. לוודא שמופיע "Engine running".
2. **Git** – https://git-scm.com/download/win (ברירות מחדל בהתקנה).
3. **VS Code** (מומלץ) – https://code.visualstudio.com
4. חשבון **GitHub** לכל חבר צוות.

בדיקה ב-PowerShell:
```powershell
docker --version
docker compose version
git --version
```

## 🚀 הרצה
```powershell
git clone https://github.com/<user>/<repo>.git
cd <repo>
docker compose up -d --build
```
- לוח בקרה: http://localhost:8080
- API ישירות: http://localhost:5000/api/cars

שליחת רכבים מה"מצלמה":
```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\scripts\camera.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\camera.ps1 -Count 12   # למלא את החניון
# Mac / Linux / Git Bash
./scripts/camera.sh
```

## 💾 הוכחת Persistence (לדמו)
```powershell
.\scripts\camera.ps1 -Count 3       # להכניס רכבים
docker compose down                 # מוחק containers + network, אבל לא את ה-volume
docker compose up -d
# לרענן את http://localhost:8080 - הרכבים עדיין שם ✅
docker volume ls                    # רואים את <project>_redis-data
```
⚠️ `docker compose down -v` **כן** מוחק את ה-volume – והנתונים ייעלמו.

## 🔁 CI/CD
קובץ: `.github/workflows/ci.yml`
- **build-and-test** (בכל push ו-PR): בדיקת קובץ compose, build לכל האימג'ים, הרמת המערכת,
  בדיקת POST/GET דרך Nginx, ובדיקת persistence עם down/up.
- **publish** (בונוס, רק ב-push ל-`main` ואחרי שהבדיקות עברו): התחברות ל-`ghcr.io` עם `GITHUB_TOKEN`,
  תיוג `latest`, `v1.0.<run_number>`, `sha-xxxxxxx` ו-push של `-api` ו-`-web` ל-GitHub Container Registry.

## 📡 API
| Method | Endpoint | תיאור | תגובות |
|---|---|---|---|
| POST | `/api/entry` | `{"plate":"12-345-67"}` – כניסת רכב | 201, 400, 409 |
| GET | `/api/cars` | רשימת רכבים + סטטיסטיקות | 200 |
| POST | `/api/exit/<plate>` | שחרור רכב + חישוב תשלום | 200, 404 |
| GET | `/api/history` | 20 האירועים האחרונים | 200 |
| GET | `/api/health` | בדיקת חיים (כולל Redis) | 200, 503 |

## 👥 צוות
| שם | אחריות |
|---|---|
| חבר/ה 1 | API + Redis |
| חבר/ה 2 | Frontend + Nginx |
| חבר/ה 3 | CI/CD + תיעוד |

## 📁 מבנה
```
├── docker-compose.yml
├── api/            Dockerfile, app.py, requirements.txt
├── web/            Dockerfile, nginx.conf, index.html
├── scripts/        camera.ps1, camera.sh
├── .github/workflows/ci.yml
├── AI_USAGE.md     ARCHITECTURE.md     STUDY_GUIDE.md
```
