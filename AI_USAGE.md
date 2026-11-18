# AI_USAGE.md – תיעוד השימוש ב-AI

השתמשנו ב-Claude כעוזר לכתיבת קוד, קונפיגורציה ותיעוד. כל קובץ נקרא, הורץ ונבדק על ידינו,
ואנחנו מסוגלים להסביר כל שורה (ראו `STUDY_GUIDE.md`).

## פרומפטים עיקריים שנשלחו
1. "הנה הוראות המטלה (Track 2). תבנה לי מבנה פרויקט עם docker-compose לשלושה שירותים: Nginx, API ב-Python Flask ו-Redis עם persistence."
2. "תכתוב API ב-Flask עם POST לכניסת רכב ו-GET לרשימת הרכבים, שישמור ב-Redis. תוסיף בדיקת קיבולת מקסימלית."
3. "תכתוב index.html בעברית עם JavaScript שעושה fetch כל 3 שניות ומציג את הרכבים דינמית, עם Dark Mode וכפתור שחרור."
4. "תכתוב GitHub Actions workflow שבודק docker build בכל push, ומעלה את האימג'ים ל-ghcr.io עם תיוג גרסה."
5. "איך מוכיחים ב-CI שה-volume שומר את הנתונים אחרי docker compose down?"

## שגיאות / אי-דיוקים של ה-AI ואיך תיקנו

### 1. CORS – לוח הבקרה לא הצליח לדבר עם ה-API
**מה ה-AI הציע:** ב-JavaScript `fetch("http://localhost:5000/api/cars")`.
**הבעיה:** הדף נטען מ-`localhost:8080` והבקשה הולכת ל-`localhost:5000` – זה Origin אחר,
והדפדפן חסם את התגובה בשגיאת CORS בקונסול.
**התיקון:** במקום להוסיף `flask-cors`, הגדרנו ב-`nginx.conf` בלוק `location /api/` שמעביר את הבקשות
ל-`http://api:5000`, וב-JS שינינו ל-URL יחסי `"/api"`. עכשיו הדפדפן מדבר רק עם Origin אחד.

### 2. `depends_on` לא חיכה ל-Redis
**מה ה-AI הציע:** `depends_on: [redis]`.
**הבעיה:** זה מחכה רק שה-container *יתחיל*, לא שRedis *מוכן*. בהרצה הראשונה ה-API ניסה להתחבר מוקדם מדי.
**התיקון:** הוספנו `healthcheck` עם `redis-cli ping` לשירות redis ו-`condition: service_healthy` ב-api.

### 3. הנתונים נמחקו בבדיקת ה-CI
**מה ה-AI הציע:** בשלב בדיקת ה-persistence – `docker compose down -v`.
**הבעיה:** הדגל `-v` מוחק גם את ה-volumes, אז הבדיקה תמיד נכשלה.
**התיקון:** `docker compose down` בלי `-v` באמצע הבדיקה, ו-`down -v` רק בשלב הניקוי הסופי.

### 4. Race condition בבדיקת "חניון מלא"
**מה ה-AI הציע:** `if r.zcard(...) >= CAPACITY` ואז `zadd` בשתי פקודות נפרדות.
**הבעיה:** שתי מצלמות שמזהות רכב באותו רגע יכולות שתיהן לעבור את הבדיקה ולתפוס את המקום האחרון.
**התיקון:** `WATCH` + `MULTI/EXEC` (optimistic locking) – אם הסט השתנה באמצע, הטרנזקציה נכשלת ומנסים שוב.
