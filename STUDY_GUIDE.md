# 📘 מדריך לימוד – להבין את הפרויקט מהיסוד

המטרה: שתוכל לעמוד מול המרצה ולהסביר כל שורה. קרא לפי הסדר.

---

## חלק 0 – מושגי יסוד ב-30 שניות כל אחד

- **Image (אימג')** – "תבנית" קפואה: מערכת קבצים + הוראת הפעלה. נבנית מ-Dockerfile. דומה ל-class.
- **Container** – מופע רץ של Image. דומה ל-object. אפשר להריץ כמה מאותו אימג'.
- **Dockerfile** – מתכון לבניית Image. כל שורה (`FROM`, `COPY`, `RUN`...) יוצרת **Layer**.
- **Layer cache** – Docker זוכר כל שכבה. אם שורה וכל מה שלפניה לא השתנו – לא בונה אותה שוב.
- **Docker Compose** – קובץ YAML שמגדיר כמה containers ביחד (שירותים, רשת, volumes) ומרים הכול בפקודה אחת.
- **Volume** – תיקייה שמנוהלת ע"י Docker ו**חיה מחוץ ל-container**. מוחקים container – הנתונים נשארים.
- **Network** – Compose יוצר רשת פרטית אחת, וכל שירות מקבל **שם DNS = שם השירות** (`redis`, `api`, `web`).
- **Port mapping** `"8080:80"` – **צד שמאל = המחשב שלך (host)**, צד ימין = בתוך ה-container.
- **CI/CD** – Continuous Integration / Delivery: בכל push שרת של GitHub בונה ובודק את הקוד אוטומטית (ובונוס – מפרסם).
- **Registry** – "מחסן" של אימג'ים. Docker Hub הוא אחד, **ghcr.io** הוא של GitHub.

---

## חלק 1 – התקנה ממש מאפס (Windows)

1. **Docker Desktop** – הורדה מ-docker.com, התקנה, אתחול. אם מבקש WSL 2 – לאשר (פותח PowerShell כמנהל ומריץ `wsl --install` אם צריך). פותחים את Docker Desktop ומחכים ל-"Engine running" (ריבוע ירוק בפינה).
2. **Git** – git-scm.com → Download for Windows → Next, Next, Next.
3. **VS Code** – code.visualstudio.com. מומלץ להתקין את התוסף "Docker".
4. הגדרת Git (פעם אחת, ב-PowerShell):
   ```powershell
   git config --global user.name "השם שלך"
   git config --global user.email "המייל של GitHub"
   ```

### יצירת ה-Repository ועבודת צוות (חובה: commit מכל חבר צוות!)
1. חבר צוות אחד: GitHub → New repository → שם `smart-parking` → Public → Create.
2. Settings → Collaborators → Add people → מוסיפים את שאר הצוות.
3. מחלצים את ה-ZIP לתיקייה, ובתוכה ב-PowerShell:
   ```powershell
   git init
   git add .
   git commit -m "Initial project structure"
   git branch -M main
   git remote add origin https://github.com/<user>/smart-parking.git
   git push -u origin main
   ```
   (בפעם הראשונה ייפתח חלון התחברות ל-GitHub בדפדפן.)
4. כל שאר חברי הצוות: `git clone ...`, עושים שינוי אמיתי (למשל מוסיפים את השם שלהם בטבלת הצוות ב-README, משנים הודעת נחיתה, מוסיפים סוג ספינה), ואז:
   ```powershell
   git add .
   git commit -m "Add my welcome messages"
   git pull --rebase
   git push
   ```
5. לשונית **Actions** ב-GitHub → רואים את ה-workflow רץ. ירוק = עבר.
6. בונוס: אחרי push ל-main, בדף הראשי של ה-repo בצד ימין → **Packages** – יופיעו `smart-parking-api` ו-`smart-parking-web`.
   אם ה-push נכשל בהרשאות: Settings → Actions → General → Workflow permissions → "Read and write permissions".

### הרצה מקומית
```powershell
docker compose up -d --build     # בונה ומרים ברקע
docker compose ps                # מה רץ ומה הסטטוס (healthy?)
docker compose logs -f api       # לוגים חיים של ה-API (Ctrl+C ליציאה)
docker compose down              # עוצר ומוחק containers + רשת (ה-volume נשאר!)
```
פותחים http://localhost:8080 ושולחים רכבים: `powershell -ExecutionPolicy Bypass -File .\scripts\camera.ps1`

---

## חלק 2 – זרימת המידע (הכי חשוב להבין!)

1. **המצלמה** (`camera.ps1`) שולחת `POST http://localhost:5000/api/entry` עם JSON `{"plate":"12-345-67"}`.
   הפורט 5000 במחשב ממופה ל-5000 ב-container של ה-API.
2. **ה-API** מנרמל את הלוחית לספרות בלבד (`1234567`), בודק שהיא לא כבר בחניון ושיש מקום, ושומר ב-Redis.
3. **הדפדפן** טוען את `http://localhost:8080` → מגיע ל-Nginx (פורט 80 ב-container) → מקבל `index.html`.
4. ה-JavaScript מריץ `fetch("/api/cars")` כל 3 שניות. זה URL **יחסי**, אז זה הולך ל-`localhost:8080/api/cars` → **Nginx** רואה `/api/` ומעביר (proxy) ל-`http://api:5000/api/cars` דרך הרשת הפנימית.
5. ה-API קורא מ-Redis ומחזיר JSON, וה-JS בונה מחדש את הרשימה ב-DOM.

> 💡 למה Nginx מעביר את `/api`? כי אחרת הדפדפן היה פונה מ-8080 ל-5000 = Origin אחר = **CORS**. ככה הכול מאותו מקור.

---

## חלק 3 – הסבר קובץ אחר קובץ

### `docker-compose.yml`
| שורה | הסבר |
|---|---|
| `services:` | רשימת השירותים (containers). |
| `image: redis:7-alpine` | אימג' מוכן מ-Docker Hub. `alpine` = לינוקס זעיר (~5MB). |
| `command: redis-server --appendonly yes --appendfsync everysec` | מפעיל **AOF**: כל פקודת כתיבה נרשמת לקובץ `appendonly` בתוך `/data`. `everysec` = כתיבה לדיסק פעם בשנייה. |
| `volumes: - redis-data:/data` | ה-volume בשם `redis-data` מחובר לתיקייה `/data` שבה Redis שומר את הקבצים. **זה מה שמציל את הנתונים.** |
| `healthcheck: redis-cli ping` | Docker בודק כל 5 שניות אם Redis עונה `PONG`. |
| Redis בלי `ports:` | אי אפשר לגשת אליו מבחוץ – רק ה-API ברשת הפנימית. אבטחה. |
| `build: ./api` | לבנות אימג' מה-Dockerfile שבתיקייה `api`. |
| `environment:` | משתני סביבה שה-Python קורא עם `os.getenv`. משנים קיבולת/מחיר בלי לגעת בקוד. |
| `REDIS_HOST: redis` | שם השירות = שם המחשב ברשת של Compose. |
| `depends_on: redis: condition: service_healthy` | ה-API מתחיל רק אחרי שה-healthcheck של Redis עבר. |
| `ports: "8080:80"` | host:container. בדפדפן 8080, Nginx מאזין בפנים על 80. |
| `restart: unless-stopped` | אם ה-container קורס – Docker מרים אותו שוב (אלא אם עצרת ידנית). |
| `volumes: redis-data:` בסוף | הצהרה על named volume. השם בפועל: `<שם-תיקייה>_redis-data`. |

### `api/Dockerfile`
| שורה | הסבר |
|---|---|
| `FROM python:3.12-slim` | אימג' בסיס עם Python. `slim` = בלי כלים מיותרים → קטן יותר. |
| `ENV PYTHONUNBUFFERED=1` | ההדפסות יוצאות מיד ל-`docker logs` ולא נתקעות ב-buffer. |
| `WORKDIR /app` | תיקיית העבודה בתוך ה-container (נוצרת אם לא קיימת). |
| `COPY requirements.txt .` ואז `RUN pip install` ורק **אחר כך** `COPY app.py` | **Layer caching**: אם שיניתי רק את `app.py`, שכבת ה-pip לא נבנית מחדש → build מהיר. |
| `--no-cache-dir` | pip לא שומר cache → אימג' קטן יותר. |
| `useradd` + `USER appuser` | לא מריצים כ-root. עיקרון Least Privilege. |
| `EXPOSE 5000` | **תיעוד בלבד** – לא פותח פורט! הפתיחה היא ב-`ports` של compose. |
| `HEALTHCHECK` | Docker בודק את `/api/health` (שעושה גם `PING` ל-Redis). |
| `CMD ["gunicorn", ... "app:app"]` | הפקודה שרצה כשה-container עולה. `app:app` = קובץ `app.py`, משתנה `app`. |

### `web/Dockerfile` + `nginx.conf`
- `FROM nginx:1.27-alpine` – Nginx מוכן.
- `COPY nginx.conf /etc/nginx/conf.d/default.conf` – מחליף את הגדרת ברירת המחדל.
- `COPY index.html /usr/share/nginx/html/` – התיקייה ש-Nginx מגיש ממנה.
- אין `CMD` – יורש מהאימג' הבסיסי (`nginx -g 'daemon off;'` – רץ בחזית כדי שה-container לא ייסגר).
- `location /` → קבצים סטטיים. `location /api/` → `proxy_pass http://api:5000` (Reverse Proxy).

### `api/app.py` – מבני הנתונים ב-Redis
| Key | סוג | תוכן |
|---|---|---|
| `parking:parked` | **Sorted Set** | member = לוחית, score = זמן כניסה (timestamp). ממוין לפי זמן. |
| `car:1234567` | **Hash** | `plate`, `entry_time`, `ship_class`, `message` |
| `parking:history` | **List** | אירועי כניסה/יציאה ב-JSON, `LTRIM` שומר 50 אחרונים |
| `parking:total_entries` | String (מונה) | `INCR` בכל כניסה |
| `parking:revenue` | String (float) | `INCRBYFLOAT` בכל יציאה |

**Endpoints:**
- `POST /api/entry` – מצלמה. `400` לוחית לא תקינה, `409` כבר בחניון / חניון מלא, `201` נוצר.
- `GET /api/cars` – לוח הבקרה. מחשב לכל רכב דקות ומחיר נוכחי.
- `POST /api/exit/<plate>` – שחרור. `404` אם לא קיים. מוסיף להכנסות.
- `GET /api/history`, `GET /api/health`.

**חישוב מחיר:** עד 15 דק' = 0. אחרת `ceil(דקות/60) * 12`. כלומר 16 דק' = 12, 61 דק' = 24.

**WATCH / MULTI / EXEC (שאלה אהובה על מרצים):**
`WATCH parking:parked` → בודקים כמות → `MULTI` → פקודות נכנסות לתור → `EXEC`.
אם מישהו אחר שינה את `parking:parked` בין ה-WATCH ל-EXEC, ה-EXEC נכשל (`WatchError`) והלולאה מנסה שוב.
ככה שתי מצלמות לא יתפסו ביחד את המקום האחרון. זה נקרא **Optimistic Locking**.

**`@app.errorhandler(redis.exceptions.ConnectionError)`** – אם Redis נפל, מחזירים `503` מסודר במקום קריסה.

### `web/index.html` – ה-JavaScript
- `fetch()` – בקשת רשת אסינכרונית. `await` מחכה לתשובה בלי לתקוע את הדף.
- `setInterval(refresh, 3000)` – **Polling**: שואלים את השרת כל 3 שניות.
- `Promise.all([...])` – שתי בקשות במקביל (`cars` + `history`).
- **Dynamic DOM**: `document.createElement`, `replaceChildren`, `appendChild` – בונים את הרשימה מחדש.
- `textContent` ולא `innerHTML` – מונע **XSS** (אם מישהו ישלח קוד HTML כנתון, הוא יוצג כטקסט ולא ירוץ).
- `knownPlates` – Set שזוכר אילו לוחיות כבר הוצגו, כדי להפעיל אנימציית "נחיתה" רק לחדשים.
- Dark mode – מחלקת CSS `dark` על ה-body שמחליפה משתני CSS (`--bg`, `--text`...), נשמר ב-`localStorage`.
- Easter egg – מאזין ל-`keydown` ובודק רצף Konami.

### `.github/workflows/ci.yml`
| חלק | הסבר |
|---|---|
| `on: push / pull_request / workflow_dispatch` | מתי רץ: כל push, כל PR, ולחיצה ידנית. |
| `runs-on: ubuntu-latest` | מכונה וירטואלית של GitHub שכבר יש בה Docker. |
| `actions/checkout@v4` | מוריד את הקוד שלנו למכונה. |
| `docker compose config --quiet` | בודק שה-YAML תקין. |
| `docker compose build` | **הדרישה המרכזית** – בדיקת תקינות build. |
| Wait for API | לולאה עד 30 פעמים × 2 שניות עד ש-`/api/health` עונה. |
| Smoke test | POST דרך Nginx (8080) ובדיקה עם `grep` שהלוחית מופיעה ב-GET. |
| Persistence test | `down` (בלי `-v`) → `up` → בודק שהרכב עדיין שם. |
| `if: always()` | ניקוי רץ גם אם שלב קודם נכשל. |
| `needs: build-and-test` | ה-publish רץ רק אם הבדיקות עברו. |
| `if: ... refs/heads/main` | מפרסמים רק מ-main. |
| `permissions: packages: write` | נותן ל-`GITHUB_TOKEN` הרשאה לדחוף ל-ghcr. |
| `strategy: matrix: service: [api, web]` | מריץ את אותם צעדים פעמיים – לכל אימג'. |
| `docker/login-action` + `secrets.GITHUB_TOKEN` | התחברות מאובטחת. הטוקן נוצר אוטומטית לכל ריצה ופג בסופה – לא צריך להגדיר secret ידנית. |
| `docker/metadata-action` | מייצר תגיות: `latest`, `v1.0.<מספר ריצה>`, `sha-abc1234`. גם הופך את השם ל-lowercase (חובה ב-ghcr). |
| `docker/build-push-action` | בונה ודוחף. |

---

## חלק 4 – תסריט לדמו (5–10 דקות)

1. **פתיחה (30 ש')**: "בנינו חניון חלליות. 3 מיקרו-סרביסים ב-Compose." – להראות את הדיאגרמה ב-README.
2. `docker compose up -d --build` ואז `docker compose ps` – להראות שכולם `healthy`.
3. לפתוח http://localhost:8080. להריץ `camera.ps1` – לראות ספינות "נוחתות" **בלי רענון**.
4. להריץ `camera.ps1 -Count 12` – **באנר FULL CAPACITY** אדום מהבהב 🚨.
5. ללחוץ "שחרור ספינה" – להראות חישוב תשלום והכנסות.
6. Dark mode, ואז לוחית `42-424-24` ו-Konami code (↑↑↓↓←→←→BA) – רגע הצחוק.
7. **הוכחת Persistence**: `docker compose down` → להראות ב-`docker ps` שאין כלום → `docker compose up -d` → רענון → הנתונים שם! להסביר: AOF + volume.
8. GitHub → Actions (ריצה ירוקה) → Packages (האימג'ים ב-ghcr).

**טיפ:** לפני הדמו להריץ `docker compose pull` / build פעם אחת כדי שלא יחכה להורדות באינטרנט של הכיתה.

---

## חלק 5 – פקודות שכדאי לדעת בעל פה
```powershell
docker compose up -d --build        # בנייה + הרצה ברקע
docker compose ps                   # סטטוס
docker compose logs -f api          # לוגים
docker compose down                 # עצירה (volume נשאר)
docker compose down -v              # עצירה + מחיקת volumes ⚠️
docker volume ls                    # רשימת volumes
docker volume inspect smart-parking_redis-data
docker exec -it parking-redis redis-cli      # להיכנס ל-Redis
  > ZRANGE parking:parked 0 -1 WITHSCORES
  > HGETALL car:1234567
  > KEYS *
docker exec -it parking-api sh      # shell בתוך ה-API
docker images                       # אימג'ים מקומיים
```

## חלק 6 – תקלות נפוצות
| תקלה | פתרון |
|---|---|
| `error during connect ... docker_engine` | Docker Desktop לא פתוח. לפתוח ולחכות ל-"Engine running". |
| `port is already allocated` | משהו אחר תופס 8080/5000. לשנות לצד שמאל, למשל `"8081:80"`. |
| `camera.ps1 cannot be loaded ... execution policy` | להריץ עם `powershell -ExecutionPolicy Bypass -File ...` |
| לוח הבקרה אומר "אין חיבור" | `docker compose logs api` – כנראה ה-API קרס או Redis לא עלה. |
| publish ב-Actions נכשל עם `denied` | Settings → Actions → General → Read and write permissions. |
