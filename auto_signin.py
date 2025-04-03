import requests
import time
import os

# 签到函数
def checkin():
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
            print("签到成功！")
            print(f"响应内容: {response.text}")
        else:
            print(f"签到失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    checkin()