import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
from typing import Dict, Any

from core.config import load_app_config, save_app_config
from sites.imsil_forest import monitor_site as monitor_imsil_forest

# --- 전역 변수 및 설정 ---
app_config: Dict[str, Any] = load_app_config()
monitoring_tasks: Dict[str, asyncio.Task] = {}
monitoring_status: Dict[str, bool] = {
    site_id: config.get("monitoring_active", False)
    for site_id, config in app_config.get("sites", {}).items()
}

# --- 템플릿 및 플래시 메시지 설정 ---
templates = Jinja2Templates(directory="templates")

def flash(request: Request, message: str):
    request.session.setdefault("_flash", []).append(message)

def get_flashed_messages(request: Request):
    return request.session.pop("_flash", [])

# --- 모니터링 작업 관리 ---
async def start_monitoring_for_site(site_id: str):
    if site_id not in monitoring_tasks or monitoring_tasks[site_id].done():
        site_config = app_config["sites"][site_id]
        
        # 각 사이트에 맞는 모니터링 함수를 동적으로 선택
        monitor_function = None
        if site_id == "imsil_forest":
            monitor_function = monitor_imsil_forest
        
        if monitor_function:
            monitoring_status[site_id] = True
            task = asyncio.create_task(monitor_function(site_id, site_config, monitoring_status))
            monitoring_tasks[site_id] = task
            print(f"[INFO] {site_id} 모니터링 작업을 시작합니다.")

def stop_monitoring_for_site(site_id: str):
    if site_id in monitoring_tasks and not monitoring_tasks[site_id].done():
        monitoring_status[site_id] = False
        monitoring_tasks[site_id].cancel()
        print(f"[INFO] {site_id} 모니터링 작업을 중단합니다.")

# --- 애플리케이션 수명 주기 (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("애플리케이션 시작...")
    for site_id, config in app_config.get("sites", {}).items():
        if config.get("monitoring_active", False):
            await start_monitoring_for_site(site_id)
    yield
    print("애플리케이션 종료...")
    for task in monitoring_tasks.values():
        if not task.done():
            task.cancel()

# --- FastAPI 앱 초기화 ---
app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24).hex())

# --- FastAPI 엔드포인트 ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    messages = get_flashed_messages(request)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sites": app_config.get("sites", {}),
            "messages": messages
        }
    )

@app.post("/update-site", response_class=RedirectResponse)
async def update_site(
    request: Request,
    site_id: str = Form(...),
    dates: str = Form(...),
    action: str = Form(...)
):
    site_config = app_config["sites"].get(site_id)
    if not site_config:
        flash(request, "존재하지 않는 사이트입니다.")
        return RedirectResponse(url="/", status_code=303)

    if action == "save_dates":
        new_dates = [d.strip() for d in dates.split(',') if d.strip()]
        if new_dates:
            site_config["dates"] = new_dates
            save_app_config(app_config)
            flash(request, f"[{site_config['display_name']}] 감시 날짜가 변경되었습니다.")
        else:
            flash(request, "올바른 날짜를 입력해주세요.")

    elif action == "start":
        site_config["monitoring_active"] = True
        save_app_config(app_config)
        await start_monitoring_for_site(site_id)
        flash(request, f"[{site_config['display_name']}] 감시를 시작합니다.")

    elif action == "stop":
        site_config["monitoring_active"] = False
        save_app_config(app_config)
        stop_monitoring_for_site(site_id)
        flash(request, f"[{site_config['display_name']}] 감시가 중단되었습니다.")

    return RedirectResponse(url="/", status_code=303)
