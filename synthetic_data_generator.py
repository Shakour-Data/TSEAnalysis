"
# Synthetic Market Data Generator
# Creates realistic OHLCV data for testing technical indicators
""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SyntheticDataGenerator:
    ""
    Generates synthetic OHLCV data with realistic patterns
    """

    def __init__(self, symbols: List[str] = ['TSM1', 'TSM2'], days: int = 365,
                 base_price: float = 1000, volatility: float = 0.02)
        self.symbols = symbols
        self.days = days
        self.base_price = base_price
        self.volatility = volatility

    def generate_data(self) -> Dict[str, pd.DataFrame]:
        """
        Returns dictionary of synthetic OHLCV dataframes
        """
        data = {}
        for symbol in self.symbols:
            df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            current_price = self.base_price
            for i in range(self.days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                # Generate true price movement
                movement = np.random.normal(0, self.volatility)
                current_price *= (1 + movement)
                
                # Calculate OHLC prices
                open_price = current_price * (1 + np.random.normal(0, 0.005))
                high_price = current_price * (1 + np.random.normal(0, 0.01))
                low_price = current_price * (1 - np.random.normal(0, 0.01))
                close_price = current_price * (1 + np.random.normal(0, 0.005))
                
                # Volume with random spikes
                volume = np.random.randint(100000, 1000000 + i*1000)
                
                df = df.append({
                    'date': date,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                }, ignore_index=True)
            data[symbol] = df.sort_values('date')
        return data

# Generate synthetic data for testing
synthetic_data = SyntheticDataGenerator(days=365).generate_data()

# Save to CSV for reference
for symbol, df in synthetic_data.items():
    df.to_csv(f'E:\Shakour\MyAnalysis\TSEAnalysis\synthetic_data\{symbol}.csv', index=False)