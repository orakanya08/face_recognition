let ws = null;
const canvas = document.getElementById("canvas");
const context = canvas.getContext("2d");
const cameraToggle = document.getElementById("cameraToggle");
const statusText = document.getElementById("status");

cameraToggle.addEventListener("change", function() {
    if (cameraToggle.checked) {
        // เริ่มการเชื่อมต่อ WebSocket
        ws = new WebSocket("ws://127.0.0.1:8000/ws");
        statusText.innerText = "Camera is on";
        canvas.style.display = "block";

        ws.onmessage = function(event) {
            const img = new Image();
            img.src = "data:image/jpeg;base64," + event.data;
            img.onload = function() {
                context.drawImage(img, 0, 0, canvas.width, canvas.height);
            }
        };

        ws.onclose = function() {
            console.log("WebSocket closed");
            ws = null;
        };
    } else {
        // ปิด WebSocket และกล้อง
        if (ws) {
            ws.close();
            ws = null;
        }
        context.clearRect(0, 0, canvas.width, canvas.height);
        canvas.style.display = "none";
        statusText.innerText = "Camera is off";
    }
});
