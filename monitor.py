import asyncio
import httpx
from bs4 import BeautifulSoup
import datetime
import re
import database 
import requests

# --- 글로벌 설정 ---
BASE_URL = "https://임실성수산왕의숲국민여가캠핑장.com/16/"
CHECK_DATES = ["20250815", "20250816"]
CHECK_INTERVAL_SECONDS = 120
send_url = 'https://apis.aligo.in/send/'

async def check_reservation_status():
    """2분마다 캠핑장 예약 가능 여부를 확인하고 결과를 DB에 저장합니다."""
    global CHECK_INTERVAL_SECONDS
    while True:
        found_sites = {}
        log_status = "No available spots."
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(BASE_URL)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for check_date in CHECK_DATES:
                    available_site_ids = []
                    target_links = soup.find_all('a', href=lambda href: href and check_date in href)
                    
                    if target_links:
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
            CHECK_INTERVAL_SECONDS = 3600 # 발견 시 1시간 대기
        else:
            CHECK_INTERVAL_SECONDS = 120 # 미발견 시 2분 대기
        
        # 감시 결과를 DB에 기록
        database.insert_log(
            monitored_dates=",".join(CHECK_DATES),
            found_sites=str(found_sites),
            status=log_status
        )
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {log_status} Next check in {CHECK_INTERVAL_SECONDS} seconds.")
        
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)