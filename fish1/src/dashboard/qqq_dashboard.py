import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings
warnings.filterwarnings('ignore')

# Create data directory if it doesn't exist
if not os.path.exists('../../data/output'):
    os.makedirs('../../data/output')

# Strategy Parameters
INITIAL_CAPITAL = 100000
POSITION_SIZE = 0.1  # 10% of capital per trade
STOP_LOSS_MULTIPLIER = 2  # Stop loss at 2x ATR
TAKE_PROFIT_MULTIPLIER = 4  # Take profit at 4x ATR
VOLUME_THRESHOLD = 1.5  # Minimum volume ratio for signals
VOLATILITY_THRESHOLD = 1.2  # Minimum ATR ratio for signals
ZSCORE_THRESHOLD = 2.0  # Z-score threshold for mean reversion
LOOKBACK_PERIOD = 5  # Days for z-score calculation

try:
    # Fetch QQQ data
    print("Fetching QQQ data...")
    ticker = yf.Ticker("QQQ")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)  # Increased for better z-score calculation
    data = ticker.history(start=start_date, end=end_date, interval='1d')
    data = data.reset_index()
    print("Data fetched successfully!")
except Exception as e:
    print(f"Error fetching data: {e}")
    # Create sample data for testing
    print("Creating sample data...")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    data = pd.DataFrame({
        'Date': dates,
        'Open': np.random.normal(100, 2, len(dates)),
        'High': np.random.normal(102, 2, len(dates)),
        'Low': np.random.normal(98, 2, len(dates)),
        'Close': np.random.normal(100, 2, len(dates)),
        'Volume': np.random.normal(1000000, 200000, len(dates))
    })
    print("Sample data created successfully!")

def calculate_indicators(data):
    print("Calculating technical indicators...")
    # Calculate ATR
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    data['ATR'] = tr.rolling(window=14).mean()
    
    # Calculate ATR bands
    data['ATR_Upper'] = data['Close'] + (data['ATR'] * 2)
    data['ATR_Lower'] = data['Close'] - (data['ATR'] * 2)
    
    # Calculate ATR ratio for volatility regime
    data['ATR_Ratio'] = data['ATR'] / data['ATR'].rolling(window=20).mean()
    
    # Calculate EMAs
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
    data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()
    
    # Calculate RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate volume indicators
    data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
    data['Volume_Ratio'] = data['Volume'] / data['Volume_MA']
    
    # Calculate z-scores for mean reversion
    data['Rolling_Mean'] = data['Close'].rolling(window=LOOKBACK_PERIOD).mean()
    data['Rolling_Std'] = data['Close'].rolling(window=LOOKBACK_PERIOD).std()
    data['Z_Score'] = (data['Close'] - data['Rolling_Mean']) / data['Rolling_Std']
    
    # Calculate overnight gap
    data['Overnight_Gap'] = data['Open'] - data['Close'].shift(1)
    data['Gap_Pct'] = (data['Overnight_Gap'] / data['Close'].shift(1)) * 100
    
    # Calculate morning reversal potential
    data['Morning_Reversal'] = (data['High'] - data['Open']) / data['Open'] * 100
    data['Evening_Reversal'] = (data['Close'] - data['Open']) / data['Open'] * 100
    
    print("Technical indicators calculated successfully!")
    return data

