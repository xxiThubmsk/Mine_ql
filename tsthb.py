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
import requests
from datetime import datetime
import initialize  # 引入初始化模块

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

    def get_activity_id(self):
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
            )
            
            response_json = response.json()
            
            for item in response_json.get('result', []):
                if '每日签到' in item.get('bannerName', ''):
                    qd = item['jumpPara']
                    activity_id = json.loads(qd)['activityId']
                    initialize.info_message(f"获取到本月签到代码：{activity_id}")
                    return str(activity_id)
            return None
        except Exception as e:
            initialize.error_message(f"获取活动ID失败: {str(e)}")
            return None

    def get_points(self):
        """查询积分余额"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/intelligence/member/getMemberDetail",
                headers=self.headers
            ).json()
            
            if response['code'] == 200:
                points = response['result']['point']
                initialize.info_message(f"当前积分：{points}")
                return points
            return None
        except Exception as e:
            initialize.error_message(f"查询积分失败: {str(e)}")
            return None

    def get_sign_history(self):
        """查询本月签到记录"""
        try:
            activity_id = self.get_activity_id()
            if not activity_id:
                return
                
            response = requests.get(
                f"{self.BASE_URL}/sign/member/getSignRecordV2?activityId={activity_id}",
                headers=self.headers
            ).json()
            
            if response['code'] == 200:
                total_days = response['result'].get('totalSignDays', 0)
                initialize.info_message(f"本月已签到：{total_days}天")
        except Exception as e:
            initialize.error_message(f"查询签到记录失败: {str(e)}")

    def sign_in(self):
        """执行签到流程"""
        try:
            # 获取用户信息
            response = requests.get(
                f"{self.BASE_URL}/intelligence/member/getMemberDetail",
                headers=self.headers
            )
            
            user_info = response.json()
            
            if user_info['code'] != 200:
                initialize.error_message(f"获取用户信息失败: {user_info.get('msg', '未知错误')}")
                return False
                
            phone = user_info['result']['phone']
            initialize.info_message(f"账号：{phone} 登录成功")
            
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
                    initialize.info_message(f"签到情况：获得 {reward['rewardName']}")
                else:
                    initialize.info_message(f"签到情况：获得 {reward['point']} 积分")
                # 在签到完成后查询积分和签到历史
                self.get_points()
                self.get_sign_history()
                return True
            else:
                initialize.error_message(f"签到情况：{sign_result.get('msg', '签到失败')}")
                return False
                
        except Exception as e:
            initialize.error_message(f"签到过程出错: {str(e)}")
            return False

def main():
    initialize.init()  # 初始化日志系统
    
    # 获取环境变量中的账号信息
    tokens = re.split("@|&", os.environ.get("tsthbck", ""))
    if not tokens or tokens == ['']:
        initialize.error_message("未找到账号配置，请设置环境变量 tsthbck")
        return

    initialize.info_message(f"共找到 {len(tokens)} 个账号")
    
    for i, token in enumerate(tokens, 1):
        if not token.strip():
            continue
            
        initialize.info_message(f"开始处理第 {i} 个账号")
        initialize.info_message("----------------------")
        
        burger = TastyBurger(token)
        burger.sign_in()
        
        initialize.info_message("----------------------")

    # 发送通知
    initialize.send_notify("塔斯汀汉堡自动签到")

if __name__ == '__main__':
    main()
    