"""
Function:
    HIT 每日上报
Author:
    leishufei
"""
import requests
from urllib.parse import urlencode
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.header import Header


class Reporter(object):
    def __init__(self):
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36 Edg/85.0.564.51",
            "Origin": "https://xg.hit.edu.cn",
            "Host": "xg.hit.edu.cn",
            "Cookie": ""
        }

    def get_cookie(self, account, password):
        """
        获取 cookie，后续操作通过 cookie 来识别学生身份
        :param account: 登陆账号
        :param password: 登录密码
        :return: cookie
        """
        url = "http://ids.hit.edu.cn/authserver/login?service=https://xg.hit.edu.cn/zhxy-xgzs/common/casLogin?params=L3hnX21vYmlsZS94c0hvbWU="
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options=chrome_options)
        # driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 5)
        driver.get(url)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form#casLoginForm")))
        account_input = driver.find_element_by_id("username")
        password_input = driver.find_element_by_id("password")
        submit_button = driver.find_element(By.CSS_SELECTOR, "form#casLoginForm button.auth_login_btn.primary.full_width")
        account_input.send_keys(account)
        password_input.send_keys(password)
        submit_button.click()
        cookies = driver.get_cookies()[0]
        cookie = cookies["name"] + "=" + cookies["value"]
        self.headers["Cookie"] = cookie
        driver.quit()

    def get_token(self):
        """
        获取 token 值
        :return: token
        """
        url = "https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xs/getToken"
        response = requests.post(url, headers=self.headers)
        token = response.text
        return token

    def save_twsb(self, token):
        """
        保存之前上报体温信息并新增一个待填写的体温信息
        :param token: 新增上报信息前需要 post 一个请求，请求参数 为 token
        :return:
        """
        base_url = f"https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xsTwsb/saveTwsb?"
        data = {
            "info": {
                "token": token
            }
        }
        url = base_url + urlencode(data).replace("%27", "%22")
        requests.post(url, headers=self.headers)

    def get_twsb_id(self):
        """
        获取待填写体温信息的 id 值
        :return:
        """
        url = "https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xsTwsb/getTwsb"
        response = requests.post(url, headers=self.headers)
        json_data = json.loads(response.text)
        id_ = json_data["module"][0]["id"]
        return id_

    def post_twsb_info(self):
        """
        post 请求，上报体温信息
        :return:
        """
        token = self.get_token()
        self.save_twsb(token)
        id_ = self.get_twsb_id()
        base_url = "https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xsTwsb/updateTwsb?"
        data = {
            "info": {
                "data": {
                    "id": id_,
                    "bs": ""
                }
            }
        }
        for i in range(2):
            temp = format(random.randint(362, 366) * 1.0 / 10, ".1f")
            time_ = ""
            # 早上和晚上对应的参数不同，需要分别进行处理
            if i == 0:
                # 提交早上体温
                data["info"]["data"].update({"sdid1": "1", "tw1": temp, "fr1": "0"})
                data["info"]["data"]["bs"] = "1"
                time_ = "早上"
            elif i == 1:
                # 提交晚上体温
                data["info"]["data"].update({"sdid2": "3", "tw2": temp, "fr2": "0"})
                data["info"]["data"]["bs"] = "2"
                time_ = "晚上"

            url = base_url + urlencode(data).replace("%27", "%22")
            response = requests.post(url, headers=self.headers)
            json_data = json.loads(response.text)
            is_success = bool(json_data["isSuccess"])
            if is_success:
                print(f"上报结果：{time_}温度信息上报成功")
            else:
                print(f"上报结果：{time_}温度信息上报失败")
            time.sleep(2)

    def get_xxsb_id(self):
        """
        获取待上传信息的 id
        :return: id
        """
        url = "https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xs/getYqxxList"
        response = requests.post(url, headers=self.headers)
        # print(response.text)
        json_data = json.loads(response.text)
        id_ = json_data["module"]["data"][0]["id"]
        return id_

    def new_xxsb(self):
        """
        新增一个待填报的每日信息
        :return:
        """
        url = "https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xs/csh"
        requests.post(url, headers=self.headers)

    def post_xxsb_info(self):
        """
        post 请求，上报每日信息
        :return:
        """
        self.new_xxsb()
        id_ = self.get_xxsb_id()
        base_url = "https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xs/saveYqxx?"
        data = {
            "info": {
                "model": {
                    "id": id_,
                    "dqszd": "01",
                    "hwgj": "",
                    "hwcs": "",
                    "hwxxdz": "",
                    "dqszdsheng": "230000",
                    "dqszdshi": "230100",
                    "dqszdqu": "230103",
                    "gnxxdz": "HIT A16",
                    "dqztm": "01",
                    "dqztbz": "",
                    "brfsgktt": "0",
                    "brzgtw": "",
                    "brsfjy": "",
                    "brjyyymc": "",
                    "brzdjlm": "",
                    "brzdjlbz": "",
                    "qtbgsx": "",
                    "sffwwhhb": "0",
                    "sftjwhjhb": "0",
                    "tcyhbwhrysfjc": "0",
                    "sftzrychbwhhl": "0",
                    "sfjdwhhbry": "0",
                    "tcjtfs": "",
                    "tchbcc": "",
                    "tccx": "",
                    "tczwh": "",
                    "tcjcms": "",
                    "gpsxx": "",
                    "sfjcqthbwhry": "0",
                    "sfjcqthbwhrybz": "",
                    "tcjtfsbz": ""
                }
            }
        }
        url = base_url + urlencode(data).replace("%27", "%22")
        response = requests.post(url, headers=self.headers)
        json_data = json.loads(response.text)
        is_success = bool(json_data["isSuccess"])
        if is_success:
            print("上报结果：每日信息上报成功")
        else:
            print("上报结果：每日信息上报失败")

    def send_email(self, text):
        """
        发送邮件
        :param text: 待发送的文本
        :return:
        """
        sender = ""  # 发送方的邮箱
        receiver = ""  # 接收方的邮箱
        host = "smtp.xx.com"  # 邮箱服务器
        user_name = ""  # 邮箱登录账号
        authorization_code = ""  # 开启 smtp 服务得到的授权码，而不是 qq 密码
        subject = "上传结果"  # 邮件主题

        smtp = SMTP_SSL(host)
        smtp.login(user_name, authorization_code)

        msg = MIMEText(text, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["from"] = sender
        msg["to"] = receiver

        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()

    def run(self):
        users = {
            "user": {
                "account": "",
                "password": ""
            },
        }
        text = ""
        for user in users.keys():
            account = users[user]["account"]
            password = users[user]["password"]

            if account != "" and password != "":
                print("=" * 30 + "\n" + f"当前待上报用户：{user}")
                self.get_cookie(account, password)
                text += f"{user}\n"
                try:
                    self.post_xxsb_info()
                    text += "每日信息\t【上报成功】\n"
                except:
                    print("上报结果：每日信息上报失败")
                    text += "每日信息\t【上报失败】\n"
                time.sleep(2)
                try:
                    self.post_twsb_info()
                    text += "体温信息\t【上报成功】\n"
                except:
                    print("上报结果：体温信息上报失败")
                    text += "体温信息\t【上报失败】\n\n"
                print("=" * 20 + "\n")
            time.sleep(5)
        self.send_email(text)


if __name__ == "__main__":
    reporter = Reporter()
    reporter.run()
