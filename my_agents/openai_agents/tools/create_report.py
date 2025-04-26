import datetime
import json
import os
import time
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


def get_account_reports(token):
    base_url = "https://api.mercadopago.com/v1/account/settlement_report/list"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{base_url}", headers=headers)
    return response.content


def get_report(token, report_name):
    base_url = "https://api.mercadopago.com/v1/account/release_report/"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{base_url}{report_name}", headers=headers)
    return response.content


def get_reports(token):
    base_url = "https://api.mercadopago.com/v1/account/release_report/list"
    headers = {"accept": "application/json", "Authorization": f"Bearer {token}"}

    response = requests.get(base_url, headers=headers)
    return response.content


def download_last_report(token, folder_path=None):
    if folder_path == None:
        folder_path = ""

    reports = get_reports(token).decode("utf-8")
    reports = json.loads(reports)
    df = pd.DataFrame(reports)

    if df.empty:
        print("No reports found to download.")
        return

    print(f"Downloading report {df['file_name'][0]}...")

    last_report = get_report(token, df["file_name"][0]).decode("utf-8")
    data = pd.read_csv(StringIO(last_report))

    data.to_csv(os.path.join(folder_path, df["file_name"][0]), index=False)


def create_report(token, start_date, end_date):
    url = "https://api.mercadopago.com/v1/account/release_report"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"begin_date": start_date, "end_date": end_date}

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 202:
        data = response.json()
        print(f"Report request accepted from {start_date} to {end_date}")
        if "file_url" in data:
            print(f"🔗 Download URL: {data['file_url']}")
        return data
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


def main():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=env_path)

    access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
    folder_path = os.getenv("FOLDER_PATH")
    # API accepts maximun to get data for a whole month
    start_date = (datetime.today().replace(day=1) - timedelta(days=1)).strftime(
        "%Y-%m-%dT00:00:00Z"
    )
    end_date = datetime.today().strftime("%Y-%m-%dT00:00:00Z")

    create_report(access_token, start_date, end_date)

    print("Waiting 3 minutes for the report to be generated...")
    time.sleep(180)

    download_last_report(access_token, folder_path)


if __name__ == "__main__":
    main()
