# QQQ Trading Dashboard

This project implements a trading strategy visualization dashboard for the QQQ ETF using Python. The dashboard includes technical indicators, trading signals, and performance metrics.

## Features

- Interactive candlestick chart with technical indicators
- Multiple trading signal types:
  - Mean Reversion
  - Morning Reversal
  - Evening Reversal
- Risk management with ATR-based stop loss and take profit levels
- Volume analysis
- RSI and Z-Score indicators
- Gap and reversal analysis
- Detailed strategy statistics

## Project Structure

```
.
├── src/
│   └── dashboard/
│       └── qqq_dashboard.py
├── data/
│   └── output/
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the dashboard script:
```bash
python src/dashboard/qqq_dashboard.py
```

The script will:
1. Fetch QQQ data using yfinance
2. Calculate technical indicators
3. Generate trading signals
4. Create an interactive dashboard
5. Save the dashboard as an HTML file in the data/output directory
6. Print strategy statistics to the console

## Strategy Parameters

- Initial Capital: $100,000
- Position Size: 10% of capital per trade
- Stop Loss: 2x ATR
- Take Profit: 4x ATR
- Volume Threshold: 1.5x average volume
- Volatility Threshold: 1.2x average ATR
- Z-Score Threshold: 2.0
- Lookback Period: 5 days

## Output

The dashboard is saved as an HTML file in the data/output directory with a timestamp in the filename. The file can be opened in any web browser to view the interactive charts and indicators.

## Dependencies

- pandas >= 1.5.0
- numpy >= 1.21.0
- yfinance >= 0.2.0
- plotly >= 5.13.0 