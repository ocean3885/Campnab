import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import monitor 
import database 

# --- FastAPI 앱 및 템플릿 설정 ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- FastAPI 엔드포인트 ---
@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 시 DB 테이블을 생성하고 백그라운드 작업을 시작합니다.
    """
    print("Application started. Initializing database and starting background check.")
    database.create_table()
    asyncio.create_task(monitor.check_reservation_status())

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    루트 URL에 접속했을 때 날짜 설정 페이지를 보여줍니다.
    """
    current_dates = ", ".join(monitor.CHECK_DATES)
    return templates.TemplateResponse("index.html", {"request": request, "message": f"현재 감시 날짜: {current_dates}"})

@app.post("/set-dates", response_class=HTMLResponse)
async def set_dates(request: Request, dates: str = Form(...)):
    """
    POST 요청을 통해 새로운 감시 날짜를 설정합니다.
    """
    new_dates = [d.strip() for d in dates.split(',') if d.strip()]
    if new_dates:
        monitor.CHECK_DATES = new_dates
        message = f"감시 날짜가 성공적으로 변경되었습니다. 새로운 날짜: {', '.join(monitor.CHECK_DATES)}"
    else:
        message = "올바른 날짜를 입력해주세요."
    
    return templates.TemplateResponse("index.html", {"request": request, "message": message})

@app.get("/logs", response_class=HTMLResponse)
async def get_logs(request: Request):
    """
    DB에 저장된 모든 감시 기록을 HTML 테이블로 보여줍니다.
    """
    logs = database.get_all_logs()
    return templates.TemplateResponse("logs.html", {"request": request, "logs": logs})