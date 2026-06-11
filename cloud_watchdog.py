import os
import requests
from datetime import datetime, timezone

# --- Target Repository ---
GITHUB_USER = "Sht26"
GITHUB_REPO = "project"
FILE_PATH = "database/scraped_market_data.xlsx"

MAX_AGE_HOURS = 30 

# --- Invisible Credentials ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram credentials missing from environment.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    try:
        requests.get(url, timeout=10)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def check_github_freshness():
    print(f"[*] Auditing {FILE_PATH} in the repository...")
    
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?path={FILE_PATH}"
    
    try:
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200 or not response.json():
            send_telegram_alert(f"🚨 CRITICAL: Could not find '{FILE_PATH}' in the GitHub repository. Did the initial scrape fail?")
            return
            
        last_commit_date_str = response.json()[0]['commit']['committer']['date']
        last_commit_time = datetime.strptime(last_commit_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        hours_stale = (current_time - last_commit_time).total_seconds() / 3600
        
        if hours_stale > MAX_AGE_HOURS:
            send_telegram_alert(f"⚠️ PIPELINE STALLED: Your cloud market data hasn't updated in {hours_stale:.1f} hours. Check GitHub Actions!")
        else:
            print(f"✅ Watchdog Pass: Data is healthy. Last updated {hours_stale:.1f} hours ago.")
            send_telegram_alert(f"✅ Watchdog Pass: Data is healthy. Last updated {hours_stale:.1f} hours ago.")
            
    except Exception as e:
        print(f"Failed to check GitHub API: {e}")

if __name__ == "__main__":
    check_github_freshness()
