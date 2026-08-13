import pandas as pd
from app.services.tsetmc import client
from app.services.technical_analysis import TechnicalAnalyzer
import json

def test_full_pipeline():
    symbol = "وبملت"
    print(f"Fetching history for {symbol}...")
    history = client.get_price_history(symbol, adjusted=True, force_refresh=True)
    
    if isinstance(history, dict) and "error" in history:
        print(f"Error: {history['error']}")
        return

    print(f"Fetched {len(history)} items.")
    
    # Prepare OHLCV
    ohlcv = TechnicalAnalyzer.prepare_ohlcv_data(history)
    print(f"Prepared {len(ohlcv)} OHLCV items.")
    
    # Calculate Tech Analysis
    analysis = TechnicalAnalyzer.calculate_technical_analysis(ohlcv)
    print(f"Calculated analysis. Result items: {len(analysis)}")
    
    if analysis and len(analysis) > 0:
        latest = analysis[0]
        print("Latest sample results:")
        print(json.dumps({k: latest[k] for k in ['date', 'Signal', 'Pattern', 'RSI', 'MACD', 'SMA20'] if k in latest}, indent=4, ensure_ascii=False))
        
        # Check if indicators are NaN
        nan_count = 0
        for k in ['RSI', 'MACD', 'SMA20', 'SMA50']:
            if k in latest and latest[k] is None:
                nan_count += 1
        
        if nan_count > 0:
            print(f"WARNING: Found {nan_count} indicators with None/NaN values.")
        else:
            print("Indicators calculated successfully.")
    else:
        print("Analysis returned empty results.")

if __name__ == "__main__":
    test_full_pipeline()
