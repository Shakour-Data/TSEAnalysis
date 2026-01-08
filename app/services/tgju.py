import requests
import pandas as pd
from datetime import datetime
import time
import logging
from app.core_utils import SAFE_BROWSER_UA, update_stats

logger = logging.getLogger(__name__)

class TGJUClient:
    """
    Client for fetching data from tgju.org (Tehran Gold & Jewelry Union).
    Used for: Currencies, Gold, Coins, and Global Commodities.
    """
    BASE_URL = "https://www.tgju.org/chart/realtimes/history"
    
    # Common TGJU symbols
    SYMBOLS = {
        # Currencies
        "price_dollar_rl": "دلار آمریکا (آزاد)",
        "price_eur": "یورو",
        "price_gbp": "پوند انگلیس",
        "price_aed": "درهم امارات",
        # Gold & Coins
        "gerami": "طلای ۱۸ عیار",
        "sekeb": "سکه امامی",
        "sekee": "سکه بهار آزادی",
        "nim": "نیم سکه",
        "rob": "ربع سکه",
        "gold_mini_size": "مثقال طلا",
        # Global
        "global-gold": "انس طلا (جهانی)",
        "global-silver": "انس نقره",
        "energy-brent": "نفت برنت",
        "energy-wti": "نفت WTI",
        "market-copper": "مس (جهانی)",
        "market-aluminum": "آلومینیوم",
        "market-zinc": "روی",
    }

    HEADERS = {
        "User-Agent": SAFE_BROWSER_UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.tgju.org/",
    }

    def get_history(self, symbol, from_date=None, to_date=None):
        """
        Fetches historical data for a symbol.
        Timeframe is always Daily for this API.
        """
        now = int(time.time())
        # Default to last 2 years if not specified
        start_ts = from_date if from_date else now - (730 * 24 * 3600)
        end_ts = to_date if to_date else now

        params = {
            "symbol": symbol,
            "resolution": "D",
            "from": start_ts,
            "to": end_ts
        }

        try:
            response = requests.get(self.BASE_URL, params=params, headers=self.HEADERS, timeout=15)
            update_stats("tgju", "success")
            data = response.json()
            
            if data.get('s') != 'ok':
                logger.error(f"TGJU API Error for {symbol}: {data.get('s')}")
                return {"error": f"TGJU API Error: {data.get('s')}"}

            # TGJU returns: t (time), o (open), h (high), l (low), c (close), v (volume)
            df = pd.DataFrame({
                'Date': pd.to_datetime(data['t'], unit='s').strftime('%Y-%m-%d'),
                'Open': data['o'],
                'High': data['h'],
                'Low': data['l'],
                'Close': data['c'],
                'Volume': data['v']
            })
            
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"TGJU Request failed for {symbol}: {e}")
            update_stats("tgju", "blocked")
            return {"error": str(e)}

    def get_all_symbols(self):
        """Returns a list of supported symbols for the UI."""
        return [{"id": k, "l18": v, "l30": v} for k, v in self.SYMBOLS.items()]

tgju_client = TGJUClient()
