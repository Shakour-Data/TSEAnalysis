import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import db
import random
from datetime import datetime, timedelta

def add_mock_history():
    symbols = db.get_all_symbols()[:10]  # First 10 symbols
    base_date = datetime.now() - timedelta(days=100)

    for symbol_data in symbols:
        symbol = symbol_data['l18']
        print(f"Adding mock history for {symbol}")

        # Generate 50 days of mock data
        for i in range(50):
            date = base_date + timedelta(days=i)
            price = random.uniform(1000, 5000)
            volume = random.randint(10000, 1000000)

            mock_data = {
                'date': date.strftime('%Y-%m-%d'),
                'open': price * random.uniform(0.95, 1.05),
                'high': price * random.uniform(1.0, 1.1),
                'low': price * random.uniform(0.9, 1.0),
                'close': price,
                'vol': volume,
                'val': price * volume
            }

            db.save_history(symbol, [mock_data])

    print("Mock data added successfully")

if __name__ == "__main__":
    add_mock_history()
