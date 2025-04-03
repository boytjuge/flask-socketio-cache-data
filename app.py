from flask import Flask , request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
import requests
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app)


# ตัวแปรสำหรับเก็บข้อมูล cache
cache_data = None
last_fetched_time = None

# Dictionary สำหรับเก็บจำนวน clients ที่เชื่อมต่อและ thread สำหรับแต่ละ location_id
location_threads = {}
location_client_counts = {}


# Lock for thread safety
location_thread_lock = threading.Lock()


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
def send_data_for_client(location_id):
    global location_threads
    while location_client_counts.get(location_id, 0) > 0:  # เช็คว่ามี client เชื่อมต่อหรือไม่
        update_cache()  # อัพเดตข้อมูลจาก API หรือ cache
        # ส่งข้อมูลที่ cache ไปยัง client ที่มี location_id ตรงกับ key
        socketio.emit('update_data', cache_data, room=location_id)
        time.sleep(5)  # ส่งข้อมูลทุกๆ 5 วินาที

    print(f"No clients connected for location {location_id}, stopping data send thread.")
    
    # เมื่อไม่มี client เชื่อมต่อให้ลบ thread ออก
    with location_thread_lock:  # Ensure thread safety when modifying shared resource
        if location_id in location_threads:
            del location_threads[location_id]  # Delete thread entry

    # Log the active threads
    log_active_threads()            







# ฟังก์ชันที่ใช้สำหรับล็อกข้อมูล threads ที่กำลังทำงานอยู่
def log_active_threads():
    logger.info(f"Currently active threads: {threading.active_count()}")
    for thread in threading.enumerate():
        logger.info(f"Thread {thread.name} is alive: {thread.is_alive()}")




@socketio.on('connect')
def handle_connect():
    location_id = request.args.get('location_id')  # ดึง location_id ที่ส่งมาจาก client

    if location_id:
        # เพิ่มจำนวน client ที่เชื่อมต่อใน location_id
        location_client_counts[location_id] = location_client_counts.get(location_id, 0) + 1
        print(f"Client {request.sid} เชื่อมต่อที่ location {location_id}! จำนวน client: {location_client_counts[location_id]}")

        # ถ้าไม่มี thread สำหรับ location_id นี้ ให้สร้าง thread ใหม่
        with location_thread_lock:  # Ensure thread safety when modifying shared resource
            if location_id not in location_threads or not location_threads[location_id].is_alive():
                location_threads[location_id] = threading.Thread(target=send_data_for_client, args=(location_id,))
                location_threads[location_id].start()

        # เข้าร่วม room สำหรับ location_id เพื่อให้สามารถส่งข้อมูลไปยัง client ที่มี location_id เดียวกันได้
        join_room(location_id)

@socketio.on('disconnect')
def handle_disconnect():
    location_id = request.args.get('location_id')  # ดึง location_id ที่ส่งมาจาก client

    if location_id:
        # ลดจำนวน client ที่เชื่อมต่อใน location_id
        location_client_counts[location_id] -= 1
        print(f"Client {request.sid} ตัดการเชื่อมต่อที่ location {location_id}! จำนวน client: {location_client_counts[location_id]}")

        # ถ้าไม่มี client เชื่อมต่อแล้ว ให้หยุด thread
        if location_client_counts[location_id] < 1:
            print(f"No more clients for location {location_id}, stopping data send thread.")
            
            # ลบ location_id จาก dictionary และหยุด thread
            with location_thread_lock:  # Ensure thread safety when modifying shared resource
                if location_id in location_threads:
                    del location_client_counts[location_id]
                    del location_threads[location_id]
                    leave_room(location_id)  # Exit the room
                    print(f"Thread for location {location_id} has been removed.")
                    socketio.server.eio.close(request.sid)  # Ensure that the connection is properly closed
                    print(f"Closed connection for client {request.sid}")

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)