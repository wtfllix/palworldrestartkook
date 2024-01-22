import requests
from urllib.parse import urlencode
import psutil
import time
from datetime import datetime,timedelta
import subprocess
import sys


# 定义 API 接口的基础 URL
api_base_url = "https://www.kookapp.cn"
token = "Your bot token"
target_id = "Default channel id"
guild_id = "guild_id"
process_name = "PalServer-Win64-Test-Cmd.exe"
interval_hours = 3
shortcut_path = r"path to server.exe"


# 定义处理请求的函数
def call_api(endpoint, method="GET", params=None, data=None):
    url = api_base_url + endpoint

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    if method == "GET":
        if params is not None:
            query_string = urlencode(params)
            url += "?" + query_string
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    else:
        raise ValueError("Invalid HTTP method.")

    return response.json()
#获取服务器信息
def get_guild_list(page=None, page_size=None, sort=None):
    endpoint = "/api/v3/guild/list"

    params = {}
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size
    if sort is not None:
        params["sort"] = sort

    response = call_api(endpoint, method="GET", params=params)
    return response

# 发送信息 (guild_id:服务器id target_id：频道id)
def create_message(content):
    endpoint = "/api/v3/message/create"
    data = {
    "type": 1,
    "target_id": target_id,
    "content": content,
    "guild_id": guild_id
    }
    response = call_api(endpoint, method="POST",data=data)
    return response

# 通过进程名查找进程
def find_process_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc
    return None

# 获取进程的内存信息（以MB为单位）
def get_process_memory_info(process):
    memory_info = process.memory_info()
    memory_usage = memory_info.rss / (1024 * 1024)  # 内存占用转换为MB单位
    memory_usage_mb = round(memory_usage, 2)  # 
    memory_percent = round(process.memory_percent(), 2)
    return {
        'pid': process.pid,
        'name': process.name(),
        'memory_usage': memory_usage_mb,
        'memory_percent': memory_percent
    }

# 监控特定进程的内存信息
def monitor_process_memory(process_name):
    while True:
        process = find_process_by_name(process_name)
        if process is None:
            print("未找到进程：", process_name)
            return None
        else:
            memory_info = get_process_memory_info(process)
            memory_info_format = {
            'pid': memory_info['pid'],
            'name': memory_info['name'],
            'memory_usage': memory_info['memory_usage'],
            'memory_percent': memory_info['memory_percent']
                        }
            return memory_info_format

def terminate_process_by_name(process_name):
    for proc in psutil.process_iter():
        if proc.name() == process_name:
            proc.terminate()

def msg_construct(memory_usage_mb,memory_percent):
    current_time = datetime.now()
    next_restart_time = current_time + timedelta(hours=interval_hours)
    formatted_currenttime = str(current_time)[:19]
    formatted_next_restart_time = str(next_restart_time)[:19]
    full_msg_format = f"{formatted_currenttime}\n当前服务器进程已占用{memory_percent}%，用量{memory_usage_mb}MB。正在重启中...\n服务器将于{formatted_next_restart_time}重启。"
    return full_msg_format


def main():
        kook_info = get_guild_list()
        guild_data = kook_info['data']
        guild_data_items = guild_data['items']
        name_id_list = [(item['name'], item['id'],item['default_channel_id']) for item in guild_data_items]
        for name, id, default_channel_id in name_id_list:
            guild_name_id = f"名称：{name}，公会ID：{id}，默认频道ID：{default_channel_id}"
            print(guild_name_id)
        user_input =input("是否需要启动服务器？输入 Yes or No:")
        while True:               
            if user_input == "Yes":
                while True:
                    mem_msg = monitor_process_memory(process_name)
                    if mem_msg is None:
                        subprocess.Popen(['explorer', shortcut_path])
                        print("正在启动 " + process_name)
                        time.sleep(2)
                    else:
                        response = create_message(msg_construct(mem_msg['memory_usage'],mem_msg['memory_percent']))
                        print(response)
                        time.sleep(interval_hours * 60 * 60)
                        terminate_process_by_name(process_name)
                        time.sleep(2)
                        subprocess.Popen(['explorer', shortcut_path])
                        print("重启成功")
                        time.sleep(2)
            else:
                sys.exit()
# 调用主函数
        
if __name__=="__main__":
    main()