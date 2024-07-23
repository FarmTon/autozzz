import os
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from telethon import TelegramClient, events, sync

# Ensure necessary directories exist
os.makedirs('sessions', exist_ok=True)
os.makedirs('querys', exist_ok=True)

# Telegram accounts configuration
accounts = [
    {'api_id': 'YOUR_API_ID_1', 'api_hash': 'YOUR_API_HASH_1', 'phone_number': 'YOUR_PHONE_NUMBER_1'},
    {'api_id': 'YOUR_API_ID_2', 'api_hash': 'YOUR_API_HASH_2', 'phone_number': 'YOUR_PHONE_NUMBER_2'},
    # Add more accounts as needed
]

# Function to start the Android emulator
def start_emulator():
    subprocess.run(["emulator", "-avd", "Pixel_3_API_30"])  # Replace with your AVD name

# Function to set up proxy on the emulator
def set_proxy():
    subprocess.run(["adb", "wait-for-device"])  # Wait until the emulator is fully booted
    subprocess.run(["adb", "shell", "settings", "put", "global", "http_proxy", "127.0.0.1:8888"])  # Set proxy to localhost:8888

# Function to start mitmproxy
def start_mitmproxy():
    subprocess.Popen(["mitmdump", "-s", "mitm_script.py"])  # Run mitmproxy with a custom script

# Function to get webview link using Telethon
async def get_webview_link(client, bot_username):
    async with client:
        await client.send_message(bot_username, '/start')
        @client.on(events.NewMessage(from_users=bot_username))
        async def handler(event):
            if event.message.buttons:
                for row in event.message.buttons:
                    for button in row:
                        if button.url:
                            return button.url
        await client.run_until_disconnected()

# Function to extract init data from webview using Selenium
def extract_init_data_from_webview(webview_link, account_phone):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service('/path/to/chromedriver')  # Replace with the path to your chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(webview_link)
        time.sleep(5)  # Wait for the page to load

        init_data = driver.execute_script("return Telegram.WebApp.initData;")
        print(f'Init data for {account_phone}: {init_data}')

        with open('querys/init_data_tokens.txt', 'a') as log:
            log.write(f'{account_phone}: {init_data}\n')
    
    finally:
        driver.quit()

# mitmproxy script to log network requests
mitm_script = """
from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    if "your-game-api-keyword" in flow.request.pretty_url:  # Replace with a keyword related to your game API
        with open("api_requests.log", "a") as log:
            log.write(f"URL: {flow.request.pretty_url}\\n")
            log.write(f"Method: {flow.request.method}\\n")
            log.write(f"Headers: {flow.request.headers}\\n")
            log.write(f"Content: {flow.request.content}\\n\\n")

addons = [
    request
]
"""

# Write the mitmproxy script to a file
with open('mitm_script.py', 'w') as file:
    file.write(mitm_script)

# Main function to run the entire process
def main():
    start_emulator()  # Start the Android emulator
    time.sleep(30)  # Wait for the emulator to fully boot
    set_proxy()  # Set the proxy on the emulator
    start_mitmproxy()  # Start mitmproxy to capture traffic

    bot_username = 'YourGameBot'  # Replace with your game bot's username

    for account in accounts:
        client = TelegramClient(f'sessions/session_{account["phone_number"]}', account['api_id'], account['api_hash'])
        webview_link = client.loop.run_until_complete(get_webview_link(client, bot_username))
        
        if webview_link:
            extract_init_data_from_webview(webview_link, account['phone_number'])  # Extract the init data from the webview using Selenium

if __name__ == "__main__":
    main()
