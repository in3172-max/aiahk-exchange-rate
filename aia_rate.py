import requests
import json
from datetime import datetime
import time
import os
import csv

# ================== 匯率相關函數 (原有) ==================
def fetch_exchange_rates(api_url):
    """從AIA API取得所有外幣匯率"""
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
            print(f"❌ 匯率API請求失敗，狀態碼：{response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 匯率請求錯誤：{e}")
        return None

def extract_all_rates(data):
    """從API數據中提取所有貨幣匯率"""
    rates = {}
    if not isinstance(data, list):
        print("❌ 匯率數據格式不是預期的列表類型")
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
    """將所有貨幣匯率記錄到CSV（寬格式：日期,usd,rmb,eur...）"""
    try:
        today_date = datetime.now().strftime("%Y-%m-%d")
        currency_order = ['usd', 'aus', 'rmb', 'can', 'chf', 'pound', 
                          'peso', 'mop', 'nt', 'sing', 'nzd', 'euro', 'yen']
        file_exists = os.path.isfile(filename)
        if file_exists:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:
                    last_row = rows[-1]
                    if last_row and last_row[0] == today_date:
                        print(f"⚠️ 今天 ({today_date}) 的匯率已記錄過，跳過。")
                        return
        header = ['日期'] + [curr.upper() for curr in currency_order]
        new_row = [today_date] + [rates_dict.get(curr, '') for curr in currency_order]
        with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(new_row)
        print(f"✅ 已記錄 {today_date} 的所有貨幣匯率")
        # === 已移除 detailed 檔案的寫入 ===
    except Exception as e:
        print(f"❌ 匯率檔案寫入錯誤：{e}")

# ================== 基金相關函數 (修改) ==================
def fetch_fund_data(api_base_url, fund_code, fund_cat="TMP2"):
    """呼叫基金API取得特定基金的數據"""
    full_url = f"{api_base_url}?fund_code={fund_code}&fund_cat={fund_cat}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.aia.com.hk/'
    }
    try:
        response = requests.get(full_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 基金 {fund_code} API請求失敗，狀態碼：{response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 基金 {fund_code} 請求錯誤：{e}")
        return None

def extract_latest_fund_price(data, fund_code):
    """從基金API數據中提取最新一筆的價格"""
    if not isinstance(data, list) or len(data) == 0:
        print(f"❌ 基金 {fund_code} 數據格式錯誤或為空")
        return None, None
    latest = data[-1]
    if len(latest) >= 2:
        try:
            timestamp_ms = latest[0]
            price = float(latest[1])
            date_obj = datetime.fromtimestamp(timestamp_ms / 1000.0)
            date_str = date_obj.strftime("%Y-%m-%d")
            return date_str, price
        except (ValueError, IndexError) as e:
            print(f"❌ 基金 {fund_code} 解析價格時出錯：{e}")
            return None, None
    else:
        print(f"❌ 基金 {fund_code} 數據格式不完整")
        return None, None

def save_fund_price_to_csv(date_str, price, fund_code, filename_prefix="aia_fund"):
    """將單一基金的價格記錄到獨立的 CSV 檔案（只保留日期與價格）"""
    filename = f"{filename_prefix}_{fund_code}.csv"
    file_exists = os.path.isfile(filename)

    # 檢查今天是否已記錄（避免重複）
    if file_exists:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) > 1:  # 有標題列和至少一筆資料
                last_row = rows[-1]
                if len(last_row) >= 1 and last_row[0] == date_str:
                    print(f"⚠️ 基金 {fund_code} 日期 {date_str} 的價格已記錄過，跳過")
                    return

    # 寫入新記錄（不再包含記錄時間）
    with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['日期', '價格'])  # 標題列簡化
        writer.writerow([date_str, price])

    print(f"✅ 基金 {fund_code} 於 {date_str} 的價格：{price} 已記錄至 {filename}")

def process_all_funds(fund_list, fund_cat="TMP2"):
    """處理多個基金，依次抓取並儲存"""
    api_base_url = "https://www1.aia.com.hk/CorpWS/Investment/Get/FundChart/"
    print("\n開始抓取多檔基金數據...")
    for fund_code in fund_list:
        print(f"\n--- 正在處理基金 {fund_code} ---")
        raw_data = fetch_fund_data(api_base_url, fund_code, fund_cat)
        if raw_data:
            date_str, price = extract_latest_fund_price(raw_data, fund_code)
            if date_str and price is not None:
                save_fund_price_to_csv(date_str, price, fund_code)
            else:
                print(f"❌ 無法提取基金 {fund_code} 的價格")
        else:
            print(f"❌ 無法取得基金 {fund_code} 的API數據")
        time.sleep(1)
    print("\n所有基金處理完畢！")

# ================== 主程式 ==================
def main():
    # 1. 抓取匯率
    print("=" * 40)
    print("開始抓取匯率數據")
    print("=" * 40)
    rate_api_url = "https://www1.aia.com.hk/CorpWS/Investment/Get/ExchangeRate2"
    rate_data = fetch_exchange_rates(rate_api_url)
    if rate_data:
        all_rates = extract_all_rates(rate_data)
        if all_rates:
            save_all_rates_to_csv(all_rates)
            # 顯示摘要
            print("今日匯率摘要：")
            for key in ['usd', 'rmb', 'euro', 'yen']:
                if key in all_rates:
                    print(f"  {key.upper()}: {all_rates[key]}")
        else:
            print("❌ 無法提取匯率數據")
            with open("debug_exchange_api.json", "w", encoding='utf-8') as f:
                json.dump(rate_data, f, ensure_ascii=False, indent=2)
            print("🔍 已將原始API回應儲存至 debug_exchange_api.json")
    else:
        print("❌ 無法取得匯率API數據")

    # 2. 抓取多檔基金
    print("\n" + "=" * 40)
    print("開始抓取基金數據")
    print("=" * 40)
    fund_codes = ["Z15", "Z20", "Z29"]  # 可在此增減基金代碼
    process_all_funds(fund_codes)

    print("\n所有任務完成！")

if __name__ == "__main__":
    main()
