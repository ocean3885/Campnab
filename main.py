import asyncio
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI
import datetime
import re
import requests


# 알림을 보낼 URL과 확인 날짜 설정
BASE_URL = "https://임실성수산왕의숲국민여가캠핑장.com/16/"
CHECK_DATES = ["20250815", "20250816"] # 예시로 날짜 추가
send_url = 'https://apis.aligo.in/send/'

app = FastAPI()

async def check_reservation_status():
    """
    2분마다 캠핑장 예약 가능 여부를 확인하고 알림을 보냅니다.
    """
    while True:
        found_sites = {}
        print(f"[{datetime.datetime.now()}] Checking for available spots for dates: {CHECK_DATES}...")

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(BASE_URL)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                
                for check_date in CHECK_DATES:
                    available_site_ids = []
                    
                    target_links = soup.find_all('a', href=lambda href: href and check_date in href)

                    if not target_links:
                        print(f"    - {check_date} 날짜가 포함된 링크를 찾을 수 없습니다.")
                        continue
                    
                    for a_tag in target_links:
                        booking_badge_span = a_tag.find('span', class_='booking_badge')
                        
                        if booking_badge_span and booking_badge_span.text == '가':
                            # href 속성에서 idx 번호만 추출
                            href = a_tag['href']
                            match = re.search(r'idx=(\d+)', href)
                            if match:
                                available_site_ids.append(int(match.group(1)))
                    
                    if available_site_ids:
                        found_sites[check_date] = sorted(available_site_ids)

            except httpx.HTTPStatusError as e:
                print(f"HTTP 오류가 발생했습니다: {e} (URL: {BASE_URL})")
            except Exception as e:
                print(f"오류가 발생했습니다: {e} (URL: {BASE_URL})")

        if found_sites:
            print("🚨 알림: 예약 가능한 자리가 발견되었습니다!")
            for date, site_ids in found_sites.items():
                print(f"  - 날짜: {date}")
                print(f"  - 예약 가능 사이트: {site_ids}")
                # SMS 전송 가정
                sms_data = {
                    'key': 'mbam9e8v586xu9vugol89i2wxvihrv9l',
                    'userid': 'ocean3885',
                    'sender': '01022324548',
                    'receiver': '01022324548',
                    'msg': '성수산왕의숲-예약가능'
                }
                send_response = requests.post(send_url, data=sms_data)  # send_url은 정의되어야 함
                print(send_response.json())
            
            print("🚨 조건 충족! 1시간 뒤에 다시 확인합니다.")
            await asyncio.sleep(3600)
        else:
            print("예약 가능한 자리가 없습니다. 2분 뒤에 다시 확인합니다.")
            await asyncio.sleep(120)

@app.on_event("startup")
async def startup_event():
    print("애플리케이션 시작. 백그라운드 예약 확인 작업을 시작합니다.")
    asyncio.create_task(check_reservation_status())

@app.get("/")
def read_root():
    return {"message": "Reservation checker is running in the background."}