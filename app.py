from flask import Flask, request, jsonify
import psycopg2
from datetime import date
import os

app = Flask(__name__)

# Ambil environment variable untuk koneksi DB
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", 5432)  # default PostgreSQL port


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )


@app.route("/validate_license", methods=["POST"])
def validate_license():
    data = request.get_json()
    license_key = data.get("license_key")
    machine_id = data.get("machine_id")

    if not license_key or not machine_id:
        return jsonify({"error": "Missing license_key or machine_id"}), 400

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT end_date, status FROM licenses
            WHERE license_key = %s AND machine_id = %s
        """, (license_key, machine_id))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            end_date, status = row
            today = date.today()
            days_left = (end_date - today).days

            if status == "active" and days_left >= 0:
                return jsonify({
                    "status": "valid",
                    "days_remaining": days_left
                })
            else:
                return jsonify({
                    "status": "expired",
                    "days_remaining": days_left
                })
        else:
            return jsonify({"status": "invalid"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add_license", methods=["POST"])
def add_license():
    data = request.get_json()
    license_key = data.get("license_key")
    machine_id = data.get("machine_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    status = data.get("status", "active")

    if not all([license_key, machine_id, start_date, end_date]):
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO licenses (license_key, machine_id, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (license_key, machine_id, start_date, end_date, status))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "License added successfully."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
