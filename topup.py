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
            
            # Smile.one ဘက်မှ ပြန်လာသော အမှားစာသားကို ဖမ်းယူခြင်း
            api_msg = str(check_res.get('msg') or check_res.get('message') or "Unknown Error")
            
            card_amount = 0.0
            try:
                if 'data' in check_res and isinstance(check_res['data'], dict):
                    val = check_res['data'].get('amount', check_res['data'].get('money', 0))
                    if val: card_amount = float(val)
            except: pass

            # --- Server မှ ပြန်လာသော စာသားကိုသာ တိုက်ရိုက်ပြသပေးမည် ---
            if code_status in ['201', '202'] or 'fail' in api_msg.lower():
                return await loading_msg.edit_text(f"❌ <b>Cʜᴇᴄᴋ Fᴀɪʟᴇᴅ</b>\n{api_msg}")

            # --- Success ဖြစ်မှသာ ငွေဆက်ဖြည့်ရန် ---
            elif code_status in ['200', '0', '1'] or 'success' in api_msg.lower():
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
                else: 
                    pay_error_msg = str(pay_res.get('msg') or "Payment failed during redemption.")
                    await loading_msg.edit_text(f"❌ {pay_error_msg}")
            else: 
                await loading_msg.edit_text(f"Cʜᴇᴄᴋ Fᴀɪʟᴇᴅ❌\n{api_msg}")
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
            
            # Smile.one ဘက်မှ ပြန်လာသော အမှားစာသားကို ဖမ်းယူခြင်း
            api_msg = str(check_res.get('msg') or check_res.get('message') or "Unknown Error")
            
            card_amount = 0.0
            try:
                if 'data' in check_res and isinstance(check_res['data'], dict):
                    val = check_res['data'].get('amount', check_res['data'].get('money', 0))
                    if val: card_amount = float(val)
            except: pass

            # --- Server မှ ပြန်လာသော စာသားကိုသာ တိုက်ရိုက်ပြသပေးမည် ---
            if code_status in ['201', '202'] or 'fail' in api_msg.lower():
                return await loading_msg.edit_text(f"❌ <b>Cʜᴇᴄᴋ Fᴀɪʟᴇᴅ</b>\n{api_msg}")

            # --- Success ဖြစ်မှသာ ငွေဆက်ဖြည့်ရန် ---
            elif code_status in ['200', '0', '1'] or 'success' in api_msg.lower():
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
                else: 
                    pay_error_msg = str(pay_res.get('msg') or "Payment failed during redemption.")
                    await loading_msg.edit_text(f"❌ {pay_error_msg}")
            else: 
                await loading_msg.edit_text(f"Cʜᴇᴄᴋ Fᴀɪʟᴇᴅ❌\n{api_msg}")
        except Exception as e: await loading_msg.edit_text(f"❌ Error: {str(e)}")