def generate_signals(data):
    print("Generating trading signals...")
    data['Signal'] = 0  # 1 for buy, -1 for sell
    data['Stop_Loss'] = 0
    data['Take_Profit'] = 0
    data['Signal_Type'] = ''  # 'Mean_Reversion', 'Morning_Reversal', 'Evening_Reversal'
    
    # Trend conditions
    uptrend = data['EMA20'] > data['EMA50']
    downtrend = data['EMA20'] < data['EMA50']
    
    # Volume conditions
    high_volume = data['Volume_Ratio'] > VOLUME_THRESHOLD
    
    # Volatility conditions
    high_volatility = data['ATR_Ratio'] > VOLATILITY_THRESHOLD
    
    # Z-score conditions
    oversold_zscore = data['Z_Score'] < -ZSCORE_THRESHOLD
    overbought_zscore = data['Z_Score'] > ZSCORE_THRESHOLD
    
    # Morning reversal conditions
    morning_reversal_buy = (data['Gap_Pct'] < -1.0) & (data['Morning_Reversal'] > 0.5)
    morning_reversal_sell = (data['Gap_Pct'] > 1.0) & (data['Morning_Reversal'] < -0.5)
    
    # Evening reversal conditions
    evening_reversal_buy = (data['Gap_Pct'] < -1.0) & (data['Evening_Reversal'] > 0.5)
    evening_reversal_sell = (data['Gap_Pct'] > 1.0) & (data['Evening_Reversal'] < -0.5)
    
    # Generate buy signals
    mean_reversion_buy = uptrend & oversold_zscore & high_volume & high_volatility
    data.loc[mean_reversion_buy, 'Signal'] = 1
    data.loc[mean_reversion_buy, 'Signal_Type'] = 'Mean_Reversion'
    data.loc[mean_reversion_buy, 'Stop_Loss'] = data.loc[mean_reversion_buy, 'Close'] - (data.loc[mean_reversion_buy, 'ATR'] * STOP_LOSS_MULTIPLIER)
    data.loc[mean_reversion_buy, 'Take_Profit'] = data.loc[mean_reversion_buy, 'Close'] + (data.loc[mean_reversion_buy, 'ATR'] * TAKE_PROFIT_MULTIPLIER)
    
    # Morning reversal buy signals
    data.loc[morning_reversal_buy, 'Signal'] = 1
    data.loc[morning_reversal_buy, 'Signal_Type'] = 'Morning_Reversal'
    data.loc[morning_reversal_buy, 'Stop_Loss'] = data.loc[morning_reversal_buy, 'Open'] - (data.loc[morning_reversal_buy, 'ATR'] * STOP_LOSS_MULTIPLIER)
    data.loc[morning_reversal_buy, 'Take_Profit'] = data.loc[morning_reversal_buy, 'Open'] + (data.loc[morning_reversal_buy, 'ATR'] * TAKE_PROFIT_MULTIPLIER)
    
    # Evening reversal buy signals
    data.loc[evening_reversal_buy, 'Signal'] = 1
    data.loc[evening_reversal_buy, 'Signal_Type'] = 'Evening_Reversal'
    data.loc[evening_reversal_buy, 'Stop_Loss'] = data.loc[evening_reversal_buy, 'Close'] - (data.loc[evening_reversal_buy, 'ATR'] * STOP_LOSS_MULTIPLIER)
    data.loc[evening_reversal_buy, 'Take_Profit'] = data.loc[evening_reversal_buy, 'Close'] + (data.loc[evening_reversal_buy, 'ATR'] * TAKE_PROFIT_MULTIPLIER)
    
    # Generate sell signals
    mean_reversion_sell = downtrend & overbought_zscore & high_volume & high_volatility
    data.loc[mean_reversion_sell, 'Signal'] = -1
    data.loc[mean_reversion_sell, 'Signal_Type'] = 'Mean_Reversion'
    data.loc[mean_reversion_sell, 'Stop_Loss'] = data.loc[mean_reversion_sell, 'Close'] + (data.loc[mean_reversion_sell, 'ATR'] * STOP_LOSS_MULTIPLIER)
    data.loc[mean_reversion_sell, 'Take_Profit'] = data.loc[mean_reversion_sell, 'Close'] - (data.loc[mean_reversion_sell, 'ATR'] * TAKE_PROFIT_MULTIPLIER)
    
    # Morning reversal sell signals
    data.loc[morning_reversal_sell, 'Signal'] = -1
    data.loc[morning_reversal_sell, 'Signal_Type'] = 'Morning_Reversal'
    data.loc[morning_reversal_sell, 'Stop_Loss'] = data.loc[morning_reversal_sell, 'Open'] + (data.loc[morning_reversal_sell, 'ATR'] * STOP_LOSS_MULTIPLIER)
    data.loc[morning_reversal_sell, 'Take_Profit'] = data.loc[morning_reversal_sell, 'Open'] - (data.loc[morning_reversal_sell, 'ATR'] * TAKE_PROFIT_MULTIPLIER)
    
    # Evening reversal sell signals
    data.loc[evening_reversal_sell, 'Signal'] = -1
    data.loc[evening_reversal_sell, 'Signal_Type'] = 'Evening_Reversal'
    data.loc[evening_reversal_sell, 'Stop_Loss'] = data.loc[evening_reversal_sell, 'Close'] + (data.loc[evening_reversal_sell, 'ATR'] * STOP_LOSS_MULTIPLIER)
    data.loc[evening_reversal_sell, 'Take_Profit'] = data.loc[evening_reversal_sell, 'Close'] - (data.loc[evening_reversal_sell, 'ATR'] * TAKE_PROFIT_MULTIPLIER)
    
    print("Trading signals generated successfully!")
    return data

