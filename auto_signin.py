import requests
import time
import os
from datetime import datetime, timezone
import initialize

def check_cookie_expiration():
    # user_id 过期时间
    expiration_date = datetime(2025, 4, 17, 11, 32, 31, tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    days_remaining = (expiration_date - current_time).days
    
    if days_remaining <= 30:  # 如果剩余天数小于30天
        initialize.error_message(f"⚠️ 警告：Cookie 将在 {days_remaining} 天后过期，请及时更新！")
    return days_remaining > 0  # 返回 cookie 是否有效

def checkin():
    if not check_cookie_expiration():
        initialize.error_message("❌ Cookie 已过期，请更新后再试！")
        return
        
    url = "https://www.xxworld.org/api/checkin"
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.xxworld.org',
        'referer': 'https://www.xxworld.org/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'cookie': 'browser-fingerprint=kf68kzjw4920bu92alzob; NEXT_LOCALE=zh; user_id=67d9598dfced55ab60efbdde'
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            initialize.info_message("✅ 签到成功！")
            initialize.info_message(f"响应内容: {response.text}")
        else:
            initialize.error_message(f"❌ 签到失败，状态码: {response.status_code}")
            initialize.error_message(f"错误信息: {response.text}")
    except Exception as e:
        initialize.error_message(f"❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    initialize.init()  # 初始化日志系统
    checkin()
    initialize.send_notify("XXWorld 自动签到")  # 发送通知