"""
塔斯汀汉堡签到

打开微信小程序抓sss-web.tastientech.com里面的user-token(一般在headers里)填到变量tsthbck里面即可

支持多用户运行
多用户用&或者@隔开
例如账号1：10086 账号2： 1008611
则变量为10086&1008611
export tsthbck=""

cron: 55 1,9,16 * * *
"""

import os
import re
import json
import logging
from typing import Optional, List
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TastyBurger:
    BASE_URL = "https://sss-web.tastientech.com/api"
    VERSION = "1.46.8"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'user-token': token,
            'version': self.VERSION,
            'channel': '1'
        }
        self.log_messages = []

    def log(self, message: str):
        """统一日志处理"""
        logger.info(message)
        self.log_messages.append(f"{message}\n")

    def get_activity_id(self) -> Optional[str]:
        """获取签到活动ID"""
        try:
            data = {
                "shopId": "",
                "birthday": "",
                "gender": 0,
                "nickName": None,
                "phone": ""
            }
            response = requests.post(
                f"{self.BASE_URL}/minic/shop/intelligence/banner/c/list",
                json=data,
                headers=self.headers
            ).json()
            
            for item in response.get('result', []):
                if item['bannerName'] == '每日签到':
                    qd = item['jumpPara']
                    activity_id = re.findall('activityId%2522%253A(.*?)%257D', qd)[0]
                    self.log(f"获取到本月签到代码：{activity_id}")
                    return activity_id
            return None
        except Exception as e:
            self.log(f"获取活动ID失败: {str(e)}")
            return None

    def sign_in(self) -> bool:
        """执行签到流程"""
        try:
            # 获取用户信息
            user_info = requests.get(
                f"{self.BASE_URL}/intelligence/member/getMemberDetail",
                headers=self.headers
            ).json()
            
            if user_info['code'] != 200:
                self.log(f"获取用户信息失败: {user_info.get('msg', '未知错误')}")
                return False
                
            phone = user_info['result']['phone']
            self.log(f"账号：{phone} 登录成功")
            
            # 获取活动ID并签到
            activity_id = self.get_activity_id() or "57"
            
            # 执行签到
            sign_data = {
                "activityId": activity_id,
                "memberName": "",
                "memberPhone": phone
            }
            
            sign_result = requests.post(
                f"{self.BASE_URL}/sign/member/signV2",
                json=sign_data,
                headers=self.headers
            ).json()
            
            if sign_result['code'] == 200:
                reward = sign_result['result']['rewardInfoList'][0]
                if reward['rewardName']:
                    self.log(f"签到情况：获得 {reward['rewardName']}")
                else:
                    self.log(f"签到情况：获得 {reward['point']} 积分")
                return True
            else:
                self.log(f"签到情况：{sign_result.get('msg', '签到失败')}")
                return False
                
        except Exception as e:
            self.log(f"签到过程出错: {str(e)}")
            return False

def main():
    # 获取环境变量中的账号信息
    tokens = re.split("@|&", os.environ.get("tsthbck", ""))
    if not tokens or tokens == ['']:
        logger.error("未找到账号配置，请设置环境变量 tsthbck")
        return

    logger.info(f"共找到 {len(tokens)} 个账号")
    all_messages = []
    
    for i, token in enumerate(tokens, 1):
        if not token.strip():
            continue
            
        logger.info(f"开始处理第 {i} 个账号")
        logger.info("----------------------")
        
        burger = TastyBurger(token)
        burger.sign_in()
        all_messages.extend(burger.log_messages)
        
        logger.info("----------------------")

    # 发送通知
    try:
        from sendNotify import send
        send("塔斯汀汉堡", ''.join(all_messages))
    except ImportError:
        logger.warning("未找到通知模块，跳过通知发送")
    except Exception as e:
        logger.error(f"发送通知失败: {str(e)}")

if __name__ == '__main__':
    main()
    