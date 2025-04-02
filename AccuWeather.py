#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: accuweather.py
Author: thubmskx
Date: 2023/5/17 19:09
cron: 0 7 * * *
new Env('AccuWeather天气通知');
Description: 获取AccuWeather天气信息并通过Discord发送通知
"""
import requests
import json
import time
from datetime import datetime
import random
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import initialize


class AccuWeatherMonitor:
    def __init__(self):
        # API池配置
        self.api_keys = [
            "6rNvIz1GFFALoeArmv2kwHr8CwD7CbtJ",
            "lO7WxNbOs0TMUJfnxKQESMF1eKvHF9jj",  # 请替换为你的其他API密钥
            "mHbHIH8Yynn66b5DVwlVRtftArYN5Kvc",
            # "YOUR_API_KEY_4"
        ]
        self.current_api_index = 0
        self.latitude = 34.784658
        self.longitude = 113.819502
        self.language = "zh"
        self.details = "true"
        self.location_base_url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        self.current_conditions_url = "http://dataservice.accuweather.com/currentconditions/v1/"
        self.forecast_url = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/"
        self.location_key = None
        self.location_info = None

    def get_next_api_key(self):
        """获取下一个可用的API密钥"""
        self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)
        return self.api_keys[self.current_api_index]

    def make_request(self, url, params):
        """统一的请求处理函数，支持API轮询"""
        max_retries = len(self.api_keys)
        retries = 0
        
        while retries < max_retries:
            try:
                params["apikey"] = self.api_keys[self.current_api_index]
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                
                # 检查响应是否有效
                data = response.json()
                if data:  # 可以根据实际情况添加更具体的验证
                    return data
                
            except (requests.exceptions.RequestException, ValueError) as e:
                initialize.error_message(f"API请求失败 (key: {params['apikey']}): {str(e)}")
                
            # 如果当前API失败，切换到下一个
            self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)
            retries += 1
            
        return None

    def get_location_key(self):
        """获取位置的Key"""
        try:
            params = {
                "q": f"{self.latitude},{self.longitude}",
                "language": self.language,
                "details": self.details
            }
            
            data = self.make_request(self.location_base_url, params)
            if not data:
                initialize.error_message("❌ 所有API均无法获取位置信息")
                return None
                
            self.location_info = data
            self.location_key = self.location_info.get("Key")
            
            if self.location_key:
                location_name = self.location_info.get("LocalizedName", "未知位置")
                admin_area = self.location_info.get("AdministrativeArea", {}).get("LocalizedName", "")
                country = self.location_info.get("Country", {}).get("LocalizedName", "")
                return self.location_key
            else:
                initialize.error_message("❌ 无法获取位置Key")
                return None
                
        except Exception as e:
            initialize.error_message(f"❌ 获取位置信息时发生未知错误: {str(e)}")
            return None

    def get_current_weather(self):
        """获取当前天气状况"""
        if not self.location_key:
            initialize.error_message("❌ 位置Key未获取，无法获取天气信息")
            return None
            
        try:
            params = {
                "language": self.language,
                "details": self.details
            }
            
            url = f"{self.current_conditions_url}{self.location_key}"
            weather_data = self.make_request(url, params)
            
            if weather_data and len(weather_data) > 0:
                return weather_data[0]
            else:
                initialize.error_message("❌ 获取到的天气数据为空")
                return None
                
        except Exception as e:
            initialize.error_message(f"❌ 获取当前天气信息时发生未知错误: {str(e)}")
            return None

    def get_forecast(self):
        """获取5天天气预报"""
        if not self.location_key:
            initialize.error_message("❌ 位置Key未获取，无法获取天气预报")
            return None
            
        try:
            params = {
                "language": self.language,
                "details": self.details,
                "metric": "true"  # 使用公制单位
            }
            
            url = f"{self.forecast_url}{self.location_key}"
            forecast_data = self.make_request(url, params)
            
            if forecast_data and "DailyForecasts" in forecast_data:
                return forecast_data
            else:
                initialize.error_message("❌ 获取到的天气预报数据为空")
                return None
                
        except Exception as e:
            initialize.error_message(f"❌ 获取天气预报时发生未知错误: {str(e)}")
            return None

    def format_weather_message(self, current_weather, forecast):
        """格式化天气信息为通知消息"""
        try:
            if not current_weather or not forecast:
                return "❌ 无法获取完整的天气信息"
                
            # 获取位置信息
            location_name = self.location_info.get("LocalizedName", "未知位置")
            admin_area = self.location_info.get("AdministrativeArea", {}).get("LocalizedName", "")
            country = self.location_info.get("Country", {}).get("LocalizedName", "")
            full_location = f"{country} {admin_area} {location_name}"
            
            # 获取当前天气信息
            weather_text = current_weather.get("WeatherText", "未知")
            temperature = current_weather.get("Temperature", {}).get("Metric", {}).get("Value", "未知")
            feels_like = current_weather.get("RealFeelTemperature", {}).get("Metric", {}).get("Value", "未知")
            humidity = current_weather.get("RelativeHumidity", "未知")
            wind_speed = current_weather.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value", "未知")
            wind_direction = current_weather.get("Wind", {}).get("Direction", {}).get("Localized", "未知")
            uv_index = current_weather.get("UVIndex", "未知")
            uv_text = current_weather.get("UVIndexText", "未知")
            
            # 获取预报信息
            headline = forecast.get("Headline", {}).get("Text", "无特别预警")
            daily_forecasts = forecast.get("DailyForecasts", [])
            
            # 构建消息
            message = f"@thubmskxxi 🌈 **AccuWeather天气通知** 🌈\n\n"
            message += f"📍 **位置**: {full_location}\n"
            message += f"🕒 **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            message += f"🌤️ **当前天气**: {weather_text}\n"
            message += f"🌡️ **温度**: {temperature}°C (体感温度: {feels_like}°C)\n"
            message += f"💧 **湿度**: {humidity}%\n"
            message += f"🌬️ **风况**: {wind_direction} {wind_speed} km/h\n"
            message += f"☀️ **紫外线指数**: {uv_index} ({uv_text})\n\n"
            
            message += f"⚠️ **天气提醒**: {headline}\n\n"
            
            # 添加未来几天预报
            message += f"📅 **未来天气预报**:\n"
            for day in daily_forecasts[:3]:  # 只显示未来3天
                date = datetime.fromtimestamp(day.get("EpochDate", 0)).strftime('%m-%d')
                day_weather = day.get("Day", {}).get("IconPhrase", "未知")
                min_temp = day.get("Temperature", {}).get("Minimum", {}).get("Value", "未知")
                max_temp = day.get("Temperature", {}).get("Maximum", {}).get("Value", "未知")
                
                message += f"  • **{date}**: {day_weather}, {min_temp}°C - {max_temp}°C\n"
            
            message += f"\n📷 **天气图片**: https://raw.githubusercontent.com/xxiThubmsk/Typora/main/img/image-20250330231844401.png"
            
            return message
            
        except Exception as e:
            initialize.error_message(f"❌ 格式化天气信息时出错: {str(e)}")
            return f"❌ 格式化天气信息时出错: {str(e)}"

    def check_and_notify(self):
        """检查天气并发送通知"""
        # 简化日志输出，只保留关键错误信息
        
        # 获取位置Key
        location_key = self.get_location_key()
        if not location_key:
            return
        
        # 获取当前天气
        current_weather = self.get_current_weather()
        
        # 获取天气预报
        forecast = self.get_forecast()
        
        # 格式化消息并发送通知
        if current_weather and forecast:
            weather_message = self.format_weather_message(current_weather, forecast)
            # 只记录最终的通知消息
            initialize.clear_messages()
            initialize.info_message(weather_message)
            initialize.send_notify("")
        else:
            initialize.error_message("❌ 无法获取完整的天气信息，取消发送通知")


def main():
    """
    主函数
    
    :return:
    """
    # 简化启动和结束日志
    
    monitor = AccuWeatherMonitor()
    monitor.check_and_notify()


if __name__ == '__main__':
    initialize.init()  # 初始化日志系统
    main()
    # initialize.send_notify("")  # 发送通知
