# ARCHITECTURE.md – החלטות ארכיטקטוניות

| החלטה | למה |
|---|---|
| **Python + Flask** ל-API | קוד קצר וקריא, קל להסביר ב-Code Review. |
| **gunicorn** ולא `app.run()` | השרת המובנה של Flask מיועד לפיתוח בלבד. gunicorn מריץ 2 workers במקביל. |
| **Nginx כ-Reverse Proxy** ל-`/api/` | Origin אחד לדפדפן → אין CORS. ה-API גם לא חייב להיות חשוף החוצה. |
| **Redis בלי `ports`** | אבטחה: רק שירותים ברשת הפנימית של Compose יכולים לגשת אליו. |
| **AOF (`--appendonly yes`)** | כל כתיבה נרשמת לקובץ. עם `everysec` מאבדים לכל היותר שנייה של נתונים בקריסה. RDB (snapshots) עלול לאבד דקות. |
| **Named volume `redis-data`** | מנוהל ע"י Docker, עובד זהה ב-Windows/Mac/Linux, שורד `down`. |
| **Sorted Set** לרכבים בחניון | score = זמן כניסה → מקבלים רשימה ממוינת ובדיקת קיום ב-O(log N). |
| **Hash** לפרטי רכב | שדות מרובים לכל רכב (`plate`, `entry_time`, `ship_class`, `message`). |
| **List** ליומן אירועים + `LTRIM` | שומר רק 50 אחרונים – הזיכרון לא גדל בלי סוף. |
| **WATCH/MULTI/EXEC** | מונע race condition על המקום האחרון בחניון. |
| **Polling כל 3 שניות** (ולא WebSocket) | פשוט, עונה על הדרישה, ומספיק לחניון. |
| **healthcheck + `service_healthy`** | ה-API עולה רק כש-Redis באמת עונה. |
| **משתמש לא-root ב-Dockerfile** | אם מישהו פורץ ל-container, אין לו הרשאות root. |
| **`COPY requirements.txt` לפני הקוד** | ניצול Layer cache – שינוי קוד לא מתקין מחדש את הספריות. |
| **CI עם בדיקת down/up** | מוכיח אוטומטית בכל push שה-persistence עובד. |
| **Publish רק מ-`main` ואחרי שהטסטים עברו** (`needs`) | לא מפרסמים אימג' שבור או מענף ניסיוני. |
