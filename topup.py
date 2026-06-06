import os
import time
import datetime
import random
import re
import asyncio
import html
import json
import concurrent.futures
from collections import defaultdict
from dotenv import load_dotenv

from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions
from curl_cffi.requests import AsyncSession

from aiogram import Bot, Dispatcher, Router, BaseMiddleware, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, or_f
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

import database as db

# ==========================================
# 1. Configuration & Global Variables
# ==========================================
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 6437656033))
GOOGLE_EMAIL = os.getenv('GOOGLE_EMAIL')
GOOGLE_PASS = os.getenv('GOOGLE_PASS')

if not BOT_TOKEN:
    print("❌ Error: BOT_TOKEN is missing in the .env file.")
    exit()

MMT = datetime.timezone(datetime.timedelta(hours=6, minutes=30))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
main_router = Router()

IS_MAINTENANCE = False
GLOBAL_SCAMMERS = set()
user_locks = defaultdict(asyncio.Lock)
api_semaphore = asyncio.Semaphore(10)
auth_lock = asyncio.Lock()

# Clone Bot များ Code ဖြည့်လျှင် ဖြတ်မည့် Fees ရာခိုင်နှုန်း (ဥပမာ 0.05 = 5%)
CLONE_BOT_FEE_PERCENT = 0.05 

BR_EMOJI = "5228878788867142213"   
PH_EMOJI = "5231361434583049965"



last_login_time = 0

# Global variables keyed by bot_id
GLOBAL_SCRAPERS = {}
GLOBAL_COOKIES = {}
GLOBAL_CSRF = {}

# ==========================================
# 2. Package Definitions
# ==========================================
DOUBLE_DIAMOND_PACKAGES = {
    '55': [{'pid': '22590', 'price': 39.0, 'name': '50+50 💎'}],
    '165': [{'pid': '22591', 'price': 116.9, 'name': '150+150 💎'}],
    '275': [{'pid': '22592', 'price': 187.5, 'name': '250+250 💎'}],
    '565': [{'pid': '22593', 'price': 385.0, 'name': '500+500 💎'}],
}

