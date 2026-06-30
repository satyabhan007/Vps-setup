import subprocess
import requests
import json

# CONFIGURATION: Your alert webhook (Telegram, Slack, or WhatsApp)
ALERT_WEBHOOK = "https://api.telegram.org/botYOUR_TOKEN/sendMessage"
ALERT_CHAT_ID = "YOUR_CHAT_ID"

def send_alert(message):
    print(f"🚨 ALERT: {message}")
    try:
        payload = {"chat_id": ALERT_CHAT_ID, "text": f"🚨 *Endurance CRM Alert*\n{message}"}
        requests.post(ALERT_WEBHOOK, json=payload)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def check_system():
    # Run the existing checkpoints script
    result = subprocess.run(["python3", "checkpoints.py"], capture_output=True, text=True)
    
    if "⚠️ SOME CHECKPOINTS FAILED" in result.stdout:
        # Extract which service failed from the output
        failed_services = []
        for line in result.stdout.split('\n'):
            if "❌" in line:
                failed_services.append(line.strip())
        
        alert_msg = "System Health Check Failed!\n\n" + "\n".join(failed_services)
        send_alert(alert_msg)
        return False
    
    return True

if __name__ == "__main__":
    check_system()