print("Starting data processing...")
# Calculate indicators and generate signals
data = calculate_indicators(data)
data = generate_signals(data)

print("Creating interactive dashboard...")
# Create figure with secondary y-axis
fig = make_subplots(rows=5, cols=1, 
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    row_heights=[0.4, 0.15, 0.15, 0.15, 0.15])

# Add candlestick chart
fig.add_trace(go.Candlestick(x=data['Date'],
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close'],
                            name='QQQ'),
              row=1, col=1)

# Add EMAs
fig.add_trace(go.Scatter(x=data['Date'], y=data['EMA20'],
                        name='EMA20',
                        line=dict(color='orange', width=1)),
              row=1, col=1)
fig.add_trace(go.Scatter(x=data['Date'], y=data['EMA50'],
                        name='EMA50',
                        line=dict(color='blue', width=1)),
              row=1, col=1)

# Add ATR bands
fig.add_trace(go.Scatter(x=data['Date'], y=data['ATR_Upper'],
                        name='ATR Upper',
                        line=dict(color='gray', width=1, dash='dash'),
                        opacity=0.5),
              row=1, col=1)
fig.add_trace(go.Scatter(x=data['Date'], y=data['ATR_Lower'],
                        name='ATR Lower',
                        line=dict(color='gray', width=1, dash='dash'),
                        opacity=0.5),
              row=1, col=1)

# Add buy/sell signals
buy_signals = data[data['Signal'] == 1]
sell_signals = data[data['Signal'] == -1]

# Plot buy signals
for signal_type in ['Mean_Reversion', 'Morning_Reversal', 'Evening_Reversal']:
    type_signals = buy_signals[buy_signals['Signal_Type'] == signal_type]
    if not type_signals.empty:
        color = 'lime' if signal_type == 'Mean_Reversion' else 'cyan' if signal_type == 'Morning_Reversal' else 'magenta'
        fig.add_trace(go.Scatter(x=type_signals['Date'], y=type_signals['Close'],
                               mode='markers',
                               name=f'{signal_type} Buy',
                               marker=dict(color=color, size=10, symbol='triangle-up'),
                               showlegend=True),
                     row=1, col=1)
        
        # Add stop loss and take profit lines
        for idx, row in type_signals.iterrows():
            fig.add_trace(go.Scatter(x=[row['Date'], row['Date']],
                                   y=[row['Stop_Loss'], row['Take_Profit']],
                                   mode='lines',
                                   line=dict(color=color, width=1, dash='dash'),
                                   showlegend=False),
                         row=1, col=1)

# Plot sell signals
for signal_type in ['Mean_Reversion', 'Morning_Reversal', 'Evening_Reversal']:
    type_signals = sell_signals[sell_signals['Signal_Type'] == signal_type]
    if not type_signals.empty:
        color = 'red' if signal_type == 'Mean_Reversion' else 'orange' if signal_type == 'Morning_Reversal' else 'pink'
        fig.add_trace(go.Scatter(x=type_signals['Date'], y=type_signals['Close'],
                               mode='markers',
                               name=f'{signal_type} Sell',
                               marker=dict(color=color, size=10, symbol='triangle-down'),
                               showlegend=True),
                     row=1, col=1)
        
        # Add stop loss and take profit lines
        for idx, row in type_signals.iterrows():
            fig.add_trace(go.Scatter(x=[row['Date'], row['Date']],
                                   y=[row['Stop_Loss'], row['Take_Profit']],
                                   mode='lines',
                                   line=dict(color=color, width=1, dash='dash'),
                                   showlegend=False),
                         row=1, col=1)

# Add volume bars
fig.add_trace(go.Bar(x=data['Date'], y=data['Volume'],
                    name='Volume',
                    marker_color='gray',
                    opacity=0.5),
              row=2, col=1)
fig.add_trace(go.Scatter(x=data['Date'], y=data['Volume_MA'],
                        name='Volume MA',
                        line=dict(color='blue', width=1)),
              row=2, col=1)

