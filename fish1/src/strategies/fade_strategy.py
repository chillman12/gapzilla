import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings
warnings.filterwarnings('ignore')

class FadeStrategy:
    def __init__(self, symbol="QQQ", lookback_days=30):
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.data = None
        self.signals = []

    def fetch_data(self):
        """Fetch historical data for the symbol"""
        try:
            ticker = yf.Ticker(self.symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            self.data = ticker.history(start=start_date, end=end_date, interval='1d')
            self.data = self.data.reset_index()
            print(f"Successfully fetched {len(self.data)} days of data for {self.symbol}")
        except Exception as e:
            print(f"Error fetching data: {e}")
            raise

    def calculate_indicators(self):
        """Calculate technical indicators for fade strategies"""
        if self.data is None:
            raise ValueError("Data not fetched. Call fetch_data() first.")

        # Calculate overnight gap
        self.data['Overnight_Gap'] = self.data['Open'] - self.data['Close'].shift(1)
        self.data['Gap_Pct'] = (self.data['Overnight_Gap'] / self.data['Close'].shift(1)) * 100

        # Calculate first hour movement
        self.data['First_Hour_Move'] = (self.data['High'] - self.data['Open']) / self.data['Open'] * 100
        self.data['First_Hour_Direction'] = np.where(self.data['First_Hour_Move'] > 0, 1, -1)

        # Calculate extreme moves
        self.data['Extreme_Move'] = abs(self.data['First_Hour_Move']) >= 1.0

        # Calculate ATR for volatility
        high = self.data['High']
        low = self.data['Low']
        close = self.data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        self.data['ATR'] = tr.rolling(window=14).mean()

    def identify_signals(self):
        """Identify trading signals based on fade strategies"""
        if self.data is None:
            raise ValueError("Data not fetched. Call fetch_data() first.")

        self.calculate_indicators()
        self.signals = []

        # First Hour Fade Strategy
        for i in range(1, len(self.data)):
            if self.data['First_Hour_Direction'].iloc[i] == 1:  # Up move
                self.signals.append({
                    'date': self.data['Date'].iloc[i],
                    'type': 'SELL',
                    'price': self.data['Close'].iloc[i],
                    'strategy': 'First Hour Fade',
                    'reason': 'First hour up move fade'
                })
            elif self.data['First_Hour_Direction'].iloc[i] == -1:  # Down move
                self.signals.append({
                    'date': self.data['Date'].iloc[i],
                    'type': 'BUY',
                    'price': self.data['Close'].iloc[i],
                    'strategy': 'First Hour Fade',
                    'reason': 'First hour down move fade'
                })

        # Gap Fade Strategy
        for i in range(1, len(self.data)):
            if self.data['Gap_Pct'].iloc[i] > 1.0:  # Gap up
                self.signals.append({
                    'date': self.data['Date'].iloc[i],
                    'type': 'SELL',
                    'price': self.data['Open'].iloc[i],
                    'strategy': 'Gap Fade',
                    'reason': 'Gap up fade'
                })
            elif self.data['Gap_Pct'].iloc[i] < -1.0:  # Gap down
                self.signals.append({
                    'date': self.data['Date'].iloc[i],
                    'type': 'BUY',
                    'price': self.data['Open'].iloc[i],
                    'strategy': 'Gap Fade',
                    'reason': 'Gap down fade'
                })

        # Extreme Moves Fade Strategy
        for i in range(1, len(self.data)):
            if self.data['Extreme_Move'].iloc[i]:
                if self.data['First_Hour_Move'].iloc[i] > 0:  # Extreme up move
                    self.signals.append({
                        'date': self.data['Date'].iloc[i],
                        'type': 'SELL',
                        'price': self.data['Close'].iloc[i],
                        'strategy': 'Extreme Move Fade',
                        'reason': 'Extreme up move fade'
                    })
                else:  # Extreme down move
                    self.signals.append({
                        'date': self.data['Date'].iloc[i],
                        'type': 'BUY',
                        'price': self.data['Close'].iloc[i],
                        'strategy': 'Extreme Move Fade',
                        'reason': 'Extreme down move fade'
                    })

        return self.signals

    def get_statistics(self):
        """Calculate strategy statistics"""
        if not self.signals:
            return "No signals generated yet."

        stats = {
            'total_signals': len(self.signals),
            'buy_signals': len([s for s in self.signals if s['type'] == 'BUY']),
            'sell_signals': len([s for s in self.signals if s['type'] == 'SELL']),
            'strategies': {}
        }

        for strategy in ['First Hour Fade', 'Gap Fade', 'Extreme Move Fade']:
            strategy_signals = [s for s in self.signals if s['strategy'] == strategy]
            stats['strategies'][strategy] = {
                'total': len(strategy_signals),
                'buy': len([s for s in strategy_signals if s['type'] == 'BUY']),
                'sell': len([s for s in strategy_signals if s['type'] == 'SELL'])
            }

        return stats 