from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import requests

app = FastAPI()

# Datenbank einrichten
db = sqlite3.connect("assets.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT,
    purchase_price REAL,
    current_value REAL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    date TEXT PRIMARY KEY,
    total_value REAL
);
""")
db.commit()

class Asset(BaseModel):
    name: str
    type: str
    purchase_price: float
    current_value: float

GOLD_API_URL = "https://api.metals-api.com/v1/latest?access_key=YOUR_API_KEY&base=USD&symbols=XAU"

def get_gold_price():
    try:
        response = requests.get(GOLD_API_URL)
        data = response.json()
        return data["rates"].get("XAU", None)
    except:
        return None

@app.get("/assets")
def get_assets():
    cursor.execute("SELECT * FROM assets")
    assets = cursor.fetchall()
    return [{"id": a[0], "name": a[1], "type": a[2], "purchase_price": a[3], "current_value": a[4]} for a in assets]

@app.post("/assets")
def add_asset(asset: Asset):
    cursor.execute("INSERT INTO assets (name, type, purchase_price, current_value) VALUES (?, ?, ?, ?)", 
                   (asset.name, asset.type, asset.purchase_price, asset.current_value))
    db.commit()
    return {"message": "Asset added"}

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int):
    cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    db.commit()
    return {"message": "Asset deleted"}

@app.get("/total-value")
def get_total_value():
    cursor.execute("SELECT SUM(current_value) FROM assets")
    total = cursor.fetchone()[0] or 0
    return {"total_value": total}

@app.post("/save-history")
def save_history():
    total = get_total_value()["total_value"]
    date = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("INSERT OR REPLACE INTO history (date, total_value) VALUES (?, ?)", (date, total))
    db.commit()
    return {"message": "History saved"}
