"""
塔斯汀汉堡签到

打开微信小程序抓sss-web.tastientech.com里面的user-token(一般在headers里)填到变量tsthbck里面即可

支持多用户运行

多用户用&或者@隔开
例如账号1：10086 账号2： 1008611
则变量为10086&1008611
export tsthbck=""

cron: 55 1,9,16 * * *
const $ = new Env("塔斯汀汉堡");
"""
import requests
import re
import os
import time
import json
#初始化
print('============📣初始化📣============')
#版本
github_file_name = 'tsthb.py'
sjgx = '2025-02-17T21:30:11.000+08:00'
version = '1.46.8'


def myprint(text):
    """打印并保存日志"""
    print(text)
    try:
        global all_print_list
        all_print_list.append(f"{text}\n")
    except:
        all_print_list = []
        all_print_list.append(f"{text}\n")

# 发送通知消息
def send_notification_message(title):
    try:
        from sendNotify import send

        send(title, ''.join(all_print_list))
    except Exception as e:
        if e:
            print('发送通知消息失败！')

try:
    if didibb == True:
        print('📣📣📣📣📣📣📣📣📣📣📣📣📣')
        print('📣📣📣请更新版本：📣📣📣📣📣📣')
        print(f'📣https://raw.githubusercontent.com/linbailo/zyqinglong/main/{github_file_name}📣')
        print('📣📣📣📣📣📣📣📣📣📣📣📣📣')
    else:
        print(f"无版本更新")
except Exception as e:
    print('无法检查版本更新')


#分割变量
if 'tsthbck' in os.environ:
    tsthbck = re.split("@|&",os.environ.get("tsthbck"))
    print(f'查找到{len(tsthbck)}个账号')
else:
    tsthbck =['']
    print('无tsthbck变量')


def qdsj(ck):
    headers = {'user-token':ck,'version':version,'channel':'1'}
    data = {"shopId":"","birthday":"","gender": 0,"nickName":None,"phone":""}
    dl = requests.post(url='https://sss-web.tastientech.com/api/minic/shop/intelligence/banner/c/list',json=data,headers=headers).json()
    activityId = ''
    for i in dl['result']:
        if i['bannerName'] == '每日签到':
            qd = i['jumpPara']
            activityId = re.findall('activityId%2522%253A(.*?)%257D',qd)[0]
            print(f"获取到本月签到代码：{activityId}")
            #activityId = json.loads(qd)['activityId']
    return activityId



def yx(ck):
    activityId= ''
    try:
        activityId = qdsj(ck)
    except Exception as e:
        activityId = ''
    if activityId == '':
        activityId = 57
    headers = {'user-token':ck,'version':version,'channel':'1'}
    dl = requests.get(url='https://sss-web.tastientech.com/api/intelligence/member/getMemberDetail',headers=headers).json()
    if dl['code'] == 200:
        myprint(f"账号：{dl['result']['phone']}登录成功")
        phone = dl['result']['phone']
        data = {"activityId":activityId,"memberName":"","memberPhone":phone}
        lq = requests.post(url='https://sss-web.tastientech.com/api/sign/member/signV2',json=data,headers=headers).json()
        if lq['code'] == 200:
            if lq['result']['rewardInfoList'][0]['rewardName'] == None:
                myprint(f"签到情况：获得 {lq['result']['rewardInfoList'][0]['point']} 积分")
            else:
                myprint(f"签到情况：获得 {lq['result']['rewardInfoList'][0]['rewardName']}")
        else:
            myprint(f"签到情况：{lq['msg']}")



def main():
    z = 1
    for ck in tsthbck:
        try:
            myprint(f'登录第{z}个账号')
            myprint('----------------------')
            yx(ck)
            myprint('----------------------')
            z = z + 1
        except Exception as e:
            print(e)
            print('未知错误')

if __name__ == '__main__':
    print('====================')
    try:
        main()
    except Exception as e:
        print('未知错误')
    print('====================')
    try:
        send_notification_message(title='塔斯汀汉堡')  # 发送通知
    except Exception as e:
        print('小错误')
    