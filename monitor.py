import requests
import smtplib
import time
from email.mime.text import MIMEText
import sys
import logging
import os
import gzip
import shutil
from datetime import datetime

# Define the log directory and log file name with today's date
log_directory = os.path.dirname(os.path.abspath(__file__))
log_filename = f"monitor_log_{datetime.now().strftime('%Y%m%d')}.txt"

# Configure logging
logging.basicConfig(
    filename=os.path.join(log_directory, log_filename),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# Replace these variables with your actual credentials and URLs to monitor
URLS_TO_MONITOR = [
    "https://prod.inbound.afrisend.com/favicon.ico",
    "https://mail.gravityafrica.co.ke",
    "https://crm.gravityafrica.co.ke/",
    "https://support.gravityafrica.co.ke"
]

#TO_EMAIL = "Recipient incasw of and error @tech@gravityafrica.co.ke"
TO_EMAIL = "youremail"
GMAIL_USERNAME = "xxx@gmail.com"
GMAIL_PASSWORD = "Password"

# Replace the below IP value with the current Public IP value of your server or PC
EXPECTED_PUBLIC_IP = "1.1.1.1"

# Check for the Public IP of the Container
# Check is necessary as the IP is explicitly white-listed on EADC Ingress servers for some sensitive URLs

#def get_public_ip():
#    response = requests.get("https://api.ipify.org?format=json")
#    return response.json()["ip"]
def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org/?format=json")
        if response.status_code == 200:
            data = response.json()
            public_ip = data["ip"]
            return public_ip
        else:
            print("Failed to fetch IP. Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error occurred:", str(e))
        return None

# Test the function
current_public_ip = get_public_ip()
if current_public_ip:
    print("Current Public IP Address is:", current_public_ip)


# Define your Email fields for the smtplib

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USERNAME
    msg['To'] = TO_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        server.send_message(msg)

#Check if the current IP is the same as the expected IP, if not equal, script exits here.

if current_public_ip != EXPECTED_PUBLIC_IP:
    subject = "Public IP Address Changed"
    body = f"The Public IP address of the server has changed to: {current_public_ip}. Please white list this new IP. The script will terminate."
    print("Oops, there is a problem")
    send_email(subject, body)
    logging.warning(f"Public IP changed : {current_public_ip}. Please white list this new IP. The script will terminate .")
    raise SystemExit   # Exit the script if the IP address has changed

# Check Connection to URLs specified above using a timeout of 15 seconds
def test_url_status(url, expected_status_code):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == expected_status_code:
            return True
        else:
            return False
    except Exception as e:
        return False

def check_services():
    for url in URLS_TO_MONITOR:
        # Callback URL expects Post requests and returns 405 on GET request.
        if "support.gravityafrica.co.ke" in url:
            expected_status_code = 405
            test_result = test_url_status(url, expected_status_code)
            if not test_result:
                subject = f"Service Alert: {url} - Failed Test for HTTP {expected_status_code}"
                body = f"The service at {url} did not return the expected HTTP {expected_status_code} status code."
                send_email(subject, body)
                logging.warning(f"Service check failed: {url} - Expected HTTP {expected_status_code} not received.")
        # Blasts Emalify URL expects Post and returns 404 on GET requests.
        elif "crm.gravityafrica.co.ke" in url:
            expected_status_code = 404
            test_result = test_url_status(url, expected_status_code)
            if not test_result:
                subject = f"Service Alert: {url} - Failed Test for HTTP {expected_status_code}"
                body = f"The service at {url} did not return the expected HTTP {expected_status_code} status code."
                send_email(subject, body)
                logging.warning(f"Service check failed: {url} - Expected HTTP {expected_status_code} not received.")
        # Other URLs expect HTTP 200 status code.
        else:
            expected_status_code = 200
            test_result = test_url_status(url, expected_status_code)
            if not test_result:
                subject = f"Service Alert: {url} - Failed Test for HTTP {expected_status_code}"
                body = f"The service at {url} did not return the expected HTTP {expected_status_code} status code."
                send_email(subject, body)
                logging.warning(f"Service check failed: {url} - Expected HTTP {expected_status_code} not received.")

if __name__ == "__main__":
    while True:
        check_services()
        time.sleep(120)  # Wait for 2 minutes before checking again

# Compress log files with gzip. 
today = datetime.now().strftime('%Y%m%d')
log_files = [f for f in os.listdir(log_directory) if f.startswith("monitor_log_") and f.endswith(".txt")]
for log_file in log_files:
    log_date = log_file.split("_")[-1].split(".")[0]
    if log_date != today:
        with open(os.path.join(log_directory, log_file), 'rb') as f_in:
            with gzip.open(os.path.join(log_directory, f"{log_file}.gz"), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(os.path.join(log_directory, log_file))

