from flask import Flask, request, jsonify, render_template
import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)

# ---------------- DATABASE INIT ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            liters_used INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- ADD DATA ----------------

@app.route("/add_usage", methods=["POST"])
def add_usage():
    data = request.json
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO water_usage (date, liters_used) VALUES (?, ?)",
        (data["date"], data["liters"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Data added successfully"})

# ---------------- GET DATA ----------------

@app.route("/get_usage")
def get_usage():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, liters_used FROM water_usage")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

# ---------------- ANALYSIS ----------------

@app.route("/analysis")
def analysis():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM water_usage", conn)
    conn.close()

    if len(df) == 0:
        return jsonify({})

    return jsonify({
        "total_usage": int(df["liters_used"].sum()),
        "average_usage": round(float(df["liters_used"].mean()),2),
        "max_usage": int(df["liters_used"].max()),
        "min_usage": int(df["liters_used"].min())
    })

# ---------------- AI PREDICTION ----------------

@app.route("/predict")
def predict():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM water_usage", conn)
    conn.close()

    if len(df) < 2:
        return jsonify([])

    df["day"] = range(1, len(df)+1)

    X = np.array(df["day"]).reshape(-1, 1)
    y = np.array(df["liters_used"])

    model = LinearRegression()
    model.fit(X, y)

    future_days = np.array(range(len(df)+1, len(df)+8)).reshape(-1, 1)
    predictions = model.predict(future_days)

    return jsonify(predictions.tolist())

# ---------------- ALERTS ----------------

@app.route("/alerts")
def alerts():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM water_usage", conn)
    conn.close()

    if len(df) < 2:
        return jsonify({"alert": ""})

    latest = df["liters_used"].iloc[-1]
    previous = df["liters_used"].iloc[-2]

    if latest > previous:
        return jsonify({"alert": "⚠ Water usage increased compared to previous record!"})
    else:
        return jsonify({"alert": ""})

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
