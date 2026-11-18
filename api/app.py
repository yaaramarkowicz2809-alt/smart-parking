"""
Galactic Spaceport - Smart Parking API
--------------------------------------
Flask backend that receives license plates from the IoT camera (POST)
and serves the live list of parked vehicles to the dashboard (GET).
All state lives in Redis (persisted to disk via AOF + a Docker volume).
"""
import json
import math
import os
import random
import re
import time

import redis
from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------- Configuration (from environment variables set in docker-compose) ----------
REDIS_HOST = os.getenv("REDIS_HOST", "redis")          # "redis" = service name in compose
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CAPACITY = int(os.getenv("PARKING_CAPACITY", "10"))    # max ships in the spaceport
RATE_PER_HOUR = float(os.getenv("RATE_PER_HOUR", "12"))  # galactic credits per started hour
FREE_MINUTES = int(os.getenv("FREE_MINUTES", "15"))    # grace period

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# ---------- Redis keys ----------
PARKED = "parking:parked"          # Sorted Set: member=plate, score=entry timestamp
HISTORY = "parking:history"        # List of JSON events (latest first, max 50)
TOTAL_ENTRIES = "parking:total_entries"  # Counter (String)
REVENUE = "parking:revenue"        # Float counter (String)


def car_key(plate: str) -> str:
    return f"car:{plate}"          # Hash with the car details


# ---------- The "personal touch": spaceport theme ----------
SHIP_CLASSES = ["X-Wing Fighter", "Cargo Freighter", "Star Cruiser",
                "Scout Pod", "Mining Shuttle", "Diplomatic Yacht"]
WELCOME_MESSAGES = [
    "ברוכים הבאים לתחנה! נא לא להשאיר אורגניזמים זרים בתא המטען 👽",
    "נחיתה מוצלחת! הדלק הגלקטי בקיוסק בקומה -42 ⛽",
    "ספינה זוהתה. מגני הכוח הושבתו, אפשר לרדת 🛸",
    "שלום טייס! החנייה בחינם ב-15 הדקות הראשונות, אחרי זה - קרדיטים 💰",
    "מערכת הניווט מודה לך שלא נחתת על הגג הפעם 🚀",
]
EASTER_EGG_PLATE = "4242424"   # the answer to life, the universe and parking


def normalize_plate(raw) -> str | None:
    """Keep digits only. Israeli plates are 7 or 8 digits (e.g. 12-345-67 / 123-45-678)."""
    digits = re.sub(r"\D", "", str(raw or ""))
    return digits if 7 <= len(digits) <= 8 else None


def calc_fee(entry_ts: float, now: float | None = None) -> float:
    """Free for FREE_MINUTES, then RATE_PER_HOUR for every *started* hour."""
    minutes = ((now or time.time()) - entry_ts) / 60
    if minutes <= FREE_MINUTES:
        return 0.0
    return math.ceil(minutes / 60) * RATE_PER_HOUR


def log_event(pipe, event: dict):
    pipe.lpush(HISTORY, json.dumps(event, ensure_ascii=False))
    pipe.ltrim(HISTORY, 0, 49)     # keep only the last 50 events


# ---------- Error handling ----------
@app.errorhandler(redis.exceptions.ConnectionError)
def redis_down(_e):
    return jsonify(error="Redis is unreachable"), 503


# ---------- Endpoints ----------
@app.get("/api/health")
def health():
    r.ping()
    return jsonify(status="ok", redis="up")


@app.post("/api/entry")
def car_entry():
    """Called by the IoT camera: {"plate": "12-345-67"}"""
    data = request.get_json(silent=True) or {}
    plate = normalize_plate(data.get("plate"))
    if not plate:
        return jsonify(error="Invalid plate - expected 7 or 8 digits"), 400

    now = time.time()
    # Optimistic locking: WATCH the parked set so two cameras can't
    # both take the last free spot at the same moment.
    with r.pipeline() as pipe:
        while True:
            try:
                pipe.watch(PARKED)
                if pipe.zscore(PARKED, plate) is not None:
                    return jsonify(error=f"Ship {plate} is already docked"), 409
                if pipe.zcard(PARKED) >= CAPACITY:
                    return jsonify(error="FULL CAPACITY - spaceport is full!", full=True), 409

                car = {
                    "plate": plate,
                    "entry_time": now,
                    "ship_class": random.choice(SHIP_CLASSES),
                    "message": random.choice(WELCOME_MESSAGES),
                }
                if plate == EASTER_EGG_PLATE:
                    car["ship_class"] = "Heart of Gold 🐬"
                    car["message"] = "42! מצאת את התשובה לחיים, ליקום ולחנייה. החנייה עליך חינם (לא באמת)."

                pipe.multi()                       # start the atomic transaction
                pipe.zadd(PARKED, {plate: now})
                pipe.hset(car_key(plate), mapping=car)
                pipe.incr(TOTAL_ENTRIES)
                log_event(pipe, {"type": "entry", "plate": plate, "time": now})
                pipe.execute()                     # fails with WatchError if PARKED changed
                break
            except redis.WatchError:
                continue                           # someone else changed it - retry

    return jsonify(status="docked", car=car), 201


@app.get("/api/cars")
def list_cars():
    """Called by the dashboard every few seconds."""
    now = time.time()
    plates = r.zrange(PARKED, 0, -1)               # ordered by entry time
    pipe = r.pipeline()
    for p in plates:
        pipe.hgetall(car_key(p))
    cars = []
    for car in pipe.execute():
        if not car:
            continue
        entry = float(car["entry_time"])
        car["entry_time"] = entry
        car["minutes_parked"] = int((now - entry) // 60)
        car["current_fee"] = calc_fee(entry, now)
        cars.append(car)

    count = len(cars)
    return jsonify(
        cars=cars,
        count=count,
        capacity=CAPACITY,
        free=max(CAPACITY - count, 0),
        full=count >= CAPACITY,
        total_entries=int(r.get(TOTAL_ENTRIES) or 0),
        revenue=float(r.get(REVENUE) or 0),
        rate_per_hour=RATE_PER_HOUR,
        free_minutes=FREE_MINUTES,
    )


@app.post("/api/exit/<plate>")
def car_exit(plate):
    """'Release car' button on the dashboard."""
    plate = normalize_plate(plate)
    if not plate:
        return jsonify(error="Invalid plate"), 400
    entry = r.zscore(PARKED, plate)
    if entry is None:
        return jsonify(error=f"Ship {plate} is not in the spaceport"), 404

    now = time.time()
    fee = calc_fee(entry, now)
    pipe = r.pipeline()                            # MULTI/EXEC by default
    pipe.zrem(PARKED, plate)
    pipe.delete(car_key(plate))
    pipe.incrbyfloat(REVENUE, fee)
    log_event(pipe, {"type": "exit", "plate": plate, "time": now, "fee": fee})
    pipe.execute()
    return jsonify(status="released", plate=plate, fee=fee,
                   minutes=int((now - entry) // 60))


@app.get("/api/history")
def history():
    return jsonify(events=[json.loads(e) for e in r.lrange(HISTORY, 0, 19)])


if __name__ == "__main__":
    # Local development only. In Docker we run gunicorn (see Dockerfile).
    app.run(host="0.0.0.0", port=5000, debug=True)