# Add RSI
fig.add_trace(go.Scatter(x=data['Date'], y=data['RSI'],
                        name='RSI',
                        line=dict(color='purple', width=1)),
              row=3, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

# Add Z-Score
fig.add_trace(go.Scatter(x=data['Date'], y=data['Z_Score'],
                        name='Z-Score',
                        line=dict(color='orange', width=1)),
              row=4, col=1)
fig.add_hline(y=ZSCORE_THRESHOLD, line_dash="dash", line_color="red", row=4, col=1)
fig.add_hline(y=-ZSCORE_THRESHOLD, line_dash="dash", line_color="green", row=4, col=1)

# Add Gap and Reversal
fig.add_trace(go.Scatter(x=data['Date'], y=data['Gap_Pct'],
                        name='Overnight Gap %',
                        line=dict(color='blue', width=1)),
              row=5, col=1)
fig.add_trace(go.Scatter(x=data['Date'], y=data['Morning_Reversal'],
                        name='Morning Reversal %',
                        line=dict(color='green', width=1)),
              row=5, col=1)
fig.add_trace(go.Scatter(x=data['Date'], y=data['Evening_Reversal'],
                        name='Evening Reversal %',
                        line=dict(color='red', width=1)),
              row=5, col=1)

# Update layout
fig.update_layout(
    title='QQQ Trading Dashboard',
    xaxis_title='Date',
    yaxis_title='Price',
    yaxis2_title='Volume',
    yaxis3_title='RSI',
    yaxis4_title='Z-Score',
    yaxis5_title='Percentage',
    height=1200,
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.05
    )
)

# Update y-axes ranges
fig.update_yaxes(range=[0, 100], row=3, col=1)  # RSI range
fig.update_yaxes(title_text="Volume", row=2, col=1)
fig.update_yaxes(title_text="RSI", row=3, col=1)
fig.update_yaxes(title_text="Z-Score", row=4, col=1)
fig.update_yaxes(title_text="Percentage", row=5, col=1)

print("Saving dashboard...")
# Save the dashboard as HTML
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'../../data/output/QQQ_Dashboard_{timestamp}.html'
fig.write_html(filename)
print(f"\nDashboard has been saved as: {os.path.abspath(filename)}")

# Print strategy statistics
total_signals = len(buy_signals) + len(sell_signals)
if total_signals > 0:
    print(f"\nStrategy Statistics:")
    print(f"Total Signals: {total_signals}")
    
    for signal_type in ['Mean_Reversion', 'Morning_Reversal', 'Evening_Reversal']:
        type_buy = len(buy_signals[buy_signals['Signal_Type'] == signal_type])
        type_sell = len(sell_signals[sell_signals['Signal_Type'] == signal_type])
        print(f"\n{signal_type} Signals:")
        print(f"Buy Signals: {type_buy}")
        print(f"Sell Signals: {type_sell}")
        print(f"Signal Ratio (Buy/Sell): {type_buy/type_sell:.2f}" if type_sell > 0 else "Signal Ratio: N/A")
    
    # Calculate average ATR for risk management
    avg_atr = data['ATR'].mean()
    print(f"\nRisk Management:")
    print(f"Average ATR: ${avg_atr:.2f}")
    print(f"Stop Loss Distance: ${avg_atr * STOP_LOSS_MULTIPLIER:.2f}")
    print(f"Take Profit Distance: ${avg_atr * TAKE_PROFIT_MULTIPLIER:.2f}")
    
    # Print position sizing
    print(f"\nPosition Sizing:")
    print(f"Account Size: ${INITIAL_CAPITAL:,.2f}")
    print(f"Position Size: ${INITIAL_CAPITAL * POSITION_SIZE:,.2f} ({POSITION_SIZE * 100:.1f}% of account)")
    print(f"Risk per Trade: ${avg_atr * STOP_LOSS_MULTIPLIER * (INITIAL_CAPITAL * POSITION_SIZE / data['Close'].iloc[-1]):,.2f}")
    
    # Print volatility statistics
    high_vol_periods = len(data[data['ATR_Ratio'] > VOLATILITY_THRESHOLD])
    low_vol_periods = len(data[data['ATR_Ratio'] < 1.0])
    print(f"\nVolatility Analysis:")
    print(f"High Volatility Periods: {high_vol_periods}")
    print(f"Low Volatility Periods: {low_vol_periods}")
    print(f"Volatility Ratio Range: {data['ATR_Ratio'].min():.2f} to {data['ATR_Ratio'].max():.2f}")
    
    # Print gap and reversal statistics
    print(f"\nGap and Reversal Analysis:")
    print(f"Average Overnight Gap: {data['Gap_Pct'].mean():.2f}%")
    print(f"Average Morning Reversal: {data['Morning_Reversal'].mean():.2f}%")
    print(f"Average Evening Reversal: {data['Evening_Reversal'].mean():.2f}%")
    print(f"Largest Gap Up: {data['Gap_Pct'].max():.2f}%")
    print(f"Largest Gap Down: {data['Gap_Pct'].min():.2f}%")

print("Script completed successfully!") 