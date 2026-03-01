from flask import Flask, request
import sqlite3
import datetime

app = Flask(__name__)

# Database setup
DB_FILE = "modbus_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS modbus_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT,
            value REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized!")

def write_to_db(raw_data, value):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO modbus_readings (timestamp, raw_data, value)
        VALUES (?, ?, ?)
    ''', (datetime.datetime.utcnow(), raw_data, value))
    conn.commit()
    conn.close()

def get_all_readings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, raw_data, value 
        FROM modbus_readings 
        ORDER BY timestamp DESC 
        LIMIT 100
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route('/data', methods=['POST', 'GET'])
def receive_data():
    raw_data = request.data.decode('utf-8').strip()
    print(f"\n{'='*40}")
    print(f"Received: {raw_data}")
    print(f"Time: {datetime.datetime.now()}")
    print(f"{'='*40}")
    
    try:
        # Try to parse as numeric value
        value = float(raw_data)
        write_to_db(raw_data, value)
        print(f"Saved numeric value: {value}")
    except ValueError:
        # Save as raw data with value 0
        write_to_db(raw_data, 0.0)
        print(f"Saved raw data: {raw_data}")
    
    return "OK", 200

@app.route('/health', methods=['GET'])
def health():
    return "Server is running!", 200

@app.route('/readings', methods=['GET'])
def get_readings():
    rows = get_all_readings()
    result = []
    for row in rows:
        result.append({
            "timestamp": row[0],
            "raw_data": row[1],
            "value": row[2]
        })
    return {"readings": result}, 200

@app.route('/latest', methods=['GET'])
def get_latest():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, raw_data, value 
        FROM modbus_readings 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "timestamp": row[0],
            "raw_data": row[1],
            "value": row[2]
        }, 200
    return {"message": "No data yet"}, 404

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)