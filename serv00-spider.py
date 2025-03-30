#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: serv00-spider.py
Author: WFRobert (Modified)
Date: 2023/5/17 19:09
cron: 0 5 6 * * ?
new Env('Serv00服务器监控');
Description: 监控Serv00服务器空位状态
"""
import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime, timedelta
import random
import initialize


class Serv00Spider:
    def __init__(self):
        self.url = "https://www.serv00.com"
        self.last_availability_found_time = None  # 上次发现空位的时间
        self.last_test_time = None  # 上次发送测试通知的时间
        self.initial_test_interval = timedelta(minutes=30)  # 初始间隔30分钟
        self.max_test_interval = timedelta(days=1)  # 最大间隔1天
        self.current_test_interval = self.initial_test_interval  # 当前测试通知间隔

    def check_availability(self):
        """检查Serv00网站上的账户可用性"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            response = requests.get(self.url, headers=headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            account_status_element = soup.find('span', {'class': 'button is-large is-flexible'}) or \
                                     soup.find('div', {'class': 'button is-large is-flexible'}) or \
                                     soup.find('button', {'class': 'button is-large is-flexible'})

            if account_status_element:
                text_content = account_status_element.get_text(strip=True)
                initialize.info_message(f"获取到的原始状态文本: {text_content}")
                parts = text_content.split('/')
                if len(parts) >= 2:
                    try:
                        current_str = parts[0].strip()
                        total_str = ""
                        for char in parts[1].strip():
                            if char.isdigit(): total_str += char
                            else: break
                        if current_str.isdigit() and total_str.isdigit():
                            current = int(current_str); total = int(total_str)
                            if total > 0:
                                percentage_used = (current / total) * 100
                                status_msg = f"当前账户数: {current}/{total} (已用{percentage_used:.1f}%)"
                                initialize.info_message(f"检查结果: {status_msg}")
                                return current < total, status_msg
                            else:
                                status_msg = f"解析状态异常: 总数({total})无效. 原始文本: {text_content}"
                                initialize.error_message(status_msg)
                                return False, status_msg
                        else:
                             status_msg = f"无法从状态文本中解析数字: '{current_str}', '{total_str}'. 原始文本: {text_content}"
                             initialize.error_message(status_msg)
                             return False, status_msg
                    except ValueError as ve:
                        status_msg = f"解析数字时出错: {ve}. 原始文本: {text_content}"
                        initialize.error_message(status_msg)
                        return False, status_msg
            else:
                status_msg = "未在页面上找到预期的账户状态元素。"
                initialize.error_message(status_msg)
                return False, status_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            initialize.error_message(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"检查过程中发生未知错误: {str(e)}"
            initialize.error_message(error_msg)
            return False, error_msg

    def perform_check_and_notify(self):
        """执行一次检查，如果发现空位则发送通知"""
        current_time = datetime.now()
        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        initialize.info_message(f"[{current_time_str}] 开始新一轮检查...")

        available, status_message = self.check_availability()

        if available:
            # 发现空位
            notify_msg = f"@thubmskxxi 太棒了！Serv00 服务器可能有空位了！\n\n" \
                         f"检测到的状态: {status_message}\n" \
                         f"检查时间: {current_time_str}\n\n" \
                         f"请尽快访问: {self.url}"
            initialize.info_message(f"发现潜在空位！状态: {status_message}")
            initialize.info_message(notify_msg)
            
            # 更新最后发现空位的时间
            self.last_availability_found_time = current_time
            # 重置测试通知计时器和间隔
            self.last_test_time = current_time
            self.current_test_interval = self.initial_test_interval
            
            # 如果有空位，设置较短的检查间隔，以便频繁通知
            return 300  # 返回5分钟(300秒)的检查间隔
        else:
            # 未发现空位，检查是否发送测试通知
            should_send_test = False

            # 条件1: 距离上次测试通知是否足够久 (或者从未发送过)
            time_since_last_test = timedelta.max  # 设为无穷大，如果从未发送过
            if self.last_test_time is not None:
                time_since_last_test = current_time - self.last_test_time

            if time_since_last_test >= self.current_test_interval:
                # 条件2: 距离上次发现空位是否足够久
                time_since_last_avail = timedelta.max
                if self.last_availability_found_time is not None:
                    time_since_last_avail = current_time - self.last_availability_found_time

                # 只有当距离上次测试通知、以及距离上次发现空位都超过当前测试间隔时，才发送
                if time_since_last_avail >= self.current_test_interval:
                    should_send_test = True

            if should_send_test:
                initialize.info_message(f"未发现空位，发送心跳测试通知 (当前间隔: {self.current_test_interval})。")

                test_msg = f"@thubmskxxi Serv00 监控脚本心跳检测。\n\n" \
                           f"当前脚本仍在运行，持续监控中。\n\n" \
                           f"检测到的最新服务器状态: {status_message}\n" \
                           f"(状态检查于: {current_time_str})\n\n" \
                           f"本次心跳通知时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                           f"当前测试通知发送间隔: {self.current_test_interval}."
                
                initialize.info_message(test_msg)
                
                # 更新上次测试通知时间
                self.last_test_time = current_time
                # 计算并更新下一次的测试间隔（翻倍，但不超过最大值）
                next_interval_seconds = self.current_test_interval.total_seconds() * 2
                self.current_test_interval = timedelta(seconds=next_interval_seconds)
                if self.current_test_interval > self.max_test_interval:
                    self.current_test_interval = self.max_test_interval
                initialize.info_message(f"心跳测试通知已发送。下一次测试通知间隔更新为: {self.current_test_interval}")
                
                # 返回特殊值-1表示这是心跳测试
                return -1
            
            # 如果不需要发送测试通知，返回正常的随机检查间隔
            return random.uniform(3, 10)


def main():
    """
    主函数
    
    :return:
    """
    initialize.info_message("Serv00服务器监控脚本已启动，将持续监控服务器状态...")
    
    spider = Serv00Spider()
    
    while True:
        try:
            # 执行检查并获取下次检查的间隔时间
            check_interval = spider.perform_check_and_notify()
            
            # 如果是空位状态(5分钟间隔)，则立即发送通知
            if check_interval == 300:
                initialize.info_message(f"发现空位！每5分钟重复发送通知，等待 {check_interval} 秒后再次通知...")
                initialize.send_notify("Serv00服务器有空位通知")  # 立即发送通知
                initialize.message_list.clear()  # 清空消息列表，确保下次通知不包含旧消息
            # 如果是心跳测试，也发送通知
            elif check_interval == -1:
                initialize.info_message("发送心跳测试通知...")
                try:
                    # 添加一些调试信息
                    initialize.info_message(f"消息列表长度: {len(initialize.message_list)}")
                    initialize.info_message(f"消息内容: {initialize.message_list}")
                    initialize.send_notify("Serv00服务器监控心跳测试")
                    initialize.info_message("通知发送完成")
                except Exception as e:
                    initialize.error_message(f"发送通知时出错: {str(e)}")
                initialize.message_list.clear()  # 清空消息列表
                check_interval = random.uniform(3, 10)  # 设置下一次检查的间隔
            else:
                initialize.info_message(f"等待 {check_interval:.1f} 秒后进行下次检查...")
            
            time.sleep(check_interval)
        except KeyboardInterrupt:
            initialize.info_message("检测到用户中断，正在退出程序...")
            break
        except Exception as loop_error:
            error_msg = f"主循环发生意外错误: {str(loop_error)}"
            initialize.error_message(error_msg)
            initialize.error_message("将在1分钟后重试...")
            time.sleep(60)
    
    initialize.info_message("爬虫程序已停止。")


if __name__ == '__main__':
    initialize.init()  # 初始化日志系统
    main()
    initialize.send_notify("Serv00服务器监控")  # 发送通知
