import sys
import os
from app import TSETMCClient, API_KEY

def get_market_counts():
    print("Using TSETMCClient from app.py (Powered by curl_cffi)...")
    client = TSETMCClient(API_KEY)
    
    # Get all potential equity symbols (Type 1)
    equity_universe = client._fetch_symbols_by_type("1")
    if isinstance(equity_universe, dict) and "error" in equity_universe:
        print(f"خطا در دریافت داده‌ها: {equity_universe['error']}")
        return
    
    if not equity_universe:
        print("هیچ داده‌ای دریافت نشد (لیست خالی).")
        return

    print(f"Total Symbols Received: {len(equity_universe)}")

    categories = {
        "bourse": "بورس تهران",
        "farabourse": "فرابورس ایران",
        "base": "بازار پایه",
        "etf": "صندوق‌های ETF",
        "fixed_income": "درآمد ثابت",
        "tashilat": "تسهیلات مسکن"
    }
    
    counts = {cat: 0 for cat in categories}
    others = 0
    
    for sym in equity_universe:
        cat = client._classify_equity_market(sym)
        if cat in counts:
            counts[cat] += 1
        else:
            others += 1
            
    print("\n--- آمار نمادها به تفکیک بازار ---")
    for cat, label in categories.items():
        print(f"{label}: {counts[cat]} نماد")
    
    if others > 0:
        print(f"سایر موارد: {others} نماد")

if __name__ == "__main__":
    get_market_counts()