BR_PACKAGES = {
    '86': [{'pid': '13', 'price': 61.5, 'name': '86 💎'}],
    '172': [{'pid': '23', 'price': 122.0, 'name': '172 💎'}],
    '257': [{'pid': '25', 'price': 177.5, 'name': '257 💎'}],
    '343': [{'pid': '13', 'price': 61.5, 'name': '86 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}],
    '429': [{'pid': '23', 'price': 122.0, 'name': '172 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}],
    '514': [{'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}],
    '600': [{'pid': '13', 'price': 61.5, 'name': '86 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}],
    '706': [{'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '878': [{'pid': '23', 'price': 122.0, 'name': '172 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '963': [{'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '1049': [{'pid': '13', 'price': 61.5, 'name': '86 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '1135': [{'pid': '23', 'price': 122.0, 'name': '172 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '1412': [{'pid': '26', 'price': 480.0, 'name': '706 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '1584': [{'pid': '23', 'price': 122.0, 'name': '172 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '1755': [{'pid': '13', 'price': 61.5, 'name': '86 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '2195': [{'pid': '27', 'price': 1453.0, 'name': '2195 💎'}],
    '2538': [{'pid': '13', 'price': 61.5, 'name': '86 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '27', 'price': 1453.0, 'name': '2195 💎'}],
    '2901': [{'pid': '27', 'price': 1453.0, 'name': '2195 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}],
    '3244': [{'pid': '13', 'price': 61.5, 'name': '86 💎'}, {'pid': '25', 'price': 177.5, 'name': '257 💎'}, {'pid': '26', 'price': 480.0, 'name': '706 💎'}, {'pid': '27', 'price': 1453.0, 'name': '2195 💎'}],
    '3688': [{'pid': '28', 'price': 2424.0, 'name': '3688 💎'}],
    '5532': [{'pid': '29', 'price': 3660.0, 'name': '5532 💎'}],
    '9288': [{'pid': '30', 'price': 6079.0, 'name': '9288 💎'}],
    'meb': [{'pid': '26556', 'price': 196.5, 'name': 'Epic Monthly Package'}],
    'tp': [{'pid': '33', 'price': 402.5, 'name': 'Twilight Passage'}],
    'web': [{'pid': '26555', 'price': 39.0, 'name': 'Elite Weekly Paackage'}],
    'wp': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'}],
    'wp2': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(2)],
    'wp3': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(3)],
    'wp4': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(4)],
    'wp5': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(5)],
    'wp6': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(6)],
    'wp7': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(7)],
    'wp8': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(8)],
    'wp9': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(9)],
    'wp10': [{'pid': '16642', 'price': 76.0, 'name': 'Weekly Pass'} for _ in range(10)]
}

PH_PACKAGES = {
    '11': [{'pid': '212', 'price': 9.50, 'name': '11 💎'}],
    '22': [{'pid': '213', 'price': 19.00, 'name': '22 💎'}],
    '33': [{'pid': '213', 'price': 19.00, 'name': '22 💎'}, {'pid': '212', 'price': 9.50, 'name': '11 💎'}],
    '44': [{'pid': '213', 'price': 19.00, 'name': '22 💎'}, {'pid': '213', 'price': 19.00, 'name': '22 💎'}],
    '56': [{'pid': '214', 'price': 47.50, 'name': '56 💎'}],
    '112': [{'pid': '215', 'price': 95.00, 'name': '112 💎'}],
    '223': [{'pid': '216', 'price': 190.00, 'name': '223 💎'}],
    '336': [{'pid': '217', 'price': 285.00, 'name': '336 💎'}],
    '570': [{'pid': '218', 'price': 475.00, 'name': '570 💎'}],
    '1163': [{'pid': '219', 'price': 950.00, 'name': '1163 💎'}],
    '2398': [{'pid': '220', 'price': 1900.00, 'name': '2398 💎'}],
    '6042': [{'pid': '221', 'price': 4750.00, 'name': '6042 💎'}],
    'tp': [{'pid': '214', 'price': 475.00, 'name': 'twilight pass 💎'}],
    'wp': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'}],
    'wp2': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(2)],
    'wp3': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(3)],
    'wp4': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(4)],
    'wp5': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(5)],
    'wp6': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(6)],
    'wp7': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(7)],
    'wp8': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(8)],
    'wp9': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(9)],
    'wp10': [{'pid': '16641', 'price': 95.00, 'name': 'Weekly Pass'} for _ in range(10)]
}

MCC_PACKAGES = {
    '86': [{'pid': '23825', 'price': 62.5, 'name': '86 💎'}],
    '172': [{'pid': '23826', 'price': 125.0, 'name': '172 💎'}],
    '257': [{'pid': '23827', 'price': 187.0, 'name': '257 💎'}],
    '343': [{'pid': '23828', 'price': 250.0, 'name': '343 💎'}],
    '429': [{'pid': '23826', 'price': 122.0, 'name': '172 💎'}, {'pid': '23827', 'price': 187.0, 'name': '257 💎'}],
    '516': [{'pid': '23829', 'price': 375.0, 'name': '516 💎'}],
    '600': [{'pid': '23825', 'price': 62.5, 'name': '86 💎'}, {'pid': '23827', 'price': 187.0, 'name': '257 💎'}, {'pid': '23827', 'price': 177.5, 'name': '257 💎'}],
    '706': [{'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '878': [{'pid': '23826', 'price': 125.0, 'name': '172 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '963': [{'pid': '23827', 'price': 187.0, 'name': '257 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '1049': [{'pid': '23825', 'price': 62.5, 'name': '86 💎'}, {'pid': '23827', 'price': 187.0, 'name': '257 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '1135': [{'pid': '23826', 'price': 125.0, 'name': '172 💎'}, {'pid': '23827', 'price': 187.0, 'name': '257 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '1346': [{'pid': '23831', 'price': 937.5, 'name': '1346 💎'}],
    '1412': [{'pid': '23830', 'price': 500.0, 'name': '706 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '1584': [{'pid': '23826', 'price': 125.0, 'name': '172 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}, {'pid': '23830', 'price': 480.0, 'name': '706 💎'}],
    '1755': [{'pid': '23825', 'price': 62.5, 'name': '86 💎'}, {'pid': '23827', 'price': 187.0, 'name': '257 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '1825': [{'pid': '23832', 'price': 1250.0, 'name': '1825 💎'}],
    '2195': [{'pid': '23833', 'price': 1500.0, 'name': '2195 💎'}],
    '2538': [{'pid': '23825', 'price': 62.5, 'name': '86 💎'}, {'pid': '23827', 'price': 187.0, 'name': '257 💎'}, {'pid': '23833', 'price': 1500.0, 'name': '2195 💎'}],
    '2901': [{'pid': '23833', 'price': 1500.0, 'name': '2195 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}],
    '3244': [{'pid': '23825', 'price': 62.5, 'name': '86 💎'}, {'pid': '23827', 'price': 187.0, 'name': '257 💎'}, {'pid': '23830', 'price': 500.0, 'name': '706 💎'}, {'pid': '23833', 'price': 1500.0, 'name': '2195 💎'}],
    '3688': [{'pid': '23834', 'price': 2500.0, 'name': '3688 💎'}],
    '5532': [{'pid': '23835', 'price': 3750.0, 'name': '5532 💎'}],
    '9288': [{'pid': '23836', 'price': 6250.0, 'name': '9288 💎'}],
    'b150': [{'pid': '23838', 'price': 120.0, 'name': '150+150 💎'}],
    'b250': [{'pid': '23839', 'price': 200.0, 'name': '250+250 💎'}],
    'b50': [{'pid': '23837', 'price': 40.0, 'name': '50+50 💎'}],
    'b500': [{'pid': '23840', 'price': 400.0, 'name': '500+500 💎'}],
    'wp': [{'pid': '23841', 'price': 99.90, 'name': 'Weekly Pass'}],
}

PH_MCC_PACKAGES = {
    '5': [{'pid': '23906', 'price': 4.75, 'name': '5 💎'}],
    '11': [{'pid': '23907', 'price': 9.03, 'name': '11 💎'}],
    '22': [{'pid': '23908', 'price': 18.05, 'name': '22 💎'}],
    '56': [{'pid': '23909', 'price': 45.13, 'name': '56 💎'}],
    '112': [{'pid': '23910', 'price': 90.25, 'name': '112 💎'}],
    '223': [{'pid': '23911', 'price': 180.50, 'name': '223 💎'}],
    '339': [{'pid': '23912', 'price': 270.75, 'name': '339 💎'}],
    '570': [{'pid': '23913', 'price': 451.25, 'name': '578 💎'}],
    '1163': [{'pid': '23914', 'price': 902.50, 'name': '1163 💎'}],
    '2398': [{'pid': '23915', 'price': 1805.00, 'name': '2398 💎'}],
    '6042': [{'pid': '23916', 'price': 4512.50, 'name': '6042 💎'}],
    'wp': [{'pid': '23922', 'price': 95.00, 'name': 'wp 💎'}],
    'lukas': [{'pid': '25600', 'price': 47.45, 'name': 'lukas battle bounty💎'}],
    'battlefordiscounts': [{'pid': '25601', 'price': 47.45, 'name': 'battlefordiscounts 💎'}],
}

# ==========================================
# 3. Helpers Functions
# ==========================================
async def is_authorized(bot_id: int, user_id: int):
    if user_id == OWNER_ID:
        return True
    user = await db.get_reseller(bot_id, str(user_id))
    if user is not None:
        return True
    return False

async def notify_owner(text: str):
    try: 
        await bot.send_message(chat_id=OWNER_ID, text=text, parse_mode=ParseMode.HTML)
    except Exception as e: 
        print(f" Owner ထံသို့ Message ပို့၍မရပါ: {e}")



def generate_list(packages_dict):
    """Dictionary ထဲမှ Package များနှင့် ဈေးနှုန်းများကို သပ်ရပ်စွာ စာရင်းထုတ်ပေးရန်"""
    text = ""
    for key, items in packages_dict.items():
        total_price = sum(item['price'] for item in items)
        price_str = f"{total_price:.1f}" if (total_price * 10) % 10 == 0 else f"{total_price:g}"
        
        if key.isdigit():
            display_name = f"{key} Diamond"
        else:
            display_name = key.upper()

        text += f"{display_name:<16} - $ {price_str}\n"
    return text.strip()

# ==========================================
# 4. Scraper Logic
# ==========================================
async def get_bot_scraper(bot_id: int):
    global GLOBAL_SCRAPERS, GLOBAL_COOKIES, GLOBAL_CSRF
    
    raw_cookie = await db.get_bot_cookie(bot_id) or ""
    
    if bot_id not in GLOBAL_SCRAPERS or raw_cookie != GLOBAL_COOKIES.get(bot_id):
        cookie_dict = {}
        if raw_cookie:
            for item in raw_cookie.split(';'):
                if '=' in item:
                    k, v = item.strip().split('=', 1)
                    cookie_dict[k.strip()] = v.strip()
                    
        # ❌ Proxy များကို ဖြုတ်ချလိုက်ပါပြီ
        GLOBAL_SCRAPERS[bot_id] = AsyncSession(
            impersonate="chrome124", 
            cookies=cookie_dict
            # proxies=proxy_dict ကို ဖယ်ရှားလိုက်ပါသည်
        )
        GLOBAL_COOKIES[bot_id] = raw_cookie
        GLOBAL_CSRF[bot_id] = {'mlbb_br': None, 'mlbb_ph': None, 'mcc_br': None, 'mcc_ph': None}
        
    return GLOBAL_SCRAPERS[bot_id]

def _sync_drission_login(email, password):
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-setuid-sandbox')
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_user_agent("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36")
        co.headless(True) 

        page = ChromiumPage(co)
        page.get("https://www.smile.one/customer/login")
        page.wait(5)
        
        sign_in_btn = page.ele('text=Sign in with Google')
        if sign_in_btn: sign_in_btn.click()
        
        page.wait.new_tab()
        google_tab = page.get_tab(page.latest_tab)
        
        google_tab.wait(2)
        google_tab.ele('input[type="email"]').input(email)
        google_tab.wait(1)
        google_tab.ele('input[type="email"]').type('\n') 
        
        google_tab.wait(4)
        google_tab.ele('input[type="password"]').input(password)
        google_tab.wait(1)
        google_tab.ele('input[type="password"]').type('\n') 
        
        page.wait.url_change("customer/order", timeout=30)
        
        cookies_dict = page.cookies(as_dict=True)
        raw_cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
        
        page.quit()
        return raw_cookie_str
    except Exception as e:
        print(f"DrissionPage Login Error: {e}")
        try: page.quit()
        except: pass
        return None

async def auto_login_and_get_cookie(bot_id: int):
    global last_login_time, GLOBAL_SCRAPERS, GLOBAL_CSRF
    if not GOOGLE_EMAIL or not GOOGLE_PASS:
        print("❌ GOOGLE_EMAIL and GOOGLE_PASS are missing in .env.")
        return False
        
    async with auth_lock:
        if time.time() - last_login_time < 120:
            return True

        print(f"Logging in with Google to fetch new Cookie for Bot ID {bot_id} using DrissionPage...")
        loop = asyncio.get_running_loop()
        new_cookie_str = await loop.run_in_executor(None, _sync_drission_login, GOOGLE_EMAIL, GOOGLE_PASS)
        
        if new_cookie_str:
            print("✅ Auto-Login (Google) successful. Saving Cookie...")
            await db.update_bot_cookie(bot_id, new_cookie_str)
            last_login_time = time.time()
            GLOBAL_SCRAPERS.pop(bot_id, None)
            GLOBAL_CSRF.pop(bot_id, None)
            return True
        else:
            print("❌ Did not reach the Order page. (Google blocked or Checkpoint)")
            return False

async def get_smile_balance(scraper, headers, balance_url='https://www.smile.one/customer/order'):
    balances = {'br_balance': 0.00, 'ph_balance': 0.00}
    try:
        response = await scraper.get(balance_url, headers=headers, timeout=15)
        
        br_match = re.search(r'(?i)(?:Balance|Saldo)[\s:]*?<\/p>\s*<p>\s*([\d\.,]+)', response.text)
        if br_match:
            balances['br_balance'] = float(br_match.group(1).replace(',', ''))
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            main_balance_div = soup.find('div', class_='balance-coins')
            if main_balance_div:
                p_tags = main_balance_div.find_all('p')
                if len(p_tags) >= 2: 
                    balances['br_balance'] = float(p_tags[1].text.strip().replace(',', ''))
                    
        ph_match = re.search(r'(?i)Saldo PH[\s:]*?<\/span>\s*<span>\s*([\d\.,]+)', response.text)
        if ph_match:
            balances['ph_balance'] = float(ph_match.group(1).replace(',', ''))
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            ph_balance_container = soup.find('div', id='all-balance')
            if ph_balance_container:
                span_tags = ph_balance_container.find_all('span')
                if len(span_tags) >= 2:
                    balances['ph_balance'] = float(span_tags[1].text.strip().replace(',', ''))
    except Exception as e: 
        print(f"Error fetching balance from site: {e}")
    return balances

async def process_smile_one_order_br(bot_id, game_id, zone_id, product_id, currency_name="BR", prev_context=None, skip_role_check=False, known_ig_name="Unknown", last_success_order_id=""):
    scraper = await get_bot_scraper(bot_id)
    global GLOBAL_CSRF
    cache_key = "mlbb_br"

    main_url = 'https://www.smile.one/merchant/mobilelegends'
    checkrole_url = 'https://www.smile.one/merchant/mobilelegends/checkrole'
    query_url = 'https://www.smile.one/merchant/mobilelegends/query'
    pay_url = 'https://www.smile.one/merchant/mobilelegends/pay'
    order_api_url = 'https://www.smile.one/customer/activationcode/codelist'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest', 
        'Referer': main_url, 
        'Origin': 'https://www.smile.one'
    }

    try:
        bot_csrf_dict = GLOBAL_CSRF.setdefault(bot_id, {})
        csrf_token = prev_context.get('csrf_token') if prev_context else bot_csrf_dict.get(cache_key)
        ig_name = known_ig_name

        if not csrf_token:
            response = await scraper.get(main_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_tag = soup.find('meta', {'name': 'csrf-token'})
            
            if meta_tag:
                csrf_token = meta_tag.get('content')
            elif soup.find('input', {'name': '_csrf'}):
                csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
            else:
                csrf_token = None
                
            if not csrf_token:
                return {"status": "error", "message": "CSRF Token not found. Re-add Cookie.", "ig_name": ig_name}
                
            bot_csrf_dict[cache_key] = csrf_token

        async def get_flow_id():
            query_data = {
                'user_id': game_id,
                'zone_id': zone_id, 
                'pid': product_id, 
                'checkrole': '', 
                'pay_methond': 'smilecoin', 
                'channel_method': 'smilecoin', 
                '_csrf': csrf_token
            }
            return await scraper.post(query_url, data=query_data, headers=headers)

        async def check_role():
            check_data = {
                'user_id': game_id, 
                'zone_id': zone_id, 
                '_csrf': csrf_token
            }
            return await scraper.post(checkrole_url, data=check_data, headers=headers)

        if skip_role_check:
            query_response_raw = await get_flow_id()
        else:
            query_response_raw, role_response_raw = await asyncio.gather(get_flow_id(), check_role())
            try:
                role_result = role_response_raw.json()
                fetched_name = role_result.get('username') or role_result.get('data', {}).get('username')
                if fetched_name and str(fetched_name).strip() != "":
                    ig_name = str(fetched_name).strip()
                else:
                    return {"status": "error", "message": "❌ Invalid Account: Account not found.", "ig_name": "Unknown"}
            except Exception: 
                return {"status": "error", "message": "Check Role API Error.", "ig_name": ig_name}

        try:
            query_result = query_response_raw.json()
        except Exception:
            return {"status": "error", "message": "Query API Error", "ig_name": ig_name}
            
        flowid = query_result.get('flowid') or query_result.get('data', {}).get('flowid')
        
        if not flowid:
            real_error = query_result.get('msg') or query_result.get('message') or query_result.get('info') or ""
            if "login" in str(real_error).lower() or "unauthorized" in str(real_error).lower():
                bot_csrf_dict[cache_key] = None
                if bot_id == bot.id: await notify_owner("⚠️ <b>Order Alert:</b> Cookie expired. Auto-login started...")
                success = await auto_login_and_get_cookie(bot_id)
                if success: return {"status": "error", "message": "Session renewed. Please try again.", "ig_name": ig_name}
                else: return {"status": "error", "message": "❌ Auto-Login failed. Please /setcookie.", "ig_name": ig_name}
            return {"status": "error", "message": str(real_error), "ig_name": ig_name}

        pay_data = {
            '_csrf': csrf_token, 'user_id': game_id, 'zone_id': zone_id, 'pay_methond': 'smilecoin', 
            'product_id': product_id, 'channel_method': 'smilecoin', 'flowid': flowid, 'email': '', 'coupon_id': ''
        }
        pay_response_raw = await scraper.post(pay_url, data=pay_data, headers=headers)
        pay_text = pay_response_raw.text.lower()
        
        if "saldo insuficiente" in pay_text or "insufficient" in pay_text:
            return {"status": "error", "message": "Insufficient Balance.", "ig_name": ig_name}
        
        real_order_id = "Not found"
        is_success = False
        actual_product_name = ""

        try:
            pay_json = pay_response_raw.json()
            status_val = str(pay_json.get('status', ''))
            code = str(pay_json.get('code', status_val))
            msg = str(pay_json.get('msg') or pay_json.get('message') or pay_json.get('info') or "").lower()
            
            if code in ['200', '0', '1'] or 'success' in msg: 
                is_success = True
                _id = str(pay_json.get('data', {}).get('order_id') or pay_json.get('order_id') or pay_json.get('increment_id') or "")
                if not _id or _id == "None": _id = f"FAST_{int(time.time())}_{random.randint(100,999)}"
                real_order_id = _id
        except:
            if 'success' in pay_text or 'sucesso' in pay_text: 
                is_success = True
                real_order_id = f"FAST_{int(time.time())}_{random.randint(100,999)}"

        if not is_success:
            try:
                hist_res_raw = await scraper.get(order_api_url, params={'type': 'orderlist', 'p': '1', 'pageSize': '5'}, headers=headers)
                hist_json = hist_res_raw.json()
                if 'list' in hist_json and len(hist_json['list']) > 0:
                    for order in hist_json['list']:
                        if str(order.get('user_id')) == str(game_id) and str(order.get('server_id')) == str(zone_id):
                            current_order_id = str(order.get('increment_id', ""))
                            if current_order_id != last_success_order_id:
                                if str(order.get('order_status', '')).lower() in ['success', '1'] or str(order.get('status')) == '1':
                                    real_order_id = current_order_id
                                    actual_product_name = str(order.get('product_name', ''))
                                    is_success = True
                                    break
            except: pass

        if is_success:
            return {"status": "success", "ig_name": ig_name, "order_id": real_order_id, "csrf_token": csrf_token, "product_name": actual_product_name}
        else:
            error_detail = pay_json.get('msg') or pay_json.get('message') or pay_json.get('info') if 'pay_json' in locals() else "Payment Verification Failed."
            return {"status": "error", "message": str(error_detail), "ig_name": ig_name}
    except Exception as e: 
        return {"status": "error", "message": f"System Error: {str(e)}", "ig_name": known_ig_name}

async def process_smile_one_order_ph(bot_id, game_id, zone_id, product_id, currency_name="PH", prev_context=None, skip_role_check=False, known_ig_name="Unknown", last_success_order_id=""):
    scraper = await get_bot_scraper(bot_id)
    global GLOBAL_CSRF
    cache_key = "mlbb_ph"

    main_url = 'https://www.smile.one/ph/merchant/mobilelegends'
    checkrole_url = 'https://www.smile.one/ph/merchant/mobilelegends/checkrole'
    query_url = 'https://www.smile.one/ph/merchant/mobilelegends/query'
    pay_url = 'https://www.smile.one/ph/merchant/mobilelegends/pay'
    order_api_url = 'https://www.smile.one/ph/customer/activationcode/codelist'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest', 'Referer': main_url, 'Origin': 'https://www.smile.one'
    }

    try:
        bot_csrf_dict = GLOBAL_CSRF.setdefault(bot_id, {})
        csrf_token = prev_context.get('csrf_token') if prev_context else bot_csrf_dict.get(cache_key)
        ig_name = known_ig_name

        if not csrf_token:
            response = await scraper.get(main_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_tag = soup.find('meta', {'name': 'csrf-token'})
            if meta_tag: csrf_token = meta_tag.get('content')
            elif soup.find('input', {'name': '_csrf'}): csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
            else: csrf_token = None
            if not csrf_token: return {"status": "error", "message": "CSRF Token not found. Re-add Cookie.", "ig_name": ig_name}
            bot_csrf_dict[cache_key] = csrf_token

        async def get_flow_id():
            query_data = {
                'user_id': game_id, 'zone_id': zone_id, 'pid': product_id, 'checkrole': '', 
                'pay_methond': 'smilecoin', 'channel_method': 'smilecoin', '_csrf': csrf_token
            }
            return await scraper.post(query_url, data=query_data, headers=headers)

        async def check_role():
            check_data = {'user_id': game_id, 'zone_id': zone_id, '_csrf': csrf_token}
            return await scraper.post(checkrole_url, data=check_data, headers=headers)

        if skip_role_check:
            query_response_raw = await get_flow_id()
        else:
            query_response_raw, role_response_raw = await asyncio.gather(get_flow_id(), check_role())
            try:
                role_result = role_response_raw.json()
                fetched_name = role_result.get('username') or role_result.get('data', {}).get('username')
                if fetched_name and str(fetched_name).strip() != "": ig_name = str(fetched_name).strip()
                else: return {"status": "error", "message": "❌ Invalid Account: Account not found.", "ig_name": "Unknown"}
            except Exception: return {"status": "error", "message": "Check Role API Error.", "ig_name": ig_name}

        try: query_result = query_response_raw.json()
        except Exception: return {"status": "error", "message": "Query API Error", "ig_name": ig_name}
            
        flowid = query_result.get('flowid') or query_result.get('data', {}).get('flowid')
        if not flowid:
            real_error = query_result.get('msg') or query_result.get('message') or query_result.get('info') or ""
            if "login" in str(real_error).lower() or "unauthorized" in str(real_error).lower():
                bot_csrf_dict[cache_key] = None
                if bot_id == bot.id: await notify_owner("⚠️ <b>Order Alert:</b> Cookie expired. Auto-login started...")
                success = await auto_login_and_get_cookie(bot_id)
                if success: return {"status": "error", "message": "Session renewed. Please try again.", "ig_name": ig_name}
                else: return {"status": "error", "message": "❌ Auto-Login failed. Please /setcookie.", "ig_name": ig_name}
            return {"status": "error", "message": str(real_error), "ig_name": ig_name}

        pay_data = {
            '_csrf': csrf_token, 'user_id': game_id, 'zone_id': zone_id, 'pay_methond': 'smilecoin', 
            'product_id': product_id, 'channel_method': 'smilecoin', 'flowid': flowid, 'email': '', 'coupon_id': ''
        }
        pay_response_raw = await scraper.post(pay_url, data=pay_data, headers=headers)
        pay_text = pay_response_raw.text.lower()
        
        if "saldo insuficiente" in pay_text or "insufficient" in pay_text:
            return {"status": "error", "message": "Insufficient Balance.", "ig_name": ig_name}
        
        real_order_id = "Not found"
        is_success = False
        actual_product_name = ""

        try:
            pay_json = pay_response_raw.json()
            status_val = str(pay_json.get('status', ''))
            code = str(pay_json.get('code', status_val))
            msg = str(pay_json.get('msg') or pay_json.get('message') or pay_json.get('info') or "").lower()
            if code in ['200', '0', '1'] or 'success' in msg: 
                is_success = True
                _id = str(pay_json.get('data', {}).get('order_id') or pay_json.get('order_id') or pay_json.get('increment_id') or "")
                if not _id or _id == "None": _id = f"FAST_{int(time.time())}_{random.randint(100,999)}"
                real_order_id = _id
        except:
            if 'success' in pay_text or 'sucesso' in pay_text: 
                is_success = True
                real_order_id = f"FAST_{int(time.time())}_{random.randint(100,999)}"

        if not is_success:
            try:
                hist_res_raw = await scraper.get(order_api_url, params={'type': 'orderlist', 'p': '1', 'pageSize': '5'}, headers=headers)
                hist_json = hist_res_raw.json()
                if 'list' in hist_json and len(hist_json['list']) > 0:
                    for order in hist_json['list']:
                        if str(order.get('user_id')) == str(game_id) and str(order.get('server_id')) == str(zone_id):
                            current_order_id = str(order.get('increment_id', ""))
                            if current_order_id != last_success_order_id:
                                if str(order.get('order_status', '')).lower() in ['success', '1'] or str(order.get('status')) == '1':
                                    real_order_id = current_order_id
                                    actual_product_name = str(order.get('product_name', ''))
                                    is_success = True
                                    break
            except: pass

        if is_success:
            return {"status": "success", "ig_name": ig_name, "order_id": real_order_id, "csrf_token": csrf_token, "product_name": actual_product_name}
        else:
            error_detail = pay_json.get('msg') or pay_json.get('message') or pay_json.get('info') if 'pay_json' in locals() else "Payment Verification Failed."
            return {"status": "error", "message": str(error_detail), "ig_name": ig_name}

    except Exception as e: 
        return {"status": "error", "message": f"System Error: {str(e)}", "ig_name": known_ig_name}

async def process_mcc_order(bot_id, game_id, zone_id, product_id, currency_name, prev_context=None, skip_role_check=False, known_ig_name="Unknown", last_success_order_id=""):
    scraper = await get_bot_scraper(bot_id)
    global GLOBAL_CSRF
    cache_key = f"mcc_{currency_name.lower()}"

    if currency_name == 'PH':
        main_url = 'https://www.smile.one/ph/merchant/game/magicchessgogo'
        checkrole_url = 'https://www.smile.one/ph/merchant/game/checkrole'
        query_url = 'https://www.smile.one/ph/merchant/game/createorder' 
        pay_url = 'https://www.smile.one/ph/merchant/game/pay' 
        order_api_url = 'https://www.smile.one/ph/customer/activationcode/codelist'
    else:
        main_url = 'https://www.smile.one/br/merchant/game/magicchessgogo'
        checkrole_url = 'https://www.smile.one/br/merchant/game/checkrole'
        query_url = 'https://www.smile.one/br/merchant/game/createorder' 
        pay_url = 'https://www.smile.one/br/merchant/game/pay'
        order_api_url = 'https://www.smile.one/br/customer/activationcode/codelist'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest', 'Referer': main_url, 'Origin': 'https://www.smile.one'
    }

    try:
        bot_csrf_dict = GLOBAL_CSRF.setdefault(bot_id, {})
        csrf_token = prev_context.get('csrf_token') if prev_context else bot_csrf_dict.get(cache_key)
        ig_name = known_ig_name
        
        if not csrf_token:
            response = await scraper.get(main_url, headers=headers)
            if response.status_code in [403, 503] or "cloudflare" in response.text.lower():
                 return {"status": "error", "message": "Blocked by Cloudflare.", "ig_name": ig_name}

            soup = BeautifulSoup(response.text, 'html.parser')
            meta_tag = soup.find('meta', {'name': 'csrf-token'})
            if meta_tag: csrf_token = meta_tag.get('content')
            elif soup.find('input', {'name': '_csrf'}): csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
            else: csrf_token = None
            if not csrf_token: return {"status": "error", "message": "CSRF Token not found. Add a new Cookie using /setcookie.", "ig_name": ig_name}
            bot_csrf_dict[cache_key] = csrf_token

        async def get_flow_id():
            query_data = {'uid': game_id, 'sid': zone_id, 'productid': product_id, 'channel_method': 'smilecoin', 'external': 'false', '_csrf': csrf_token}
            return await scraper.post(query_url, params={'product': 'magicchessgogo'}, data=query_data, headers=headers)

        async def check_role():
            check_data = {'uid': game_id, 'sid': zone_id, 'checkrole': '1', 'product': 'magicchessgogo', '_csrf': csrf_token}
            return await scraper.post(checkrole_url, params={'product': 'magicchessgogo'}, data=check_data, headers=headers)

        if skip_role_check:
            query_response_raw = await get_flow_id()
        else:
            query_response_raw, role_response_raw = await asyncio.gather(get_flow_id(), check_role())
            try:
                role_result = role_response_raw.json()
                fetched_name = role_result.get('nickname') or role_result.get('username') or role_result.get('role_name') or role_result.get('data', {}).get('nickname') or role_result.get('data', {}).get('username')
                if fetched_name and str(fetched_name).strip() != "": ig_name = str(fetched_name).strip()
                else: ig_name = "Unknown" 
            except Exception: ig_name = "Unknown"

        try: query_result = query_response_raw.json()
        except Exception: return {"status": "error", "message": "Query API Error: Failed to load JSON.", "ig_name": ig_name}
            
        flowid = query_result.get('flowid') or query_result.get('data', {}).get('flowid')
        if not flowid:
            real_error = query_result.get('msg') or query_result.get('message') or query_result.get('info') or ""
            if "login" in str(real_error).lower() or "unauthorized" in str(real_error).lower():
                bot_csrf_dict[cache_key] = None
                if bot_id == bot.id: await notify_owner("⚠️ <b>Order Alert:</b> Cookie expired. Auto-login started...")
                success = await auto_login_and_get_cookie(bot_id)
                if success: return {"status": "error", "message": "Session renewed. Please enter the command again.", "ig_name": ig_name}
                else: return {"status": "error", "message": "❌ Auto-Login failed. Please provide /setcookie.", "ig_name": ig_name}
            error_display = str(real_error) if real_error else "Invalid account or unable to purchase."
            return {"status": "error", "message": error_display, "ig_name": ig_name}

        pay_data = {
            '_csrf': csrf_token, 'uid': game_id, 'sid': zone_id, 'email': '', 'pay_methond': 'smilecoin', 'channel_method': 'smilecoin',
            'flowid': flowid, 'pay_country': '', 'coupon_id': '', 'zipcode': '', 'product': 'magicchessgogo', 'productid': product_id, 'external': 'false'
        }
        
        pay_headers = headers.copy()
        if 'X-Requested-With' in pay_headers: del pay_headers['X-Requested-With'] 
        pay_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'

        pay_response_raw = await scraper.post(pay_url, data=pay_data, headers=pay_headers, allow_redirects=False)
        
        status_code = pay_response_raw.status_code
        location = str(pay_response_raw.headers.get('Location') or pay_response_raw.headers.get('location') or "")
        pay_text = pay_response_raw.text.strip().lower()
        
        if "saldo insuficiente" in pay_text or "insufficient" in pay_text:
            return {"status": "error", "message": "Insufficient Balance.", "ig_name": ig_name}
        
        real_order_id = "Not found"
        is_success = False
        actual_product_name = ""

        if status_code in [301, 302, 303]:
            if "customer/order" in location or "success" in location or "pay" in location:
                is_success = True
                real_order_id = f"FAST_{int(time.time())}_{random.randint(100,999)}"
        
        if not is_success and pay_text:
            try:
                pay_json = pay_response_raw.json()
                code = str(pay_json.get('code', pay_json.get('status', '')))
                msg = str(pay_json.get('msg') or pay_json.get('message') or pay_json.get('info') or "").lower()
                if code in ['200', '0', '1'] or 'success' in msg: 
                    is_success = True
                    _id = str(pay_json.get('data', {}).get('order_id') or pay_json.get('order_id') or pay_json.get('increment_id') or "")
                    if not _id or _id == "None": _id = f"FAST_{int(time.time())}_{random.randint(100,999)}"
                    real_order_id = _id
            except:
                if 'success' in pay_text or 'sucesso' in pay_text: 
                    is_success = True
                    real_order_id = f"FAST_{int(time.time())}_{random.randint(100,999)}"

        if not is_success:
            try:
                hist_res_raw = await scraper.get(order_api_url, params={'type': 'orderlist', 'p': '1', 'pageSize': '5'}, headers=headers)
                hist_json = hist_res_raw.json()
                if 'list' in hist_json and len(hist_json['list']) > 0:
                    for order in hist_json['list']:
                        uid_val = str(order.get('user_id') or order.get('uid') or "")
                        sid_val = str(order.get('server_id') or order.get('sid') or order.get('zone_id') or "")
                        if uid_val == str(game_id) and sid_val == str(zone_id):
                            current_order_id = str(order.get('increment_id', ""))
                            if current_order_id != last_success_order_id:
                                if str(order.get('order_status', '')).lower() in ['success', '1'] or str(order.get('status')) == '1':
                                    real_order_id = current_order_id
                                    actual_product_name = str(order.get('product_name', ''))
                                    is_success = True
                                    break
            except Exception: pass

        if is_success:
            return {"status": "success", "ig_name": ig_name, "order_id": real_order_id, "csrf_token": csrf_token, "product_name": actual_product_name}
        else:
            if status_code in [301, 302, 303]:
                error_detail = "Payment Rejected by Server (Invalid Item or Region Mismatch)"
                if "error" in location:
                    try:
                        err_url = location if location.startswith('http') else f"https://www.smile.one{location}"
                        err_res = await scraper.get(err_url, headers=headers)
                        err_soup = BeautifulSoup(err_res.text, 'html.parser')
                        msg_box = err_soup.find(class_=re.compile('msg|error-message', re.I))
                        if msg_box: error_detail = f"Declined: {msg_box.text.strip()}"
                    except: pass
            elif not pay_text: error_detail = f"Empty Response (HTTP {status_code})"
            else: error_detail = f"Reply: {pay_text[:80]}..."
            return {"status": "error", "message": error_detail, "ig_name": ig_name}
    except Exception as e: 
        return {"status": "error", "message": f"System Error: {str(e)}", "ig_name": known_ig_name}

# ==========================================
# 5. Message Handlers
# ==========================================
async def execute_buy_process(bot_id, message, lines, regex_pattern, currency, packages_dict, process_func, title_prefix, is_mcc=False):
    tg_id = str(message.from_user.id)
    telegram_user = message.from_user.username
    display_uname = telegram_user if telegram_user else (message.from_user.first_name or str(tg_id))
        
    async with user_locks[tg_id]: 
        parsed_orders = []
        for line in lines:
            line = line.strip()
            if not line: continue 
            
            match = re.search(regex_pattern, line)
            if not match:
                await message.reply(f"Invalid format: `{line}`\nCheck /help for correct format.", link_preview_options=types.LinkPreviewOptions(is_disabled=True))
                continue
                
            game_id = match.group(1)
            zone_id = match.group(2)
            raw_items_str = match.group(3).lower()
            
            requested_packages = raw_items_str.split()
            packages_to_buy = []
            not_found_pkgs = []
            
            for pkg in requested_packages:
                active_packages = None
                if isinstance(packages_dict, list):
                    for p_dict in packages_dict:
                        if pkg in p_dict: 
                            active_packages = p_dict
                            break
                else:
                    if pkg in packages_dict: active_packages = packages_dict
                        
                if active_packages: 
                    pkg_items = []
                    for item_dict in active_packages[pkg]:
                        new_item = item_dict.copy()
                        new_item['pkg_name'] = pkg.upper() 
                        pkg_items.append(new_item)
                    packages_to_buy.append({'pkg_name': pkg.upper(), 'items': pkg_items})
                else: not_found_pkgs.append(pkg)
                    
            if not_found_pkgs:
                await message.reply(f"❌ Package(s) not found for ID {game_id}: {', '.join(not_found_pkgs)}", link_preview_options=types.LinkPreviewOptions(is_disabled=True))
                continue
                
            if not packages_to_buy: continue
                
            line_price = sum(item['price'] for p in packages_to_buy for item in p['items'])
            parsed_orders.append({'game_id': game_id, 'zone_id': zone_id, 'raw_items_str': raw_items_str, 'packages_to_buy': packages_to_buy, 'line_price': line_price})
            
        if not parsed_orders: return
            
        start_time = time.time()
        loading_icon = "<tg-emoji emoji-id='5895403643863043222'>🫧</tg-emoji>"
        loading_msg = await message.reply(f"{loading_icon}", link_preview_options=types.LinkPreviewOptions(is_disabled=True))

        scraper = await get_bot_scraper(bot_id)
        headers = {'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://www.smile.one'}
        
        is_clone = (bot_id != bot.id)
        
        try:
            if is_clone:
                v_wallet = await db.get_clone_wallet(bot_id)
                initial_bal_for_receipt = v_wallet['br_balance'] if currency == 'BR' else v_wallet['ph_balance']
            else:
                bals_before = await get_smile_balance(scraper, headers)
                initial_bal_for_receipt = bals_before['br_balance'] if currency == 'BR' else bals_before['ph_balance']
        except:
            initial_bal_for_receipt = 0.0

        total_required_amount = sum(order['line_price'] for order in parsed_orders)
        
        if initial_bal_for_receipt < total_required_amount:
            await loading_msg.delete()
            needed_amount = total_required_amount - initial_bal_for_receipt
            flag = f"<tg-emoji emoji-id='{BR_EMOJI}'>🇧🇷</tg-emoji>" if currency == 'BR' else f"<tg-emoji emoji-id='{PH_EMOJI}'>🇵🇭</tg-emoji>"
            error_msg = (
                f"✖ <b>ɪηꜱᴜꜰꜰɪᴄɪᴇηᴛ ʙᴀʟᴀɴᴄᴇ</b>\n\n"
                f"{flag} <b><code>ᴄᴏꜱᴛ : {total_required_amount:,.2f} 🪙</code></b>\n"
                f"{flag} <b><code>ɴᴇᴇᴅ : {needed_amount:,.2f} 🪙</code></b>\n"
                f"<code>━━━━━━━━━━━━━━━━━━</code>"
            )
            return await message.reply(error_msg, parse_mode=ParseMode.HTML)

        current_official_bal = [initial_bal_for_receipt] 

        async def process_order_line(order):
            game_id = order['game_id']
            zone_id = order.get('order_zone', order['zone_id'])
            raw_items_str = order['raw_items_str']
            packages_to_buy = order['packages_to_buy']
            
            overall_success_count = 0
            overall_fail_count = 0
            total_spent = 0.0
            ig_name = "Unknown"
            package_results = []

            async with api_semaphore:
                prev_context = None
                last_success_order = ""
                
                for pkg_data in packages_to_buy:
                    pkg_name = pkg_data['pkg_name']
                    items = pkg_data['items']
                    
                    pkg_success_count = 0
                    pkg_fail_count = 0
                    pkg_spent = 0.0
                    pkg_order_ids = ""
                    pkg_error = ""
                    
                    pkg_total_price = sum(item['price'] for item in items)
                    
                    if current_official_bal[0] < pkg_total_price:
                        pkg_fail_count = len(items)
                        pkg_error = "Insufficient Balance"
                        overall_fail_count += 1
                        package_results.append({'pkg_name': pkg_name, 'status': 'fail', 'spent': 0.0, 'order_ids': "", 'error_msg': pkg_error, 'ig_name': ig_name})
                        continue

                    for item in items:
                        if current_official_bal[0] < item['price']:
                            pkg_fail_count += 1
                            pkg_error = "Insufficient Balance"
                            break

                        current_official_bal[0] -= item['price']
                        skip_check = False
                        res = {}
                        max_retries = 3
                        
                        for attempt in range(max_retries):
                            res = await process_func(bot_id, game_id, zone_id, item['pid'], currency, prev_context=prev_context, skip_role_check=skip_check, known_ig_name=ig_name, last_success_order_id=last_success_order)
                            error_text_check = str(res.get('message', '')).lower()
                            if (res.get('status') == 'success' or "insufficient" in error_text_check or "invalid" in error_text_check or "not found" in error_text_check or "limit" in error_text_check or "exceed" in error_text_check or "máximo" in error_text_check):
                                break
                            if attempt < max_retries - 1:
                                if ("erro no servidor" in error_text_check or "server error" in error_text_check or "cloudflare" in error_text_check or "query failed" in error_text_check): await asyncio.sleep(5.0)
                                else: await asyncio.sleep(2.0)
                                
                        fetched_name = res.get('ig_name') or res.get('username') or res.get('role_name') or res.get('nickname')
                        if fetched_name and str(fetched_name).strip() not in ["", "Unknown", "None"]: ig_name = str(fetched_name).strip()

                        if res.get('status') == 'success':
                            pkg_success_count += 1
                            pkg_spent += item['price']
                            pkg_order_ids += f"{res.get('order_id', '')}\n"
                            prev_context = {'csrf_token': res.get('csrf_token')}
                            last_success_order = res.get('order_id', '')
                            
                            if is_clone:
                                await db.update_clone_wallet(bot_id, currency, -item['price'])
                        else:
                            current_official_bal[0] += item['price'] 
                            pkg_fail_count += 1
                            pkg_error = res.get('message', 'Unknown Error')
                            break 
                            
                    if pkg_success_count > 0:
                        overall_success_count += 1
                        total_spent += pkg_spent
                        display_name = pkg_name
                        if len(items) > 1 and pkg_success_count < len(items):
                            display_name = f"WP{pkg_success_count}" if pkg_name.upper().startswith("WP") else f"{pkg_name} ({pkg_success_count}/{len(items)} Success)"
                        package_results.append({'pkg_name': display_name, 'status': 'success', 'spent': pkg_spent, 'order_ids': pkg_order_ids.strip(), 'error_msg': "", 'ig_name': ig_name})
                        
                    if pkg_fail_count > 0:
                        overall_fail_count += 1
                        display_name = pkg_name
                        if len(items) > 1 and pkg_fail_count < len(items):
                            display_name = f"WP{len(items) - pkg_success_count}" if pkg_name.upper().startswith("WP") else f"{pkg_name} ({len(items) - pkg_success_count} Failed)"
                        package_results.append({'pkg_name': display_name, 'status': 'fail', 'spent': 0.0, 'order_ids': "", 'error_msg': pkg_error, 'ig_name': ig_name})
                        
            return {'game_id': game_id, 'zone_id': zone_id, 'raw_items_str': raw_items_str, 'success_count': overall_success_count, 'fail_count': overall_fail_count, 'total_spent': total_spent, 'ig_name': ig_name, 'package_results': package_results}

        line_tasks = [process_order_line(order) for order in parsed_orders]
        line_results = await asyncio.gather(*line_tasks)
        
        await loading_msg.delete() 
        if not line_results: return
            
        now = datetime.datetime.now(MMT) 
        date_str = now.strftime("%d.%m.%Y-%I:%M%p")

        try:
            if is_clone:
                v_wallet_after = await db.get_clone_wallet(bot_id)
                final_bal_for_receipt = v_wallet_after['br_balance'] if currency == 'BR' else v_wallet_after['ph_balance']
            else:
                await asyncio.sleep(2) 
                anti_cache_url = f"https://www.smile.one/customer/order?_t={int(time.time())}"
                bals_after = await get_smile_balance(scraper, headers, anti_cache_url)
                final_bal_for_receipt = bals_after['br_balance'] if currency == 'BR' else bals_after['ph_balance']
        except:
            final_bal_for_receipt = current_official_bal[0]

        flag = f"<tg-emoji emoji-id='{BR_EMOJI}'>🇧🇷</tg-emoji>" if currency == 'BR' else f"<tg-emoji emoji-id='{PH_EMOJI}'>🇵🇭</tg-emoji>"
        report_icon = "<tg-emoji emoji-id='5895403643863043222'>🟢</tg-emoji>"

        for res in line_results:
            report_lines = []
            report_lines.append(f"{report_icon}<code>TRANSACTION REPORT</code>")
            report_lines.append(f"<code>━━━━━━━━━━━━━━━━━━</code>")

            for pr in res['package_results']:
                safe_ig_name = html.escape(str(pr['ig_name']))
                pkg_display = f"{pr['pkg_name']}" if "WP" in pr['pkg_name'].upper() else f"{pr['pkg_name']} Diamonds"
                
                if pr['status'] == 'success':
                    report_lines.append(f"<code>Status : ✅ Sᴜᴄᴄᴇꜱꜱ</code>")
                    report_lines.append(f"<code>UID    : {res['game_id']} ({res['zone_id']})</code>")
                    report_lines.append(f"<code>Name   : {safe_ig_name}</code>")
                    report_lines.append(f"<code>Order  : {pkg_display}</code>")
                    
                    serials = [sn.strip() for sn in pr['order_ids'].split('\n') if sn.strip()]
                    if serials:
                        report_lines.append(f"<code>Serial : {serials[0]}</code>")
                        for sn in serials[1:]: report_lines.append(f"<code>         {sn}</code>")
                            
                    report_lines.append(f"<code>Spent  : {pr['spent']:.2f} 🪙</code>")
                    final_order_ids = pr['order_ids'].replace('\n', ', ')
                    
                    await db.save_order(tg_id=tg_id, game_id=res['game_id'], zone_id=res['zone_id'], item_name=pr['pkg_name'], price=pr['spent'], order_id=final_order_ids, status="success")
                else:
                    error_text = str(pr['error_msg']).lower()
                    if "insufficient" in error_text or "saldo" in error_text: display_err = "Insufficient Balance"
                    elif "invalid" in error_text or "not found" in error_text: display_err = "Invalid Account"
                    elif "erro no servidor" in error_text or "server error" in error_text: display_err = "Game Server Error"
                    elif "query failed" in error_text: display_err = "Smile.one API error"
                    elif "limit" in error_text or "exceed" in error_text or "máximo" in error_text or "limite" in error_text: display_err = "Weekly Pass Limit Exceeded"
                    elif "zone" in error_text or "region" in error_text or "country" in error_text or "indonesia" in error_text or "support recharge" in error_text or "singapore" in error_text or "russia" in error_text or "philippines" in error_text: display_err = "Ban Server"
                    else: 
                        display_err = pr['error_msg'].replace('❌', '').strip()
                        if not display_err: display_err = "Purchase Failed"
                        if "wp" in pr['pkg_name'].lower():
                            if "unable" in error_text or "fail" in error_text or "error" in error_text: display_err = "Weekly Pass Limit Exceeded"
                                
                    report_lines.append(f"<code>Status : ❌ Fᴀɪʟᴇᴅ</code>")
                    report_lines.append(f"<code>UID    : {res['game_id']} ({res['zone_id']})</code>")
                    report_lines.append(f"<code>Name   : {safe_ig_name}</code>")
                    report_lines.append(f"<code>Order  : {pkg_display}</code>")
                    report_lines.append(f"<code>Error  : {display_err}</code>")
            report_lines.append(f"<code>Date   : {date_str}</code>")
            report_lines.append(f"<code>==== {display_uname} ====</code>")
            report_lines.append(f"{flag}<code>Before : {initial_bal_for_receipt:,.2f}</code>")
            report_lines.append(f"{flag}<code>Spent  : {res['total_spent']:,.2f}</code>")
            report_lines.append(f"{flag}<code>After  : {final_bal_for_receipt:,.2f}</code>")
            report_lines.append("")
            report_lines.append(f"<code>Success {res['success_count']} / Fᴀɪʟᴇᴅ {res['fail_count']}</code>")
            
            final_report = "\n".join(report_lines)
            await message.reply(final_report, parse_mode=ParseMode.HTML, link_preview_options=types.LinkPreviewOptions(is_disabled=True))

@main_router.message(or_f(F.text.regexp(r"^\d{7,}(?:\s+\(?\d+\)?)?\s*.*$"), F.caption.regexp(r"^\d{7,}(?:\s+\(?\d+\)?)?\s*.*$")))
async def format_and_copy_text(message: types.Message):
    raw_text = (message.text or message.caption).strip()
    
    player_id = ""
    zone_id = ""
    suffix = ""
    formatted_raw = raw_text
    
    match_no_bracket = re.match(r"^(\d{7,})\s+(\d+)\s*(.*)$", raw_text)
    match_bracket = re.match(r"^(\d{7,})\s*\((\d+)\)\s*(.*)$", raw_text)
    
    if match_bracket:
        player_id, zone_id, suffix = match_bracket.groups()
    elif match_no_bracket:
        player_id, zone_id, suffix = match_no_bracket.groups()
    
    if player_id and zone_id:
        suffix = suffix.strip()
        processed_suffix = ""
        prefix = ""
        
        if suffix:
            raw_items = suffix.lower().split()
            cleaned_items = []
            
            for item in raw_items:
                wp_match = re.match(r"^(\d*)wp(\d*)$", item)
                if wp_match:
                    num_str = wp_match.group(1) + wp_match.group(2)
                    cleaned_items.append("wp" if num_str in ["", "1"] else f"wp{num_str}")
                else:
                    clean_item = re.sub(r'^(?:dia|dm|d)?(\d+)(?:dia|dm|d)?$', r'\1', item)
                    cleaned_items.append(clean_item)
            
            processed_suffix = " ".join(cleaned_items)
            first_item = cleaned_items[0]
            
            if first_item in BR_PACKAGES or first_item in DOUBLE_DIAMOND_PACKAGES: prefix = "b "
            elif first_item in PH_PACKAGES: prefix = "p "
            elif first_item in MCC_PACKAGES: prefix = "mcc "
            elif first_item in PH_MCC_PACKAGES: prefix = "mcp "

        if processed_suffix: formatted_raw = f"{prefix}{player_id} ({zone_id}) {processed_suffix}"
        else: formatted_raw = f"{player_id} ({zone_id})"
            
    premium_emoji = "<tg-emoji emoji-id='5895403643863043222'>🫧</tg-emoji>" 
    formatted_text = f"{premium_emoji} <code>{formatted_raw}</code>"
    
    try:
        from aiogram.types import CopyTextButton
        copy_btn = InlineKeyboardButton(
            text="ᴄᴏᴘʏ", copy_text=CopyTextButton(text=formatted_raw),
            icon_custom_emoji_id="5956330306167376831", style="primary"
        )
    except ImportError:
        copy_btn = InlineKeyboardButton(
            text="ᴄᴏᴘʏ", switch_inline_query=formatted_raw,
            icon_custom_emoji_id="5956330306167376831", style="primary"
        )

    confirm_btn = InlineKeyboardButton(
        text="ᴄᴏɴғɪʀᴍ", callback_data="CONFIRM_ORDER",
        icon_custom_emoji_id="5895403643863043222", style="success"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[confirm_btn, copy_btn]])
    await message.reply(formatted_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

@main_router.callback_query(F.data == "CONFIRM_ORDER")
async def process_confirm_order(call: types.CallbackQuery):
    await call.answer()
    
    bot_id = call.bot.id
    if not await is_authorized(bot_id, call.from_user.id):
        return await call.message.answer("❌ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
        
    original_msg = call.message.reply_to_message
    
    msg_html = call.message.html_text
    match = re.search(r"<code>(.*?)</code>", msg_html)
    if not match:
        return await call.message.answer("❌ Could not extract order text.")
        
    order_text = html.unescape(match.group(1).strip())
    
    try: await call.message.delete()
    except Exception: pass
        
    if not original_msg:
        return await call.message.answer("❌ မူရင်း Message ကို ရှာမတွေ့ပါ။ Manual Copy ကူး၍ ဝယ်ယူပါ။")

    lines = [line.strip() for line in order_text.strip().split('\n') if line.strip()]
    lower_order = order_text.lower()
    
    if lower_order.startswith("mcc ") or lower_order.startswith("mcb ") or lower_order.startswith("mcgg "):
        regex = r"(?i)^(?:(?:mcc|mcb|mcp|mcgg)\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        await execute_buy_process(bot_id, original_msg, lines, regex, 'BR', MCC_PACKAGES, process_mcc_order, "MCC", is_mcc=True)
    elif lower_order.startswith("mcp "):
        regex = r"(?i)^(?:mcp\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        await execute_buy_process(bot_id, original_msg, lines, regex, 'PH', PH_MCC_PACKAGES, process_mcc_order, "MCC", is_mcc=True)
    elif lower_order.startswith("b ") or lower_order.startswith("br ") or lower_order.startswith("mlb ") or lower_order.startswith("msc "):
        regex = r"(?i)^(?:(?:b|br|mlb|msc)\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        await execute_buy_process(bot_id, original_msg, lines, regex, 'BR', [DOUBLE_DIAMOND_PACKAGES, BR_PACKAGES], process_smile_one_order_br, "MLBB")
    elif lower_order.startswith("p ") or lower_order.startswith("ph ") or lower_order.startswith("mlp "):
        regex = r"(?i)^(?:(?:p|ph|mlp|mcp)\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        await execute_buy_process(bot_id, original_msg, lines, regex, 'PH', PH_PACKAGES, process_smile_one_order_ph, "MLBB")
    else:
        await call.message.answer("⚠️ Item Package မပါဝင်ပါ။")

@main_router.message(F.text.regexp(r"(?i)^\.clone\s+([^:]+:[A-Za-z0-9_-]+)"))
async def clone_bot_command(message: types.Message):
    if message.from_user.id != OWNER_ID: return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    match = re.search(r"(?i)^\.clone\s+(\S+)", message.text)
    token = match.group(1).strip()
    loading = await message.reply("⏳ Cloning Bot... Please wait.")
    
    try:
        new_bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        bot_info = await new_bot.get_me()
        await db.add_cloned_bot(token, bot_info.id)
        asyncio.create_task(start_cloned_bot_polling(new_bot))
        await loading.edit_text(
            f"✅ <b>Bot Cloned Successfully!</b>\n\n"
            f"🤖 <b>Bot:</b> @{bot_info.username}\n"
            f"🆔 <b>Bot ID:</b> <code>{bot_info.id}</code>\n\n"
            f"<i>မှတ်ချက်: Clone Bot အတွက် Cookie ကို ၎င်း Bot ဆီသို့သွား၍ /setcookie ဖြင့် သီးသန့်ထည့်သွင်းပေးပါ။</i>"
        )
    except Exception as e:
        await loading.edit_text(f"❌ <b>Clone Failed:</b> Invalid Token or API Error.\n{str(e)}")

@main_router.message(F.text.regexp(r"(?i)^\.delbot\s+([^:]+:[A-Za-z0-9_-]+)"))
async def delete_bot_command(message: types.Message):
    if message.from_user.id != OWNER_ID: return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    match = re.search(r"(?i)^\.delbot\s+(\S+)", message.text)
    token = match.group(1).strip()
    deleted = await db.remove_cloned_bot(token)
    
    if deleted:
        await message.reply(
            "✅ <b>Bot Removed Successfully!</b>\n\n"
            "မှတ်ချက်။ ။ Database ထဲမှ အောင်မြင်စွာ ဖျက်ပစ်လိုက်ပါပြီ။ လက်ရှိ Run နေသော Bot ကို အပြီးတိုင် ရပ်တန့်သွားစေရန် Render တွင် <b>Manual Restart / Redeploy</b> တစ်ကြိမ် လုပ်ပေးရန် လိုအပ်ပါသည်။"
        )
    else: await message.reply("❌ <b>Error:</b> ထို Token ဖြင့် မှတ်သားထားသော Bot မရှိပါ။")

@main_router.message(F.text.regexp(r"(?i)^\.topup\s+([a-zA-Z0-9]+)\s+b\s*$"))
async def handle_topup_br(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    match = re.search(r"(?i)^\.topup\s+([a-zA-Z0-9]+)\s+b\s*$", message.text.strip())
    activation_code = match.group(1).strip()
    tg_id = str(message.from_user.id)
    loading_msg = await message.reply(f"Checking Code `{activation_code}` for Region `BR`...")
    
    async with user_locks[tg_id]:
        scraper = await get_bot_scraper(bot_id)
        page_url = 'https://www.smile.one/customer/activationcode'
        check_url = 'https://www.smile.one/smilecard/pay/checkcard'
        pay_url = 'https://www.smile.one/smilecard/pay/payajax'
        base_origin = 'https://www.smile.one'
        base_referer = 'https://www.smile.one/'
        balance_check_url = 'https://www.smile.one/customer/order'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'text/html', 'Referer': base_referer}

        try:
            res = await scraper.get(page_url, headers=headers)
            if "login" in str(res.url).lower() or res.status_code in [403, 503]: 
                await loading_msg.edit_text("⚠️ <b>Cookies Expired!</b>\n\nAuto-login စတင်နေပါသည်... ခဏစောင့်ပြီး ပြန်လည်ကြိုးစားပါ။")
                if bot_id == bot.id: await notify_owner("⚠️ <b>Top-up Alert (BR):</b> Cookie သက်တမ်းကုန်သွားပါသည်။ Auto-login စတင်နေပါသည်...")
                success = await auto_login_and_get_cookie(bot_id)
                if not success and bot_id == bot.id: await notify_owner("❌ <b>Critical:</b> Auto-Login မအောင်မြင်ပါ။ `/setcookie` ဖြင့် အသစ်ထည့်ပေးပါ။")
                return

            soup = BeautifulSoup(res.text, 'html.parser')
            csrf_token = soup.find('meta', {'name': 'csrf-token'})
            if csrf_token: csrf_token = csrf_token.get('content')
            elif soup.find('input', {'name': '_csrf'}): csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
            else: csrf_token = None
            if not csrf_token: return await loading_msg.edit_text("❌ CSRF Token ရှာမတွေ့ပါ။ Cookie သက်တမ်းကုန်နေနိုင်ပါသည်။")

            ajax_headers = headers.copy()
            ajax_headers.update({'X-Requested-With': 'XMLHttpRequest', 'Origin': base_origin, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})

            check_res_raw = await scraper.post(check_url, data={'_csrf': csrf_token, 'pin': activation_code}, headers=ajax_headers)
            check_res = check_res_raw.json()
            code_status = str(check_res.get('code', check_res.get('status', '')))
            
            card_amount = 0.0
            try:
                if 'data' in check_res and isinstance(check_res['data'], dict):
                    val = check_res['data'].get('amount', check_res['data'].get('money', 0))
                    if val: card_amount = float(val)
            except: pass
            
            if code_status == '201':
                return await loading_msg.edit_text("Please enter the correct product code.")
            elif code_status == '202':
                return await loading_msg.edit_text("This code has already been used. Please use another code.")
            #

            if code_status in ['200', '0', '1'] or 'success' in str(check_res.get('msg', '')).lower():
                old_bal = await get_smile_balance(scraper, headers, balance_check_url)
                pay_res_raw = await scraper.post(pay_url, data={'_csrf': csrf_token, 'sec': activation_code}, headers=ajax_headers)
                pay_res = pay_res_raw.json()
                pay_status = str(pay_res.get('code', pay_res.get('status', '')))
                
                if pay_status in ['200', '0', '1'] or 'success' in str(pay_res.get('msg', '')).lower():
                    await asyncio.sleep(5) 
                    anti_cache_url = f"{balance_check_url}?_t={int(time.time())}"
                    new_bal = await get_smile_balance(scraper, headers, anti_cache_url)
                    added_amount = round(new_bal['br_balance'] - old_bal['br_balance'], 2)
                    
                    if added_amount <= 0 and card_amount > 0: added_amount = card_amount
                        
                    if added_amount <= 0:
                        await loading_msg.edit_text(f"sᴍɪʟᴇ ᴏɴᴇ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ sᴜᴄᴄᴇss ✅\n(Cannot retrieve exact amount due to System Delay.)")
                    else:
                        flag = f"<tg-emoji emoji-id='{BR_EMOJI}'>🇧🇷</tg-emoji>"
                        if bot_id != bot.id:
                            fee_amount = added_amount * CLONE_BOT_FEE_PERCENT
                            v_added = added_amount - fee_amount
                            await db.update_clone_wallet(bot_id, 'BR', v_added)
                            v_wallet = await db.get_clone_wallet(bot_id)
                            
                            fmt_amount = int(added_amount) if added_amount % 1 == 0 else added_amount
                            v_added_fmt = int(v_added) if v_added % 1 == 0 else v_added
                            fee_fmt = int(fee_amount) if fee_amount % 1 == 0 else fee_amount
                            
                            msg = (
                                f"✅ <b>Code Top-Up Successful</b>\n\n"
                                f"<code>Code   : {activation_code} (BR)\n"
                                f"Amount : {fmt_amount:,}\n"
                                f"Fee ({int(CLONE_BOT_FEE_PERCENT*100)}%) : -{fee_fmt:,}\n"
                                f"V-Added: +{v_added_fmt:,} 🪙</code>\n"
                                f"{flag} <code>V-Wallet : {v_wallet.get('br_balance', 0.0):,.2f} 🪙</code>"
                            )
                        else:
                            fmt_amount = int(added_amount) if added_amount % 1 == 0 else added_amount
                            assets = new_bal.get('br_balance', 0.0)
                            msg = (
                                f"✅ <b>Code Top-Up Successful</b>\n\n"
                                f"<code>Code   : {activation_code} (BR)\n"
                                f"Amount : {fmt_amount:,}\n"
                                f"Added  : +{added_amount:,.1f} 🪙</code>\n"
                                f"{flag} <code>Total  : {assets:,.1f} 🪙</code>"
                            )
                        await loading_msg.edit_text(msg, parse_mode=ParseMode.HTML)
                else: await loading_msg.edit_text("❌ Payment failed during redemption.")
            else: await loading_msg.edit_text("Cʜᴇᴄᴋ Fᴀɪʟᴇᴅ❌\n(Code is invalid or might have been used)")
        except Exception as e: await loading_msg.edit_text(f"❌ Error: {str(e)}")

@main_router.message(F.text.regexp(r"(?i)^\.topup\s+([a-zA-Z0-9]+)\s+p\s*$"))
async def handle_topup_ph(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    match = re.search(r"(?i)^\.topup\s+([a-zA-Z0-9]+)\s+p\s*$", message.text.strip())
    activation_code = match.group(1).strip()
    tg_id = str(message.from_user.id)
    loading_msg = await message.reply(f"Checking Code `{activation_code}` for Region `PH`...")
    
    async with user_locks[tg_id]:
        scraper = await get_bot_scraper(bot_id)
        page_url = 'https://www.smile.one/ph/customer/activationcode'
        check_url = 'https://www.smile.one/ph/smilecard/pay/checkcard'
        pay_url = 'https://www.smile.one/ph/smilecard/pay/payajax'
        base_origin = 'https://www.smile.one'
        base_referer = 'https://www.smile.one/ph/'
        balance_check_url = 'https://www.smile.one/ph/customer/order'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'text/html', 'Referer': base_referer}

        try:
            res = await scraper.get(page_url, headers=headers)
            if "login" in str(res.url).lower() or res.status_code in [403, 503]: 
                await loading_msg.edit_text("⚠️ <b>Cookies Expired!</b>\n\nAuto-login စတင်နေပါသည်... ခဏစောင့်ပြီး ပြန်လည်ကြိုးစားပါ။")
                if bot_id == bot.id: await notify_owner("⚠️ <b>Top-up Alert (PH):</b> Cookie သက်တမ်းကုန်သွားပါသည်။ Auto-login စတင်နေပါသည်...")
                success = await auto_login_and_get_cookie(bot_id)
                if not success and bot_id == bot.id: await notify_owner("❌ <b>Critical:</b> Auto-Login မအောင်မြင်ပါ။ `/setcookie` ဖြင့် အသစ်ထည့်ပေးပါ။")
                return

            soup = BeautifulSoup(res.text, 'html.parser')
            csrf_token = soup.find('meta', {'name': 'csrf-token'})
            if csrf_token: csrf_token = csrf_token.get('content')
            elif soup.find('input', {'name': '_csrf'}): csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
            else: csrf_token = None
            if not csrf_token: return await loading_msg.edit_text("❌ CSRF Token ရှာမတွေ့ပါ။ Cookie သက်တမ်းကုန်နေနိုင်ပါသည်။")

            ajax_headers = headers.copy()
            ajax_headers.update({'X-Requested-With': 'XMLHttpRequest', 'Origin': base_origin, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})

            check_res_raw = await scraper.post(check_url, data={'_csrf': csrf_token, 'pin': activation_code}, headers=ajax_headers)
            check_res = check_res_raw.json()
            code_status = str(check_res.get('code', check_res.get('status', '')))
            
            card_amount = 0.0
            try:
                if 'data' in check_res and isinstance(check_res['data'], dict):
                    val = check_res['data'].get('amount', check_res['data'].get('money', 0))
                    if val: card_amount = float(val)
            except: pass
            
            if code_status == '201':
                return await loading_msg.edit_text("Please enter the correct product code.")
            elif code_status == '202':
                return await loading_msg.edit_text("This code has already been used. Please use another code.")

            if code_status in ['200', '0', '1'] or 'success' in str(check_res.get('msg', '')).lower():
                old_bal = await get_smile_balance(scraper, headers, balance_check_url)
                pay_res_raw = await scraper.post(pay_url, data={'_csrf': csrf_token, 'sec': activation_code}, headers=ajax_headers)
                pay_res = pay_res_raw.json()
                pay_status = str(pay_res.get('code', pay_res.get('status', '')))
                
                if pay_status in ['200', '0', '1'] or 'success' in str(pay_res.get('msg', '')).lower():
                    await asyncio.sleep(5) 
                    anti_cache_url = f"{balance_check_url}?_t={int(time.time())}"
                    new_bal = await get_smile_balance(scraper, headers, anti_cache_url)
                    added_amount = round(new_bal['ph_balance'] - old_bal['ph_balance'], 2)
                    
                    if added_amount <= 0 and card_amount > 0: added_amount = card_amount
                        
                    if added_amount <= 0:
                        await loading_msg.edit_text(f"sᴍɪʟᴇ ᴏɴᴇ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ sᴜᴄᴄᴇss ✅\n(Cannot retrieve exact amount due to System Delay.)")
                    else:
                        flag = f"<tg-emoji emoji-id='{PH_EMOJI}'>🇵🇭</tg-emoji>"
                        if bot_id != bot.id:
                            fee_amount = added_amount * CLONE_BOT_FEE_PERCENT
                            v_added = added_amount - fee_amount
                            await db.update_clone_wallet(bot_id, 'PH', v_added)
                            v_wallet = await db.get_clone_wallet(bot_id)
                            
                            fmt_amount = int(added_amount) if added_amount % 1 == 0 else added_amount
                            v_added_fmt = int(v_added) if v_added % 1 == 0 else v_added
                            fee_fmt = int(fee_amount) if fee_amount % 1 == 0 else fee_amount
                            
                            msg = (
                                f"✅ <b>Code Top-Up Successful</b>\n\n"
                                f"<code>Code   : {activation_code} (PH)\n"
                                f"Amount : {fmt_amount:,}\n"
                                f"Fee ({int(CLONE_BOT_FEE_PERCENT*100)}%) : -{fee_fmt:,}\n"
                                f"V-Added: +{v_added_fmt:,} 🪙</code>\n"
                                f"{flag} <code>V-Wallet : {v_wallet.get('ph_balance', 0.0):,.2f} 🪙</code>"
                            )
                        else:
                            fmt_amount = int(added_amount) if added_amount % 1 == 0 else added_amount
                            assets = new_bal.get('ph_balance', 0.0)
                            msg = (
                                f"✅ <b>Code Top-Up Successful</b>\n\n"
                                f"<code>Code   : {activation_code} (PH)\n"
                                f"Amount : {fmt_amount:,}\n"
                                f"Added  : +{added_amount:,.1f} 🪙</code>\n"
                                f"{flag} <code>Total  : {assets:,.1f} 🪙</code>"
                            )
                        await loading_msg.edit_text(msg, parse_mode=ParseMode.HTML)
                else: await loading_msg.edit_text("❌ Payment failed during redemption.")
            else: await loading_msg.edit_text("Cʜᴇᴄᴋ Fᴀɪʟᴇᴅ❌\n(Code is invalid or might have been used)")
        except Exception as e: await loading_msg.edit_text(f"❌ Error: {str(e)}")

@main_router.message(or_f(Command("add"), F.text.regexp(r"(?i)^\.add(?:$|\s+)")))
async def add_reseller(message: types.Message):
    if message.from_user.id != OWNER_ID: return await message.reply("You are not the Owner.")
    parts = message.text.split()
    if len(parts) < 2: return await message.reply("`/add <user_id>`")
    target_id = parts[1].strip()
    if not target_id.isdigit(): return await message.reply("Please enter the User ID in numbers only.")
    bot_id = message.bot.id
    if await db.add_reseller(bot_id, target_id, f"User_{target_id}"): 
        await message.reply(f"✅ User ID `{target_id}` ဟာ ဤ Bot အတွက် အသုံးပြုခွင့် ရရှိသွားပါပြီ။")
    else: await message.reply(f"User ID `{target_id}` ဟာ ဤ Bot တွင် အသုံးပြုခွင့် ရှိပြီးသား ဖြစ်ပါသည်။")

@main_router.message(or_f(Command("remove"), F.text.regexp(r"(?i)^\.remove(?:$|\s+)")))
async def remove_reseller_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return await message.reply("You are not the Owner.")
    parts = message.text.split()
    if len(parts) < 2: return await message.reply("Usage format - `/remove <user_id>`")
    target_id = parts[1].strip()
    if target_id == str(OWNER_ID): return await message.reply("The Owner cannot be removed.")
    bot_id = message.bot.id
    if await db.remove_reseller(bot_id, target_id): await message.reply(f"✅ User ID `{target_id}` အား ဤ Bot မှ ဖယ်ရှားလိုက်ပါပြီ။")
    else: await message.reply("ထို ID သည် ဤ Bot ၏ စာရင်းထဲတွင် မရှိပါ။")

@main_router.message(or_f(Command("users"), F.text.regexp(r"(?i)^\.users$")))
async def list_resellers(message: types.Message):
    if message.from_user.id != OWNER_ID: return await message.reply("You are not the Owner.")
    bot_id = message.bot.id
    resellers_list = await db.get_all_resellers(bot_id)
    user_list = []
    for r in resellers_list:
        role = "owner" if r["tg_id"] == str(OWNER_ID) else "authorized"
        user_list.append(f"🟢 ID: <code>{r['tg_id']}</code> ({role})")
    final_text = "\n".join(user_list) if user_list else "No users found in this bot."
    await message.reply(f"🟢 **Authorized Users for this Bot:**\n\n{final_text}", parse_mode=ParseMode.HTML)

@main_router.message(Command("setcookie"))
async def set_cookie_command(message: types.Message):
    global GLOBAL_SCRAPERS, GLOBAL_CSRF
    if message.from_user.id != OWNER_ID: return await message.reply("❌ Only the Owner can set the Cookie.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return await message.reply("⚠️ **Usage format:**\n`/setcookie <Long_Main_Cookie>`")
    bot_id = message.bot.id
    await db.update_bot_cookie(bot_id, parts[1].strip())
    GLOBAL_SCRAPERS.pop(bot_id, None)
    GLOBAL_CSRF.pop(bot_id, None)
    await message.reply(f"✅ **Cookie for Bot ID {bot_id} has been successfully updated securely.**")

@main_router.message(or_f(Command("cookies"), F.text.regexp(r"(?i)^\.cookies$")))
async def check_cookie_status(message: types.Message):
    if message.from_user.id != OWNER_ID: return await message.reply("❌ You are not authorized.")
    loading_msg = await message.reply("Checking Cookie status...")
    try:
        bot_id = message.bot.id
        scraper = await get_bot_scraper(bot_id)
        headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://www.smile.one'}
        response = await scraper.get('https://www.smile.one/customer/order', headers=headers, timeout=15)
        if "login" not in str(response.url).lower() and response.status_code == 200: await loading_msg.edit_text("🟢 Aᴄᴛɪᴠᴇ")
        else: await loading_msg.edit_text("🔴 Exᴘɪʀᴇᴅ")
    except Exception as e: await loading_msg.edit_text(f"❌ Error checking cookie: {str(e)}")

@main_router.message(F.text.contains("PHPSESSID") & F.text.contains("cf_clearance"))
async def handle_smart_cookie_update(message: types.Message):
    global GLOBAL_SCRAPERS, GLOBAL_CSRF
    if message.from_user.id != OWNER_ID: return await message.reply("❌ You are not authorized.")
    text = message.text
    target_keys = ["PHPSESSID", "cf_clearance", "__cf_bm", "_did", "_csrf"]
    extracted_cookies = {}
    try:
        for key in target_keys:
            pattern = rf"['\"]?{key}['\"]?\s*[:=]\s*['\"]?([^'\",;\s}}]+)['\"]?"
            match = re.search(pattern, text)
            if match: extracted_cookies[key] = match.group(1)
        if "PHPSESSID" not in extracted_cookies or "cf_clearance" not in extracted_cookies:
            return await message.reply("❌ <b>Error:</b> `PHPSESSID` နှင့် `cf_clearance` ကို ရှာမတွေ့ပါ။", parse_mode=ParseMode.HTML)
        formatted_cookie_str = "; ".join([f"{k}={v}" for k, v in extracted_cookies.items()])
        bot_id = message.bot.id
        await db.update_bot_cookie(bot_id, formatted_cookie_str)
        GLOBAL_SCRAPERS.pop(bot_id, None)
        GLOBAL_CSRF.pop(bot_id, None)
        success_msg = f"✅ <b>Cookies Successfully Extracted & Saved for Bot {bot_id}!</b>\n\n📦 <b>Extracted Data:</b>\n"
        for k, v in extracted_cookies.items():
            display_v = f"{v[:15]}...{v[-15:]}" if len(v) > 35 else v
            success_msg += f"🔸 <code>{k}</code> : {display_v}\n"
        success_msg += f"\n🍪 <b>Formatted Final String:</b>\n<code>{formatted_cookie_str}</code>"
        await message.reply(success_msg, parse_mode=ParseMode.HTML)
    except Exception as e: await message.reply(f"❌ <b>Parsing Error:</b> {str(e)}", parse_mode=ParseMode.HTML)

@main_router.message(or_f(Command("balance"), F.text.regexp(r"(?i)^\.bal(?:$|\s+)")))
async def check_balance_command(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    loading_msg = await message.reply("Fetching balance...")
    br_flag = f"<tg-emoji emoji-id='{BR_EMOJI}'>🇧🇷</tg-emoji>"
    ph_flag = f"<tg-emoji emoji-id='{PH_EMOJI}'>🇵🇭</tg-emoji>"

    if bot_id != bot.id:
        v_wallet = await db.get_clone_wallet(bot_id)
        report = (
            f"<blockquote><b>🤖 𝗩𝗜𝗥𝗧𝗨𝗔𝗟 𝗪𝗔𝗟𝗟𝗘𝗧 (𝗖𝗹𝗼𝗻𝗲)</b>\n\n"
            f"{br_flag} <code>𝗕𝗥 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : ${v_wallet.get('br_balance', 0.00):,.2f}</code>\n"
            f"{ph_flag} <code>𝗣𝗛 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : ${v_wallet.get('ph_balance', 0.00):,.2f}</code></blockquote>"
        )
        return await loading_msg.edit_text(report, parse_mode=ParseMode.HTML)
    
    scraper = await get_bot_scraper(bot_id)
    headers = {'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://www.smile.one'}
    try:
        anti_cache_url = f"https://www.smile.one/customer/order?_t={int(time.time())}"
        balances = await get_smile_balance(scraper, headers, anti_cache_url)
        report = (
            f"<blockquote><b>𝗢𝗙𝗙𝗜𝗖𝗜𝗔𝗟 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗕𝗔𝗟𝗔𝗡𝗖𝗘</b>\n\n"
            f"{br_flag} <code>𝗕𝗥 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : ${balances.get('br_balance', 0.00):,.2f}</code>\n"
            f"{ph_flag} <code>𝗣𝗛 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : ${balances.get('ph_balance', 0.00):,.2f}</code></blockquote>"
        )
        await loading_msg.edit_text(report, parse_mode=ParseMode.HTML)
    except Exception as e: await loading_msg.edit_text(f"❌ Error fetching balance: {str(e)}")

@main_router.message(F.text.regexp(r"(?i)^(?:msc|mlb|br|b)\s+\d+"))
async def handle_br_mlbb(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply(f"ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.❌")
    try:
        lines = [line.strip() for line in message.text.strip().split('\n') if line.strip()]
        regex = r"(?i)^(?:(?:b|br|mlb|msc)\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        total_pkgs = 0
        for line in lines:
            match = re.search(regex, line)
            if match: total_pkgs += len(match.group(3).split())
        if total_pkgs > 10: return await message.reply("❌ 10 Limit Exceeded: တစ်ကြိမ်လျှင် အများဆုံး ၁၀ ခုသာ ဝယ်ယူနိုင်ပါသည်။")
        await execute_buy_process(bot_id, message, lines, regex, 'BR', [DOUBLE_DIAMOND_PACKAGES, BR_PACKAGES], process_smile_one_order_br, "MLBB")
    except Exception as e: await message.reply(f"System Error: {str(e)}")

@main_router.message(F.text.regexp(r"(?i)^(?:mlp|ph|p)\s+\d+"))
async def handle_ph_mlbb(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply(f"ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.❌")
    try:
        lines = [line.strip() for line in message.text.strip().split('\n') if line.strip()]
        regex = r"(?i)^(?:(?:p|ph|mlp|mcp)\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        total_pkgs = 0
        for line in lines:
            match = re.search(regex, line)
            if match: total_pkgs += len(match.group(3).split())
        if total_pkgs > 10: return await message.reply("❌ 10 Limit Exceeded: တစ်ကြိမ်လျှင် အများဆုံး ၁၀ ခုသာ ဝယ်ယူနိုင်ပါသည်။")
        await execute_buy_process(bot_id, message, lines, regex, 'PH', PH_PACKAGES, process_smile_one_order_ph, "MLBB")
    except Exception as e: await message.reply(f"System Error: {str(e)}")

@main_router.message(F.text.regexp(r"(?i)^(?:mcc|mcb)\s+\d+"))
async def handle_br_mcc(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply(f"ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.❌")
    try:
        lines = [line.strip() for line in message.text.strip().split('\n') if line.strip()]
        regex = r"(?i)^(?:(?:mcc|mcb|mcp|mcgg)\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        total_pkgs = 0
        for line in lines:
            match = re.search(regex, line)
            if match: total_pkgs += len(match.group(3).split())
        if total_pkgs > 5: return await message.reply("❌ 5 Limit Exceeded: တစ်ကြိမ်လျှင် အများဆုံး ၅ ခုသာ ဝယ်ယူနိုင်ပါသည်။")
        await execute_buy_process(bot_id, message, lines, regex, 'BR', MCC_PACKAGES, process_mcc_order, "MCC", is_mcc=True)
    except Exception as e: await message.reply(f"System Error: {str(e)}")

@main_router.message(F.text.regexp(r"(?i)^mcp\s+\d+"))
async def handle_ph_mcc(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply(f"ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.❌")
    try:
        lines = [line.strip() for line in message.text.strip().split('\n') if line.strip()]
        regex = r"(?i)^(?:mcp\s+)?(\d+)\s*\(?\s*(\d+)\s*\)?\s*(.+)$"
        total_pkgs = 0
        for line in lines:
            match = re.search(regex, line)
            if match: total_pkgs += len(match.group(3).split())
        if total_pkgs > 5: return await message.reply("❌ 5 Limit Exceeded: တစ်ကြိမ်လျှင် အများဆုံး ၅ ခုသာ ဝယ်ယူနိုင်ပါသည်။")
        await execute_buy_process(bot_id, message, lines, regex, 'PH', PH_MCC_PACKAGES, process_mcc_order, "MCC", is_mcc=True)
    except Exception as e: await message.reply(f"System Error: {str(e)}")

@main_router.message(or_f(Command("checkcus"), Command("cus"), F.text.regexp(r"(?i)^\.(?:checkcus|cus)(?:$|\s+)")))
async def check_official_customer(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("❌ You are not authorized.")
    parts = message.text.strip().split()
    if len(parts) < 2: return await message.reply("⚠️ <b>Usage:</b> <code>.cus <Game_ID></code>")
    search_query = parts[1]
    loading_msg = await message.reply(f"Deep Searching Official Records for: <code>{search_query}</code>...")
    scraper = await get_bot_scraper(bot_id)
    headers = {'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://www.smile.one'}
    urls_to_check = ['https://www.smile.one/customer/activationcode/codelist', 'https://www.smile.one/ph/customer/activationcode/codelist']
    found_orders = []
    seen_ids = set()
    try:
        for api_url in urls_to_check:
            for page_num in range(1, 11): 
                res = await scraper.get(api_url, params={'type': 'orderlist', 'p': str(page_num), 'pageSize': '50'}, headers=headers, timeout=15)
                try:
                    data = res.json()
                    if 'list' in data and len(data['list']) > 0:
                        for order in data['list']:
                            current_user_id = str(order.get('user_id') or order.get('role_id') or '')
                            order_id = str(order.get('increment_id') or order.get('id') or '')
                            status_val = str(order.get('order_status', '') or order.get('status', '')).lower()
                            if (current_user_id == search_query or order_id == search_query) and status_val in ['success', '1']:
                                if order_id not in seen_ids:
                                    seen_ids.add(order_id)
                                    found_orders.append(order)
                    else: break 
                except: break
        if not found_orders: return await loading_msg.edit_text(f"❌ No successful records found for: <code>{search_query}</code>")
        found_orders = found_orders[:1] 
        report = f"🎉<b>Oғғɪᴄɪᴀʟ Rᴇᴄᴏʀᴅs ғᴏʀ {search_query}</b>\n\n"
        for order in found_orders:
            serial_id = str(order.get('increment_id') or order.get('id') or 'Unknown Serial')
            date_str = str(order.get('created_at') or order.get('updated_at') or order.get('create_time') or '')
            currency_sym = str(order.get('total_fee_currency') or '$')
            date_display = date_str
            if date_str:
                try:
                    dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    mmt_dt = dt_obj + datetime.timedelta(hours=9, minutes=30)
                    date_display = f"{date_str} ( MM - {mmt_dt.strftime('%I:%M:%S %p')} )"
                except Exception: date_display = date_str

            raw_item_name = str(order.get('product_name') or order.get('goods_name') or order.get('title') or 'Unknown Item')
            raw_item_name = raw_item_name.replace("Mobile Legends BR - ", "").replace("Mobile Legends - ", "").strip()
            translations = {"Passe Semanal de Diamante": "Weekly Diamond Pass", "Passagem do crepúsculo": "Twilight Pass", "Passe Crepúsculo": "Twilight Pass", "Pacote Semanal Elite": "Elite Weekly Bundle", "Pacote Mensal Épico": "Epic Monthly Bundle", "Membro Estrela Plus": "Starlight Member Plus", "Membro Estrela": "Starlight Member", "Diamantes": "Diamonds", "Diamante": "Diamond", "Bônus": "Bonus", "Pacote": "Bundle"}
            for pt, en in translations.items():
                if pt in raw_item_name: raw_item_name = raw_item_name.replace(pt, en)
            if raw_item_name.endswith(" c") or raw_item_name.endswith(" ("): raw_item_name = raw_item_name[:-2]
            final_item_name = f"{raw_item_name.strip()}"
            price = str(order.get('price') or order.get('grand_total') or order.get('real_money') or '0.00')
            price_display = f"{price} {currency_sym}" if currency_sym != '$' else f"${price}"
            report += f"🏷 <code>{serial_id}</code>\n📅 <code>{date_display}</code>\n💎 {final_item_name} ({price_display})\n📊 Status: ✅ Success\n\n"
        await loading_msg.edit_text(report)
    except Exception as e: await loading_msg.edit_text(f"❌ Search Error: {str(e)}")

@main_router.message(or_f(Command("history"), F.text.regexp(r"(?i)^\.his$")))
async def send_order_history(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    tg_id = str(message.from_user.id)
    user_name = message.from_user.username or message.from_user.first_name
    history_data = await db.get_user_history(tg_id, limit=200)
    if not history_data: return await message.reply("📜 **No Order History Found.**")
    response_text = f"==== Order History for @{user_name} ====\n\n"
    for order in history_data:
        response_text += (f"🆔 Game ID: {order['game_id']}\n🌏 Zone ID: {order['zone_id']}\n💎 Pack: {order['item_name']}\n🆔 Order ID: {order['order_id']}\n📅 Date: {order['date_str']}\n💲 Rate: ${order['price']:,.2f}\n📊 Status: {order['status']}\n────────────────\n")
    file_bytes = response_text.encode('utf-8')
    document = BufferedInputFile(file_bytes, filename=f"History_{tg_id}.txt")
    await message.answer_document(document=document, caption=f"📜 **Order History**\n👤 User: @{user_name}\n📊 Records: {len(history_data)}")

@main_router.message(or_f(Command("clean"), F.text.regexp(r"(?i)^\.clean$")))
async def clean_order_history(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    tg_id = str(message.from_user.id)
    deleted_count = await db.clear_user_history(tg_id)
    if deleted_count > 0: await message.reply(f"🗑️ **History Cleaned Successfully.**\nDeleted {deleted_count} order records from your history.")
    else: await message.reply("📜 **No Order History Found to Clean.**")

@main_router.message(or_f(Command("region"), F.text.regexp(r"(?i)^\.region(?:$|\s+)")))
async def handle_check_region(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    match = re.search(r"(?i)^[./]?region\s+(\d+)\s*[\(]?\s*(\d+)\s*[\)]?", message.text.strip())
    if not match: return await message.reply("❌ Invalid format. Use: `.region 12345678 1234`")
    game_id, zone_id = match.group(1).strip(), match.group(2).strip()
    loading_msg = await message.reply("Checking account data...")
    api_url = 'https://yanjiestore.com/index.php/check-region-mlbb'
    payload = {'uid': game_id, 'server': zone_id}
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15', 'Accept': 'application/json'}
    try:
        # Proxy မသုံးတော့ဘဲ တိုက်ရိုက် Request လှမ်းပါမည်
        async with AsyncSession(impersonate="chrome124") as local_scraper:
            res = await local_scraper.post(api_url, data=payload, headers=headers, timeout=15)
        try: data = res.json()
        except Exception: return await loading_msg.edit_text(f"❌ API Error: Invalid Response.\n\n<code>{res.text[:100]}...</code>")
        if not data.get('status'):
            error_msg = data.get('msg') or data.get('message') or "Game ID သို့မဟုတ် Zone ID မှားယွင်းနေပါသည်။"
            return await loading_msg.edit_text(f"❌ **Invalid Account:** <code>{error_msg}</code>")
        user_data = data.get('data', {})
        ig_name = user_data.get('nick', 'Unknown')
        country_code = user_data.get('region', 'Unknown')
        
        country_map = {
            "MM": "Myanmar", "MY": "Malaysia", "PH": "Philippines", "ID": "Indonesia", "SG": "Singapore", "KH": "Cambodia", "TH": "Thailand", "JP": "Japan",
            "KR": "South Korea", "CN": "China", "TW": "Taiwan", "HK": "Hong Kong", "VN": "Vietnam", "LA": "Laos", "BN": "Brunei", "TL": "Timor-Leste",
            "IN": "India", "PK": "Pakistan", "BD": "Bangladesh", "LK": "Sri Lanka", "NP": "Nepal", "BT": "Bhutan", "MV": "Maldives", "AF": "Afghanistan",
            "IR": "Iran", "IQ": "Iraq", "SA": "Saudi Arabia", "AE": "United Arab Emirates", "QA": "Qatar", "KW": "Kuwait", "OM": "Oman", "YE": "Yemen", "JO": "Jordan",
            "LB": "Lebanon", "IL": "Israel", "SY": "Syria", "TR": "Turkey", "AZ": "Azerbaijan", "GE": "Georgia", "AM": "Armenia", "KZ": "Kazakhstan",
            "UZ": "Uzbekistan", "TM": "Turkmenistan", "KG": "Kyrgyzstan", "TJ": "Tajikistan", "MN": "Mongolia", "FR": "France", "GB": "United Kingdom",
            "DE": "Germany", "IT": "Italy", "ES": "Spain", "PT": "Portugal", "NL": "Netherlands", "BE": "Belgium", "LU": "Luxembourg", "CH": "Switzerland",
            "AT": "Austria", "PL": "Poland", "CZ": "Czech Republic", "SK": "Slovakia", "HU": "Hungary", "RO": "Romania", "BG": "Bulgaria", "GR": "Greece",
            "SE": "Sweden", "NO": "Norway", "FI": "Finland", "DK": "Denmark", "IS": "Iceland", "IE": "Ireland", "UA": "Ukraine", "BY": "Belarus",
            "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia", "HR": "Croatia", "SI": "Slovenia", "BA": "Bosnia and Herzegovina", "RS": "Serbia",
            "ME": "Montenegro", "MK": "North Macedonia", "AL": "Albania", "MD": "Moldova", "BR": "Brazil", "US": "United States", "CA": "Canada", "MX": "Mexico",
            "AR": "Argentina", "CL": "Chile", "PE": "Peru", "CO": "Colombia", "VE": "Venezuela", "EC": "Ecuador", "BO": "Bolivia", "PY": "Paraguay",
            "UY": "Uruguay", "GY": "Guyana", "SR": "Suriname", "PA": "Panama", "CR": "Costa Rica", "NI": "Nicaragua", "HN": "Honduras", "SV": "El Salvador",
            "GT": "Guatemala", "BZ": "Belize", "CU": "Cuba", "DO": "Dominican Republic", "PR": "Puerto Rico", "JM": "Jamaica", "HT": "Haiti", "BS": "Bahamas",
            "TT": "Trinidad and Tobago", "ZA": "South Africa", "EG": "Egypt", "NG": "Nigeria", "KE": "Kenya", "TZ": "Tanzania", "UG": "Uganda",
            "RW": "Rwanda", "ET": "Ethiopia", "GH": "Ghana", "SN": "Senegal", "CI": "Ivory Coast", "MA": "Morocco", "TN": "Tunisia", "DZ": "Algeria",
            "LY": "Libya", "SD": "Sudan", "SS": "South Sudan", "ZM": "Zambia", "ZW": "Zimbabwe", "MW": "Malawi", "MZ": "Mozambique", "AO": "Angola",
            "NA": "Namibia", "BW": "Botswana", "MG": "Madagascar", "MU": "Mauritius", "AU": "Australia", "NZ": "New Zealand", "FJ": "Fiji", "PG": "Papua New Guinea",
            "SB": "Solomon Islands", "VU": "Vanuatu", "WS": "Samoa", "TO": "Tonga"
        }
        final_region = country_map.get(str(country_code).upper(), country_code)
        limit_50 = limit_150 = limit_250 = limit_500 = True 
        bonus_limits = user_data.get('rechargeBonus', [])
        for item in bonus_limits:
            title = str(item.get('title', '')).lower()
            is_unavailable = (str(item.get('status', '')).lower() != 'available')
            if "50+50" in title: limit_50 = is_unavailable
            elif "150+150" in title: limit_150 = is_unavailable
            elif "250+250" in title: limit_250 = is_unavailable
            elif "500+500" in title: limit_500 = is_unavailable
        style_50 = "danger" if limit_50 else "success"
        style_150 = "danger" if limit_150 else "success"
        style_250 = "danger" if limit_250 else "success"
        style_500 = "danger" if limit_500 else "success"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Bᴏɴᴜs 50+50", callback_data="ignore", style=style_50), InlineKeyboardButton(text="Bᴏɴᴜs 150+150", callback_data="ignore", style=style_150)],
            [InlineKeyboardButton(text="Bᴏɴᴜs 250+250", callback_data="ignore", style=style_250), InlineKeyboardButton(text="Bᴏɴᴜs 500+500", callback_data="ignore", style=style_500)]
        ])
        final_report = (
            f"<u><b>Mᴏʙɪʟᴇ Lᴇɢᴇɴᴅs Bᴀɴɢ Bᴀɴɢ</b></u>\n\n"
            f"🆔 <code>{'User ID' :<9}:</code> <code>{game_id}</code> (<code>{zone_id}</code>)\n"
            f"👤 <code>{'Nickname':<9}:</code> {ig_name}\n"
            f"🌍 <code>{'Region'  :<9}:</code> {final_region}\n"
            f"────────────────\n\n"
            f"🎁 <b>Fɪʀsᴛ Rᴇᴄʜᴀʀɢᴇ Bᴏɴᴜs Sᴛᴀᴛᴜs</b>"
        )
        await loading_msg.edit_text(final_report, reply_markup=keyboard)
    except Exception as e: await loading_msg.edit_text(f"❌ System Error: {str(e)}")

@main_router.message(or_f(Command("role"), F.text.regexp(r"(?i)^\.role(?:$|\s+)")))
async def handle_check_role(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    match = re.search(r"(?i)^[./]?role\s+(\d+)\s*[\(]?\s*(\d+)\s*[\)]?", message.text.strip())
    if not match: return await message.reply("❌ Invalid format. Use: `.role 12345678 1234`")
    game_id, zone_id = match.group(1).strip(), match.group(2).strip()
    loading_msg = await message.reply("Checking account data...")
    url_caliph = 'https://cekidml.caliph.dev/api/validasi'
    params_caliph = {'id': game_id, 'serverid': zone_id}
    headers_caliph = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Referer': 'https://cekidml.caliph.dev/', 'X-Requested-With': 'XMLHttpRequest'}
    url_malsawma = 'https://www.malsawmastore.in/gadget/doublediamonds_action.php'
    payload_malsawma = {'id': game_id, 'zone': zone_id}
    headers_malsawma = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36', 'Origin': 'https://www.malsawmastore.in', 'Referer': 'https://www.malsawmastore.in/gadget/doublediamonds', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
    try:
        async with AsyncSession(impersonate="safari_ios") as local_scraper:
            await local_scraper.get('https://cekidml.caliph.dev/', headers=headers_caliph, timeout=15)
            res_caliph, res_malsawma = await asyncio.gather(
                local_scraper.get(url_caliph, params=params_caliph, headers=headers_caliph, timeout=15),
                local_scraper.post(url_malsawma, data=payload_malsawma, headers=headers_malsawma, timeout=15)
            )
        ig_name = "Unknown"
        region = "Unknown"
        try:
            data_caliph = res_caliph.json()
            if data_caliph.get('status') == 'success':
                result_data = data_caliph.get('result', {})
                ig_name = result_data.get('nickname', 'Unknown')
                region = result_data.get('country', 'Unknown')
            else:
                error_msg = data_caliph.get('message') or data_caliph.get('msg') or "Game ID သို့မဟုတ် Zone ID မှားယွင်းနေပါသည်။"
                return await loading_msg.edit_text(f"❌ **Invalid Account:** {error_msg}")
        except Exception:
            debug_msg = res_caliph.text[:120].replace('<', '&lt;').replace('>', '&gt;').strip()
            return await loading_msg.edit_text(f"❌ **API Error:**\n<code>{debug_msg}...</code>")
        limit_50 = limit_150 = limit_250 = limit_500 = True 
        debug_bonus_error = ""
        try:
            data_double = res_malsawma.json()
            if str(data_double.get('status', '')).lower() == 'true':
                dd_data = data_double.get('dd', {})
                limit_50 = not dd_data.get('50', False)
                limit_150 = not dd_data.get('150', False)
                limit_250 = not dd_data.get('250', False)
                limit_500 = not dd_data.get('500', False)
            else: debug_bonus_error = " <i>(Bonus Data Unavailable)</i>"
        except Exception: debug_bonus_error = " <i>(Bonus Data Error)</i>"
        style_50 = "danger" if limit_50 else "success"
        style_150 = "danger" if limit_150 else "success"
        style_250 = "danger" if limit_250 else "success"
        style_500 = "danger" if limit_500 else "success"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Bᴏɴᴜs 50+50", callback_data="ignore", style=style_50), InlineKeyboardButton(text="Bᴏɴᴜs 150+150", callback_data="ignore", style=style_150)],
            [InlineKeyboardButton(text="Bᴏɴᴜs 250+250", callback_data="ignore", style=style_250), InlineKeyboardButton(text="Bᴏɴᴜs 500+500", callback_data="ignore", style=style_500)]
        ])
        final_report = (
            f"<u><b>Mᴏʙɪʟᴇ Lᴇɢᴇɴᴅs Bᴀɴɢ Bᴀɴɢ</b></u>\n\n"
            f"🆔 <code>{'User ID' :<9}:</code> <code>{game_id}</code> (<code>{zone_id}</code>)\n"
            f"👤 <code>{'Nickname':<9}:</code> {ig_name}\n"
            f"🌍 <code>{'Region'  :<9}:</code> {region}\n"
            f"────────────────\n\n"
            f"🎁 <b>Fɪʀsᴛ Rᴇᴄʜᴀʀɢᴇ Bᴏɴᴜs Sᴛᴀᴛᴜs</b>{debug_bonus_error}"
        )
        await loading_msg.edit_text(final_report, reply_markup=keyboard)
    except Exception as e: await loading_msg.edit_text(f"❌ System Error: {str(e)}")

@main_router.message(or_f(Command("listb"), F.text.regexp(r"(?i)^\.listb$")))
async def show_price_list_br(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    response_text = (
        "<b>BRAZIL DIAMOND PACKAGE</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>{generate_list(BR_PACKAGES)}</code>\n\n"
        "<b>DOUBLE DIAMOND PACKAGE</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>{generate_list(DOUBLE_DIAMOND_PACKAGES)}</code>"
    )
    await message.reply(response_text)

@main_router.message(or_f(Command("listp"), F.text.regexp(r"(?i)^\.listp$")))
async def show_price_list_ph(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    response_text = "<b>PHILIPPINES DIAMOND PACKAGE</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" f"<code>{generate_list(PH_PACKAGES)}</code>"
    await message.reply(response_text)

@main_router.message(or_f(Command("listmb"), F.text.regexp(r"(?i)^\.listmb$")))
async def show_price_list_mcc_br(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    response_text = "<b>BRAZIL MCC PACKAGE</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" f"<code>{generate_list(MCC_PACKAGES)}</code>"
    await message.reply(response_text)

@main_router.message(or_f(Command("listmp"), F.text.regexp(r"(?i)^\.listmp$")))
async def show_price_list_mcc_ph(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    response_text = "<b>PHILIPPINES MCC PACKAGE</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" f"<code>{generate_list(PH_MCC_PACKAGES)}</code>"
    await message.reply(response_text)

@main_router.message(F.text.regexp(r"^[\d\s\.\(\)]+[\+\-\*\/][\d\s\+\-\*\/\(\)\.]+$"))
async def auto_calculator(message: types.Message):
    try:
        expr = message.text.strip()
        if re.match(r"^09[-\s]?\d+", expr): return
        clean_expr = expr.replace(" ", "")
        result = eval(clean_expr, {"__builtins__": None})
        formatted_result = f"{result:.4f}".rstrip('0').rstrip('.') if isinstance(result, float) else str(result)
        await message.reply(f"{expr} = {formatted_result}")
    except Exception: pass

@main_router.message(or_f(Command("maintenance"), F.text.regexp(r"(?i)^\.maintenance(?:$|\s+)")))
async def toggle_maintenance(message: types.Message):
    global IS_MAINTENANCE
    if message.from_user.id != OWNER_ID: return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    parts = message.text.strip().lower().split()
    if len(parts) < 2 or parts[1] not in ["enable", "disable"]: return await message.reply("⚠️ **Usage:** `.maintenance enable` သို့မဟုတ် `.maintenance disable`")
    if parts[1] == "enable":
        IS_MAINTENANCE = True
        await message.reply("✅ **Maintenance Mode ENABLED.**\nယခုအချိန်မှစ၍ Admin မှလွဲ၍ အခြား User များ Bot ကို အသုံးပြု၍ မရတော့ပါ။")
    else:
        IS_MAINTENANCE = False
        await message.reply("✅ **Maintenance Mode DISABLED.**\nBot ကို ပုံမှန်အတိုင်း ပြန်လည်အသုံးပြုနိုင်ပါပြီ။")

@main_router.message(or_f(Command("scam"), F.text.regexp(r"(?i)^\.scam(?:$|\s+)")))
async def add_scam_id(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    parts = message.text.strip().split()
    if len(parts) < 2: return await message.reply("⚠️ **Usage:** `.scam <Game_ID>`")
    scam_id = parts[1].strip()
    if not scam_id.isdigit(): return await message.reply("❌ Invalid Game ID. ဂဏန်းများသာ ရိုက်ထည့်ပါ။")
    await db.add_scammer(scam_id)
    GLOBAL_SCAMMERS.add(scam_id)
    await message.reply(f"🚨 **Scammer ID Added:** <code>{scam_id}</code>\n✅ ဤ ID ကို Blacklist သို့ ထည့်သွင်းပြီးပါပြီ။")

@main_router.message(or_f(Command("unscam"), F.text.regexp(r"(?i)^\.unscam(?:$|\s+)")))
async def remove_scam_id(message: types.Message):
    bot_id = message.bot.id
    if not await is_authorized(bot_id, message.from_user.id): return await message.reply("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ.")
    parts = message.text.strip().split()
    if len(parts) < 2: return await message.reply("⚠️ **Usage:** `.unscam <Game_ID>`")
    scam_id = parts[1].strip()
    removed = await db.remove_scammer(scam_id)
    GLOBAL_SCAMMERS.discard(scam_id)
    if removed: await message.reply(f"✅ **Scammer ID Removed:** <code>{scam_id}</code>\nBlacklist ထဲမှ အောင်မြင်စွာ ဖယ်ရှားလိုက်ပါပြီ။")
    else: await message.reply(f"⚠️ ထို ID သည် Scammer စာရင်းထဲတွင် မရှိပါ။")

@main_router.message(or_f(Command("help"), F.text.regexp(r"(?i)^\.help$")))
async def send_help_message(message: types.Message):
    is_owner = (message.from_user.id == OWNER_ID)
    help_text = (
        f"<blockquote><b>🤖 𝐁𝐎𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒 𝐌𝐄𝐍𝐔</b>\n━━━━━━━━━━━━━━━━━\n\n"
        f"<b>💎 𝐌𝐋𝐁Ｂ 𝐃𝐢𝐚𝐦𝐨𝐧𝐝𝐬 (ဝယ်ယူရန်)</b>\n"
        f"🇧🇷 BR MLBB: <code>msc/mlb/br/b ID (Zone) Pack</code>\n🇵🇭 PH MLBB: <code>mlp/ph/p ID (Zone) Pack</code>\n\n"
        f"<b>♟️ 𝐌𝐚𝐠𝐢𝐜 𝐂𝐡𝐞𝐬𝐬 (ဝယ်ယူရန်)</b>\n"
        f"🇧🇷 BR MCC: <code>mcc/mcb ID (Zone) Pack</code>\n🇵🇭 PH MCC: <code>mcp ID (Zone) Pack</code>\n━━━━━━━━━━━━━━━━━\n\n"
        f"<b>👤 𝐔𝐬𝐞𝐫 𝐓𝐨𝐨𝐥𝐬 (အသုံးပြုသူများအတွက်)</b>\n"
        f"🔹 <code>.topup Code b</code>  : BR Smile Code ဖြည့်ရန်\n🔹 <code>.topup Code p</code>  : PH Smile Code ဖြည့်ရန်\n"
        f"🔹 <code>.bal</code>      : Balance စစ်ရန်\n🔹 <code>.his</code>      : မိမိဝယ်ယူခဲ့သော မှတ်တမ်းကြည့်ရန်\n"
        f"🔹 <code>.clean</code>    : မှတ်တမ်းများ ဖျက်ရန်\n🔹 <code>.region ID Zone</code> : Account & Region စစ်ရန်\n"
        f"🔹 <code>.cus ID</code>     : Customer Official Record စစ်ရန်\n"
    )
    if is_owner:
        help_text += (
            f"\n━━━━━━━━━━━━━━━━━\n<b>👑 𝐎𝐰𝐧𝐞𝐫 𝐓𝐨𝐨𝐥𝐬 (Admin သီးသန့်)</b>\n\n<b>👥 ယူဆာစီမံခန့်ခွဲမှု</b>\n"
            f"🔸 <code>.add ID</code>    : အသုံးပြုခွင့်ပေးရန်\n🔸 <code>.remove ID</code> : အသုံးပြုခွင့်ပိတ်ရန်\n"
            f"🔸 <code>.users</code>     : User စာရင်းအားလုံး ကြည့်ရန်\n\n<b>⚙️ System Setup</b>\n"
            f"🔸 <code>.cookies</code>     : Cookie အခြေအနေ စစ်ဆေးရန်\n🔸 <code>/setcookie</code>   : Main Cookie အသစ်ပြောင်းရန်\n"
            f"🔸 <code>.clone</code>       : Bot အသစ်ပွားရန် (.clone Token)\n🔸 <code>.delbot</code>      : ပွားထားသော Bot အားဖျက်ရန်\n"
        )
    help_text += f"</blockquote>"
    await message.reply(help_text)

@main_router.message(Command("start"))
async def send_welcome(message: types.Message):
    tg_id = str(message.from_user.id)
    bot_id = message.bot.id
    full_name = "User"
    try:
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        full_name = f"{first_name} {last_name}".strip() or "User"
        safe_full_name = full_name.replace('<', '').replace('>', '')
        username_display = f'<a href="tg://user?id={tg_id}">{safe_full_name}</a>'
        
        EMOJI_1, EMOJI_2, EMOJI_3, EMOJI_4, EMOJI_5 = "5956355397366320202", "5954097490109140119", "5958289678837746828", "5956330306167376831", "5954078884310814346"
        status = "🟢 Aᴄᴛɪᴠᴇ" if await is_authorized(bot_id, message.from_user.id) else "🔴 Nᴏᴛ Aᴄᴛɪᴠᴇ"
        
        welcome_text = (
            f"ʜᴇʏ ʙᴀʙʏ <tg-emoji emoji-id='{EMOJI_1}'>🥺</tg-emoji>\n\n"
            f"<tg-emoji emoji-id='{EMOJI_2}'>👤</tg-emoji> {'Usᴇʀɴᴀᴍᴇ' :<11}: {username_display}\n"
            f"<tg-emoji emoji-id='{EMOJI_3}'>🆔</tg-emoji> {'𝐈𝐃' :<11}: <code>{tg_id}</code>\n"
            f"<tg-emoji emoji-id='{EMOJI_4}'>📊</tg-emoji> {'Sᴛᴀᴛᴜs' :<11}: {status}\n\n"
            f"<tg-emoji emoji-id='{EMOJI_5}'>📞</tg-emoji> {'Cᴏɴᴛᴀᴄᴛ ᴜs' :<11}: @iwillgoforwardsalone"
        )
        await message.reply(welcome_text)
    except Exception:
        fallback_text = (
            f"ʜᴇʏ ʙᴀʙʏ 🥺\n\n👤 {'Usᴇʀɴᴀᴍᴇ' :<11}: {full_name}\n"
            f"🆔 {'𝐈𝐃' :<11}: <code>{tg_id}</code>\n📊 {'Sᴛᴀᴛᴜs' :<11}: 🔴 Nᴏᴛ Aᴄᴛɪᴠᴇ\n\n"
            f"📞 {'Cᴏɴᴛᴀᴄᴛ ᴜs' :<11}: @iwillgoforwardsalone"
        )
        await message.reply(fallback_text)

# ==========================================
# 6. Middlewares, Scheduled Tasks & Global DP
# ==========================================
class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: dict):
        if IS_MAINTENANCE and event.from_user.id != OWNER_ID:
            await event.reply("⚠️ ပြုပြင်ဆောင်ရွက်နေပါသဖြင့် Topup ဘော့အား ခနရပ်ထားပါသည်။")
            return 
        return await handler(event, data)

class ScamAlertMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: dict):
        if event.text:
            text_lower = event.text.lower()
            if text_lower.startswith((".scam ", ".unscam ", "/scam", "/unscam")):
                return await handler(event, data)
            for scam_id in GLOBAL_SCAMMERS:
                if re.search(rf"\b{scam_id}\b", event.text):
                    await event.reply("Scamer game id , Scamer Alert!", parse_mode=ParseMode.HTML)
                    break 
        return await handler(event, data)

main_dp = Dispatcher()
main_dp.include_router(main_router)
main_dp.message.middleware(MaintenanceMiddleware())
main_dp.message.middleware(ScamAlertMiddleware())

# ==========================================
# 7. Main Execution Flow & Custom Polling
# ==========================================
async def start_cloned_bot_polling(clone_bot: Bot):
    try:
        bot_info = await clone_bot.get_me()
        print(f"✅ Started custom polling for Cloned Bot: @{bot_info.username} (ID: {bot_info.id})")
        await clone_bot.delete_webhook(drop_pending_updates=True)
        allowed_updates = main_dp.resolve_used_update_types()

        offset = None
        while True:
            try:
                updates = await clone_bot.get_updates(offset=offset, timeout=20, allowed_updates=allowed_updates)
                for update in updates:
                    offset = update.update_id + 1
                    asyncio.create_task(main_dp.feed_update(clone_bot, update))
            except Exception as e:
                print(f"Polling error for {bot_info.username}: {e}")
                await asyncio.sleep(5) 
    except Exception as e: print(f"❌ Could not start polling for cloned bot: {e}")

async def main():
    print("Starting Heartbeat & Clone Management tasks...")
    print("နှလုံးသားမပါရင် ဘယ်အရာမှတရားမဝင်")
    
    loop = asyncio.get_running_loop()
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=50))
    
    try:
        scammer_list = await db.get_all_scammers()
        global GLOBAL_SCAMMERS
        GLOBAL_SCAMMERS = set(scammer_list)
        print(f"Loaded {len(GLOBAL_SCAMMERS)} Scammer IDs.")
    except Exception as e:
        print(f"Error loading scammers: {e}")

    await db.setup_indexes()
    await db.init_owner(OWNER_ID)

    cloned_docs = await db.get_all_cloned_bots()
    for doc in cloned_docs:
        token = doc['token']
        try:
            clone_bot_instance = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            bot_info = await clone_bot_instance.get_me()
            await db.add_cloned_bot(token, bot_info.id)
            asyncio.create_task(start_cloned_bot_polling(clone_bot_instance))
        except Exception as e:
            print(f"❌ Failed to initialize cloned bot {token[:10]}... : {e}")

    print("Bot is successfully running on Aiogram 3 Framework... 🎉")
    await main_dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
