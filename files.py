import json
import os
import re
from http.cookiejar import MozillaCookieJar
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz


def get_vietnam_time():
    # Получаем текущее время в UTC
    utc_now = datetime.now(pytz.utc)
    
    # Конвертируем во временную зону Вьетнама
    vn_time = utc_now.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
    
    return str(vn_time)

def read_json_file(email):
    # Формирование пути к файлу JSON
    json_file_path = os.path.join('Waiting', email, f'{email}_initial_data.json')


    # Попытка открыть и прочитать JSON-файл
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data  # Возвращает словарь, загруженный из JSON-файла
    except FileNotFoundError:
        print(f"Файл {json_file_path} не найден.")
        return None  # Возвращает None, если файл не найден
    except json.JSONDecodeError:
        print("Ошибка при разборе файла JSON.")
        return None  # Возвращает None в случае ошибки парсинга
    

def read_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File {path} not found.")
        return None
    

def save_cookies_netscape_format(session, filename):
    with open(filename, 'w') as f:
        netscape_cookie_jar = MozillaCookieJar(f.name)
        for cookie in session.cookies:
            # Convert each cookie to the correct format for a Netscape cookie file
            netscape_cookie_jar.set_cookie(cookie)
        netscape_cookie_jar.save(ignore_discard=True, ignore_expires=True)

def save_cookies_json_format(session, filename):
    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
    with open(filename, 'w') as f:
        json.dump(cookies_dict, f, indent=4)  # serialize in pretty-print format


def extract_fb_dtsg_value(response_text):
    pattern = r'<input type="hidden" name="fb_dtsg" value="(.*?)"'
    match = re.search(pattern, response_text)
    if match:
        return match.group(1)
    else:
        return None
    

def extract_nh_value(text):
    nh_regex = re.compile(r'<input[^>]*name="nh"[^>]*value="([^"]+)"')
    match = nh_regex.search(text)
    if match:
        return match.group(1)
    else:
        return None  # или возбудить исключение, если предпочтительнее
    

def extract_jazoest_value(html_text):
    # Парсинг HTML
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Поиск тега input с именем 'jazoest'
    input_tag = soup.find('input', {'name': 'jazoest'})
    
    # Возвращаем значение атрибута 'value', если тег найден
    if input_tag:
        return input_tag.get('value')
    else:
        return None
    