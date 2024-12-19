FROM python:3.9-slim

# ติดตั้ง dependencies ที่จำเป็นสำหรับ dlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk2.0-dev \
    libboost-python-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# คัดลอก requirements.txt และติดตั้ง Python packages
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดแอป
COPY . .

# ระบุคำสั่งเริ่มต้น
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
