import string
import random


def generate_random_string(length: int) -> str:
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))


def generate_proxy_dict(country):
    random_string = generate_random_string(16)
   
    print(country)
    return {
        "http": f"http://devsp2023_xgmmdu:JRImTMuwGq_country-{country}@dc.proxy3g.com:11222",
        "https": f"http://devsp2023_xgmmdu:JRImTMuwGq_country-{country}@dc.proxy3g.com:11222",
    }