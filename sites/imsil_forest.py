import asyncio
import httpx
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any

from core.notifications import send_sms_alert

BASE_URL = "https://임실성수산왕의숲국민여가캠핑장.com/16/"

async def check_availability(site_config: Dict[str, Any]) -> Dict[str, List[int]]:
    """임실성수산왕의숲 캠핑장의 예약 가능 상태를 확인합니다."""
    check_dates = site_config.get("dates", [])
    found_sites = {}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for check_date in check_dates:
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
        print(f"[ERROR] 임실성수산왕의숲 확인 중 오류 발생: {e}")
    
    return found_sites

async def cancellable_sleep(site_id: str, duration: int, monitoring_status: Dict[str, bool]):
    """지정된 시간 동안 대기하지만, 1초마다 모니터링 상태를 확인하여 중단될 수 있도록 합니다."""
    for _ in range(duration):
        if not monitoring_status.get(site_id, False):
            break
        await asyncio.sleep(1)

async def monitor_site(site_id: str, site_config: Dict[str, Any], monitoring_status: Dict[str, bool]):
    """특정 사이트의 모니터링을 수행하는 비동기 작업입니다."""
    check_interval = 120  # 2분
    alert_interval = 120  # 2분

    while monitoring_status.get(site_id, False):
        try:
            found_sites = await check_availability(site_config)
            
            if not monitoring_status.get(site_id, False):
                break

            if found_sites:
                log_status = f"예약 가능: {list(found_sites.keys())}"
                display_name = site_config.get("display_name", site_id)
                asyncio.create_task(send_sms_alert(f'{display_name}-예약가능'))
                current_interval = alert_interval
            else:
                log_status = "예약 가능한 자리 없음."
                current_interval = check_interval

            print(f"[{site_id}] {log_status} (다음 확인: {current_interval}초 후)")
            
            await cancellable_sleep(site_id, current_interval, monitoring_status)

        except asyncio.CancelledError:
            print(f"[INFO] {site_id} 모니터링 작업이 외부에서 취소되었습니다.")
            break
        except Exception as e:
            print(f"[ERROR] {site_id} 모니터링 중 예외 발생: {e}")
            await cancellable_sleep(site_id, check_interval, monitoring_status)
    
    print(f"[INFO] {site_id} 모니터링이 종료되었습니다.")
