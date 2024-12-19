import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import cv2
import face_recognition
import pickle
import numpy as np
import base64
import os

app = FastAPI()

# โหลดข้อมูลใบหน้า
k_face_names, k_face_encoding = pickle.load(open('face.p', 'rb'))

# Static Files และ Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get():
    return templates.TemplateResponse("index.html", {"request": {}})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # เปิดกล้อง
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await websocket.send_text("Error: Cannot access camera")
        await websocket.close()
        return

    # ตัวแปรสำหรับหยุดการทำงาน
    stop_camera = False

    async def receive_message():
        nonlocal stop_camera
        try:
            while True:
                message = await websocket.receive_text()
                if message == "close_camera":
                    stop_camera = True
                    break
        except WebSocketDisconnect:
            print("WebSocket disconnected")
            stop_camera = True

    # สร้าง Task สำหรับรับข้อความแบบ Async
    receive_task = asyncio.create_task(receive_message())

    try:
        print("WebSocket connection established.")
        while not stop_camera:
            ret, frame = cap.read()
            if not ret:
                print("Error: Unable to read frame from camera")
                await websocket.send_text("Error: Unable to read from camera")
                break

            # ลดขนาดภาพเพื่อลดแบนด์วิธ
            frame = cv2.resize(frame, (640, 480))

            # แปลงภาพเป็น RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # ตรวจจับใบหน้า
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, face_loc in zip(face_encodings, face_locations):
                face_distances = face_recognition.face_distance(k_face_encoding, face_encoding)
                best_match = np.argmin(face_distances)

                if face_distances[best_match] < 0.6:
                    name = k_face_names[best_match]
                else:
                    name = "Unknown"

                # วาดกรอบรอบใบหน้าและใส่ชื่อ
                top, right, bottom, left = face_loc
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # เข้ารหัสภาพเป็น Base64
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            # ส่งภาพผ่าน WebSocket
            await websocket.send_text(jpg_as_text)

            # รอ 30ms เพื่อไม่ให้โหลดหนักเกินไป
            await asyncio.sleep(0.03)

        await receive_task  # รอ Task การรับข้อความให้เสร็จสมบูรณ์

    finally:
        # ปล่อยทรัพยากรกล้องเมื่อ WebSocket ปิด
        if cap.isOpened():
            cap.release()
        print("Camera released.")
