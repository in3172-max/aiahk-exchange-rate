import requests
import json
from datetime import datetime
import time
import os
import csv

def fetch_exchange_rates(api_url):
    """從AIA API取得所有外幣匯率（不變）"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.aia.com.hk/'
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API請求失敗，狀態碼：{response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 請求錯誤：{e}")
        return None

def extract_all_rates(data):
    """
    從API數據中提取所有貨幣匯率
    回傳字典: {'貨幣代碼': 匯率值}，例如 {'usd': 7.8416, 'rmb': 1.1410, ...}
    """
    rates = {}
    if not isinstance(data, list):
        print("❌ 數據格式不是預期的列表類型")
        return rates
    
    for item in data:
        if isinstance(item, dict):
            currency_type = item.get('type')
            currency_value = item.get('value')
            if currency_type and currency_value:
                try:
                    rates[currency_type] = float(currency_value)
                except (ValueError, TypeError):
                    print(f"⚠️ 警告：無法轉換 {currency_type} 的值 {currency_value} 為數字")
    return rates

def save_all_rates_to_csv(rates_dict, filename="aia_all_rates.csv"):
    """
    將所有貨幣匯率記錄到CSV（寬格式：日期,usd,rmb,eur...）
    每天一筆資料
    """
    try:
        today_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 定義所有貨幣的欄位順序（依你的API順序）
        currency_order = ['usd', 'aus', 'rmb', 'can', 'chf', 'pound', 
                          'peso', 'mop', 'nt', 'sing', 'nzd', 'euro', 'yen']
        
        file_exists = os.path.isfile(filename)
        
        # 檢查今天是否已記錄
        if file_exists:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:  # 有標題列和至少一筆資料
                    last_row = rows[-1]
                    if last_row and last_row[0] == today_date:  # 第一欄是日期
                        print(f"⚠️ 今天 ({today_date}) 的匯率已記錄過，跳過。")
                        return
        
        # 準備要寫入的資料
        header = ['日期'] + [curr.upper() for curr in currency_order]
        new_row = [today_date] + [rates_dict.get(curr, '') for curr in currency_order]
        
        # 寫入檔案
        with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(new_row)
        
        print(f"✅ 已記錄 {today_date} 的所有貨幣匯率")
        
        # 可選：同時保留一份詳細記錄檔（含時間戳）
        detailed_filename = "aia_all_rates_detailed.csv"
        with open(detailed_filename, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not os.path.isfile(detailed_filename):
                writer.writerow(['記錄時間'] + [curr.upper() for curr in currency_order])
            writer.writerow([current_time] + [rates_dict.get(curr, '') for curr in currency_order])
        
    except Exception as e:
        print(f"❌ 檔案寫入錯誤：{e}")

def main():
    api_url = "https://www1.aia.com.hk/CorpWS/Investment/Get/ExchangeRate2"
    
    print("正在從AIA API取得匯率...")
    raw_data = fetch_exchange_rates(api_url)
    
    if raw_data:
        all_rates = extract_all_rates(raw_data)
        if all_rates:
            save_all_rates_to_csv(all_rates)
            # 印出部分結果供確認
            print("今日匯率摘要：")
            for key in ['usd', 'rmb', 'euro', 'yen']:
                if key in all_rates:
                    print(f"  {key.upper()}: {all_rates[key]}")
        else:
            print("❌ 無法提取匯率數據")
            # 儲存除錯資訊
            with open("debug_api_response.json", "w", encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            print("🔍 已將原始API回應儲存至 debug_api_response.json")
    else:
        print("❌ 無法取得API數據")
    
    time.sleep(1)

if __name__ == "__main__":
    main()