import asyncio
from contextlib import asynccontextmanager
import httpx
from bs4 import BeautifulSoup
import datetime
import re
from fastapi import FastAPI, Request, Form, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
<<<<<<< HEAD
        "dates": ["20250815", "20250816"],  # 기본 날짜
        "monitoring_active": True            # 기본 감시 상태
=======
        "dates": ["20250815", "20250816"],
        "monitoring_active": True
>>>>>>> 8cef732dcc989a6d3db05a4dfd225032f6442934
    }

def save_config(dates, monitoring_active):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "dates": dates,
            "monitoring_active": monitoring_active
        }, f, ensure_ascii=False, indent=2)

# --- 글로벌 설정 ---
BASE_URL = "https://임실성수산왕의숲국민여가캠핑장.com/16/"
config = load_config()
CHECK_DATES = config["dates"]
send_url = 'https://apis.aligo.in/send/'

# --- 실행 횟수 추적 ---
EXECUTION_COUNT = 0
MONITORING_ACTIVE = config["monitoring_active"]
MONITORING_TASK = None

# --- 템플릿 ---
templates = Jinja2Templates(directory="templates")

async def send_sms_alert(message: str):
    sms_data = {
        'key': 'mbam9e8v586xu9vugol89i2wxvihrv9l',
        'userid': 'ocean3885',
        'sender': '01022324548',
        'receiver': '01022324548',
        'msg': message
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(send_url, data=sms_data)
            response.raise_for_status()
            print("SMS 전송 결과:", response.json())
        except httpx.HTTPError as e:
            print(f"[SMS ERROR] SMS 전송 실패: {e}")

async def check_reservation_status():
    global CHECK_DATES, EXECUTION_COUNT, MONITORING_ACTIVE
    check_interval = 120

    while MONITORING_ACTIVE:
        start_time = datetime.datetime.now()
        EXECUTION_COUNT += 1
        found_sites = {}
        log_status = "No available spots."

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(BASE_URL)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                for check_date in CHECK_DATES:
                    available_site_ids = []
                    target_links = soup.find_all('a', href=lambda href: href and check_date in href)
                    
                    for a_tag in target_links:
                        booking_badge_span = a_tag.find('span', class_='booking_badge')
                        if booking_badge_span and booking_badge_span.text == '가':
                            href = a_tag['href']
                            match = re.search(r'idx=(\d+)', href)
                            if match:
                                available_site_ids.append(int(match.group(1)))
                    
                    if available_site_ids:
                        found_sites[check_date] = sorted(available_site_ids)
            
        except Exception as e:
            log_status = f"Error during check: {e}"
            print(f"[ERROR] {log_status}")
        
        if found_sites:
            log_status = f"Alert: Available spots found for dates: {list(found_sites.keys())}"
            asyncio.create_task(send_sms_alert('성수산왕의숲-예약가능'))

        print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] {log_status} Next check in {check_interval} seconds.")
        await asyncio.sleep(check_interval)
        
    print("[INFO] 감시 루프가 종료되었습니다.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MONITORING_TASK, MONITORING_ACTIVE
    print("Application started. Loading config...")
    config = load_config()
    MONITORING_ACTIVE = config["monitoring_active"]
    if MONITORING_ACTIVE:
        MONITORING_TASK = asyncio.create_task(check_reservation_status())
    yield
    print("Application is shutting down.")

<<<<<<< HEAD
=======
# --- App and Router Setup ---
>>>>>>> 8cef732dcc989a6d3db05a4dfd225032f6442934
app = FastAPI(lifespan=lifespan)
router = APIRouter()

# 정적 파일 마운트 (camping 프리픽스 하에 static 제공)
app.mount("/camping/static", StaticFiles(directory="static"), name="static")

# 헬퍼: 홈 페이지 렌더링 (중복 방지)
async def render_homepage(request: Request, message: str = ""):
    current_dates = ", ".join(CHECK_DATES)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "execution_count": EXECUTION_COUNT,
            "current_dates": current_dates,
            "monitoring_active": MONITORING_ACTIVE,
            "message": message
        }
    )

# --- API Endpoints (router under /camping/) ---
@router.get("/", response_class=HTMLResponse, name="homepage")
async def read_root(request: Request):
    return await render_homepage(request)

@router.post("/set-dates", name="set_dates")
async def set_dates(request: Request, dates: str = Form(...)):
    global CHECK_DATES
    new_dates = [d.strip() for d in dates.split(',') if d.strip()]
    
    if new_dates:
        CHECK_DATES = new_dates
        save_config(CHECK_DATES, MONITORING_ACTIVE)
        message = f"감시 날짜가 성공적으로 변경되었습니다. 새로운 날짜: {', '.join(CHECK_DATES)}"
    else:
        message = "올바른 날짜를 입력해주세요."
    
    return RedirectResponse(request.url_for("homepage"), status_code=303)

<<<<<<< HEAD
@app.post("/stop", response_class=HTMLResponse)
async def stop_monitoring(request: Request):
    global MONITORING_ACTIVE, MONITORING_TASK
    if MONITORING_ACTIVE:
        MONITORING_ACTIVE = False
        if MONITORING_TASK:
            MONITORING_TASK.cancel()
        save_config(CHECK_DATES, MONITORING_ACTIVE)
        message = "감시가 중단되었습니다."
    else:
        message = "감시가 이미 중단된 상태입니다."
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "execution_count": EXECUTION_COUNT,
            "current_dates": ", ".join(CHECK_DATES),
            "message": message
        }
    )
=======
@router.get("/status")
async def get_status():
    return {"monitoring_active": MONITORING_ACTIVE}
>>>>>>> 8cef732dcc989a6d3db05a4dfd225032f6442934

@router.post("/toggle", name="toggle_monitoring")
async def toggle_monitoring(request: Request):
    global MONITORING_ACTIVE, MONITORING_TASK
    
    MONITORING_ACTIVE = not MONITORING_ACTIVE
    save_config(CHECK_DATES, MONITORING_ACTIVE)
    
    if MONITORING_ACTIVE:
        print("[INFO] 감시가 시작되었습니다.")
        if MONITORING_TASK is None or MONITORING_TASK.done():
            MONITORING_TASK = asyncio.create_task(check_reservation_status())
    else:
        if MONITORING_TASK and not MONITORING_TASK.done():
            print("[INFO] 감시 중단을 요청했습니다. 다음 확인 주기 이후에 중단됩니다.")

    return RedirectResponse(request.url_for("homepage"), status_code=303)

# --- Include Router under /camping ---
app.include_router(router, prefix="/camping")

# --- Root route: 직접 페이지 제공하여 리다이렉트 루프 방지 ---
@app.get("/", response_class=HTMLResponse)
async def root_alias(request: Request):
    return await render_homepage(request)
