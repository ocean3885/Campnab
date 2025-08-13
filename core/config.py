import json
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE = Path("config.json")

def load_app_config() -> Dict[str, Any]:
    """애플리케이션 전체 설정을 불러옵니다."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 마이그레이션 로직: 기존 config.json 형식을 새로운 구조로 변환
            if "sites" not in config:
                print("[INFO] 기존 설정 파일을 새로운 형식으로 변환합니다.")
                new_config = {
                    "sites": {
                        "imsil_forest": {
                            "display_name": "임실성수산왕의숲",
                            "dates": config.get("dates", []),
                            "monitoring_active": config.get("monitoring_active", False)
                        }
                    }
                }
                save_app_config(new_config)
                return new_config
            return config
    
    # 기본 설정: 여러 사이트를 지원하는 구조
    return {
        "sites": {
            "imsil_forest": {
                "display_name": "임실성수산왕의숲",
                "dates": ["20250815", "20250816"],
                "monitoring_active": True
            }
        }
    }

def save_app_config(config: Dict[str, Any]):
    """애플리케이션 전체 설정을 저장합니다."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
