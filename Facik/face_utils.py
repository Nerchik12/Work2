import face_recognition
import cv2
import numpy as np
import sqlite3

def register_employee(image_path, full_name, position):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    
    if not encodings:
        raise ValueError("Лицо не найдено на фото!")
    
    encoding = encodings[0]
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (full_name, position, face_encoding) VALUES (?, ?, ?)",
        (full_name, position, encoding.tobytes())
    )
    conn.commit()
    conn.close()

def recognize_face(image_path):
    unknown_image = face_recognition.load_image_file(image_path)
    unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, face_encoding FROM employees")
    employees = cursor.fetchall()
    conn.close()
    
     # сравнение
    for emp_id, full_name, encoding_bytes in employees:
        known_encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
        match = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.6)
        
        if match[0]:
            return emp_id, full_name
    
    return None, "Неизвестный сотрудник"