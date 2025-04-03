from flask import Flask , request
from flask_socketio import SocketIO, emit
import threading
import time
import requests
app = Flask(__name__)
socketio = SocketIO(app)


# ตัวแปรสำหรับเก็บข้อมูล cache
cache_data = None
last_fetched_time = None

# ฟังก์ชันดึงข้อมูลจาก API
def fetch_data_from_api():
    url = "https://pokeapi.co/api/v2/pokemon?limit=10"
    response = requests.get(url)
    return response.json()

# ฟังก์ชันที่เช็คและอัพเดตข้อมูลใน cache
def update_cache():
    global cache_data, last_fetched_time
    # เช็คว่าควรดึงข้อมูลใหม่จาก API หรือไม่
    current_time = time.time()
    if cache_data is None or current_time - last_fetched_time > 60:  # 60 วินาที
        print("Fetching new data from API...")
        cache_data = fetch_data_from_api()  # ดึงข้อมูลใหม่จาก API
        last_fetched_time = current_time
    else:
        print("Using cached data...")  # ใช้ข้อมูลจาก cache

# ฟังก์ชันส่งข้อมูลไปยัง client
def send_data_for_client():
    while True:
        update_cache()  # อัพเดตข้อมูลจาก API หรือ cache
        # ส่งข้อมูลที่ cache ไปยังทุก client
        socketio.emit('update_data', cache_data)
        time.sleep(20)  # ส่งข้อมูลทุกๆ 20 วินาที

@socketio.on('connect')
def handle_connect():
    print(f"Client {request.sid} เชื่อมต่อแล้ว!")
    # เริ่ม thread ส่งข้อมูล
    threading.Thread(target=send_data_for_client).start()

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client {request.sid} ตัดการเชื่อมต่อแล้ว!")

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)