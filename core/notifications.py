import httpx

async def send_sms_alert(message: str):
    """SMS 알림을 비동기적으로 전송합니다."""
    send_url = 'https://apis.aligo.in/send/'
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
