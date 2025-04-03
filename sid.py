from flask import Flask , request
from flask_socketio import SocketIO, emit
import threading
import time
import requests
app = Flask(__name__)
socketio = SocketIO(app)

# ใช้ dict ในการเก็บ thread ที่เชื่อมต่อกับแต่ละ client
client_threads = {}

# ฟังก์ชันที่ดึงข้อมูลจาก API ที่ใช้เวลานาน
def fetch_data_from_api():
    # ตัวอย่าง URL API ที่จะดึงข้อมูล
    url = "https://pokeapi.co/api/v2/pokemon?limit=10"
    response = requests.get(url)
    return response.json()

# ฟังก์ชันที่จะส่งข้อมูลไปยัง client
def send_data_for_client(sid):
    while True:
        # ดึงข้อมูลจาก API
        data = fetch_data_from_api()
        # ส่งข้อมูลไปยัง client ที่ระบุ sid
        socketio.emit('update_data', data, room=sid)
        time.sleep(20)  # รอ 20 วินาที

@socketio.on('connect')
def handle_connect():
    print(f"Client {request.sid} เชื่อมต่อแล้ว!")
    # สร้าง thread สำหรับ client นั้นๆ และเก็บไว้ใน dict
    client_threads[request.sid] = threading.Thread(target=send_data_for_client, args=(request.sid,))
    client_threads[request.sid].start()

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client {request.sid} ตัดการเชื่อมต่อแล้ว!")
    # หยุด thread ที่เกี่ยวข้องกับ client ที่ตัดการเชื่อมต่อ
    if request.sid in client_threads:
        # กรณีนี้ thread ไม่สามารถหยุดได้ทันที แต่สามารถตั้งค่าสถานะหรือจัดการให้หยุดได้
        client_threads[request.sid].join()  # รอให้ thread หยุดก่อน (ถ้าต้องการ)
        del client_threads[request.sid]  # ลบ client ที่ disconnect ออกจาก dict

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
