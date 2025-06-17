from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from datetime import datetime
import face_utils
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Создаем папки если их нет
os.makedirs("employees", exist_ok=True)
os.makedirs("static", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("recognize.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def register_employee(
    request: Request,
    name: str = Form(...),
    position: str = Form(...),
    photo: UploadFile = File(...)
):
    photo_path = f"employees/{name.lower().replace(' ', '_')}.jpg"
    with open(photo_path, "wb") as f:
        f.write(await photo.read())
    
    face_utils.register_employee(photo_path, name, position)
    
    return RedirectResponse("/register", status_code=303)

@app.get("/employees", response_class=HTMLResponse)
async def list_employees(request: Request):
    conn = sqlite3.connect('logs.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, position FROM employees")
    employees = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("_employees.html", {
        "request": request,
        "employees": employees
    })

@app.get("/recognize", response_class=HTMLResponse)
async def recognize_page(request: Request):
    return templates.TemplateResponse("recognize.html", {"request": request})

@app.post("/recognize", response_class=HTMLResponse)
async def recognize_employee(
    request: Request,
    photo: UploadFile = File(...)
):
    temp_path = "temp_photo.jpg"
    with open(temp_path, "wb") as f:
        f.write(await photo.read())
    
    emp_id, name = face_utils.recognize_face(temp_path)
    os.remove(temp_path)
    
    if not emp_id:
        return HTMLResponse("""
        <div class="error">Сотрудник не распознан!</div>
        """)
    
    conn = sqlite3.connect('logs.db')
    cursor = conn.cursor()
    
    # Проверяем последнее действие сотрудника
    cursor.execute("""
    SELECT action FROM logs 
    WHERE employee_id = ? 
    ORDER BY timestamp DESC 
    LIMIT 1
    """, (emp_id,))
    
    last_action = cursor.fetchone()
    new_action = 'out' if last_action and last_action[0] == 'in' else 'in'
    
    # Фиксируем новое действие
    cursor.execute(
        "INSERT INTO logs (employee_id, action) VALUES (?, ?)",
        (emp_id, new_action)
    )
    conn.commit()
    conn.close()
    
    return HTMLResponse(f"""
    <div class="success">
        Сотрудник: {name}<br>
        Действие: {'Выход' if new_action == 'out' else 'Вход'}<br>
        Время: {datetime.now().strftime('%H:%M:%S')}
    </div>
    """)

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, date: str = None):
    conn = sqlite3.connect('logs.db')
    query = """
    SELECT l.id, e.full_name, l.timestamp, l.action 
    FROM logs l JOIN employees e ON l.employee_id = e.id
    """
    params = ()
    
    if date:
        query += " WHERE date(l.timestamp) = ?"
        params = (date,)
    
    query += " ORDER BY l.timestamp DESC"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("_logs_table.html", {
        "request": request,
        "logs": logs
    })