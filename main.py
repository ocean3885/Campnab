import asyncio
from contextlib import asynccontextmanager
import httpx
from bs4 import BeautifulSoup
import datetime
import re
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# --- 글로벌 설정 ---
BASE_URL = "https://임실성수산왕의숲국민여가캠핑장.com/16/"
CHECK_DATES = ["20250815", "20250816"]
send_url = 'https://apis.aligo.in/send/'

# --- 실행 횟수 추적을 위한 전역 변수 ---
EXECUTION_COUNT = 0

# --- 템플릿 설정 ---
templates = Jinja2Templates(directory="templates")

async def send_sms_alert(message: str):
    # (기존 코드와 동일)
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
    global CHECK_DATES, EXECUTION_COUNT
    check_interval = 120
    alert_interval = 3600

    while True:
        start_time = datetime.datetime.now()
        EXECUTION_COUNT += 1  # 실행 횟수 증가
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
            current_interval = alert_interval
        else:
            current_interval = check_interval

        print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] {log_status} Next check in {current_interval} seconds.")
        
        await asyncio.sleep(current_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application started. Starting background check.")
    asyncio.create_task(check_reservation_status())
    yield
    print("Application is shutting down.")

app = FastAPI(lifespan=lifespan)

# --- FastAPI 엔드포인트 ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    루트 URL에 접속했을 때 현재 실행 횟수와 날짜 설정 페이지를 보여줍니다.
    """
    current_dates = ", ".join(CHECK_DATES)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "execution_count": EXECUTION_COUNT,
            "current_dates": current_dates,
            "message": ""
        }
    )

@app.post("/camping/set-dates", response_class=HTMLResponse)
async def set_dates(request: Request, dates: str = Form(...)):
    """
    POST 요청을 통해 새로운 감시 날짜를 설정합니다.
    """
    global CHECK_DATES
    new_dates = [d.strip() for d in dates.split(',') if d.strip()]
    
    if new_dates:
        CHECK_DATES = new_dates
        message = f"감시 날짜가 성공적으로 변경되었습니다. 새로운 날짜: {', '.join(CHECK_DATES)}"
    else:
        message = "올바른 날짜를 입력해주세요."
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "execution_count": EXECUTION_COUNT,
            "current_dates": ", ".join(CHECK_DATES),
            "message": message
        }
    )