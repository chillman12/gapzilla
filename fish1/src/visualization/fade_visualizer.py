import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
from datetime import datetime
from ..strategies.fade_strategy import FadeStrategy

class FadeVisualizer:
    def __init__(self, strategy):
        self.strategy = strategy
        self.fig = None

    def create_dashboard(self):
        """Create an interactive dashboard for fade strategy visualization"""
        if self.strategy.data is None:
            raise ValueError("Strategy data not initialized. Run fetch_data() first.")

        # Create figure with secondary y-axis
        self.fig = make_subplots(rows=4, cols=1, 
                               shared_xaxes=True,
                               vertical_spacing=0.05,
                               row_heights=[0.4, 0.2, 0.2, 0.2])

        # Add candlestick chart
        self.fig.add_trace(go.Candlestick(x=self.strategy.data['Date'],
                                        open=self.strategy.data['Open'],
                                        high=self.strategy.data['High'],
                                        low=self.strategy.data['Low'],
                                        close=self.strategy.data['Close'],
                                        name=self.strategy.symbol),
                          row=1, col=1)

        # Add buy/sell signals
        buy_signals = [s for s in self.strategy.signals if s['type'] == 'BUY']
        sell_signals = [s for s in self.strategy.signals if s['type'] == 'SELL']

        # Plot buy signals
        for strategy in ['First Hour Fade', 'Gap Fade', 'Extreme Move Fade']:
            strategy_buys = [s for s in buy_signals if s['strategy'] == strategy]
            if strategy_buys:
                color = 'lime' if strategy == 'First Hour Fade' else 'cyan' if strategy == 'Gap Fade' else 'magenta'
                self.fig.add_trace(go.Scatter(x=[s['date'] for s in strategy_buys],
                                           y=[s['price'] for s in strategy_buys],
                                           mode='markers',
                                           name=f'{strategy} Buy',
                                           marker=dict(color=color, size=10, symbol='triangle-up'),
                                           showlegend=True),
                                 row=1, col=1)

        # Plot sell signals
        for strategy in ['First Hour Fade', 'Gap Fade', 'Extreme Move Fade']:
            strategy_sells = [s for s in sell_signals if s['strategy'] == strategy]
            if strategy_sells:
                color = 'red' if strategy == 'First Hour Fade' else 'orange' if strategy == 'Gap Fade' else 'pink'
                self.fig.add_trace(go.Scatter(x=[s['date'] for s in strategy_sells],
                                           y=[s['price'] for s in strategy_sells],
                                           mode='markers',
                                           name=f'{strategy} Sell',
                                           marker=dict(color=color, size=10, symbol='triangle-down'),
                                           showlegend=True),
                                 row=1, col=1)

        # Add gap percentage
        self.fig.add_trace(go.Scatter(x=self.strategy.data['Date'],
                                    y=self.strategy.data['Gap_Pct'],
                                    name='Overnight Gap %',
                                    line=dict(color='blue', width=1)),
                          row=2, col=1)

        # Add first hour movement
        self.fig.add_trace(go.Scatter(x=self.strategy.data['Date'],
                                    y=self.strategy.data['First_Hour_Move'],
                                    name='First Hour Move %',
                                    line=dict(color='green', width=1)),
                          row=3, col=1)

        # Add ATR
        self.fig.add_trace(go.Scatter(x=self.strategy.data['Date'],
                                    y=self.strategy.data['ATR'],
                                    name='ATR',
                                    line=dict(color='purple', width=1)),
                          row=4, col=1)

        # Update layout
        self.fig.update_layout(
            title=f'{self.strategy.symbol} Fade Trading Signals',
            xaxis_title='Date',
            yaxis_title='Price',
            yaxis2_title='Gap %',
            yaxis3_title='First Hour Move %',
            yaxis4_title='ATR',
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
        self.fig.update_yaxes(title_text="Price", row=1, col=1)
        self.fig.update_yaxes(title_text="Gap %", row=2, col=1)
        self.fig.update_yaxes(title_text="First Hour Move %", row=3, col=1)
        self.fig.update_yaxes(title_text="ATR", row=4, col=1)

    def save_dashboard(self, output_dir='../../data/output'):
        """Save the dashboard as an HTML file"""
        if self.fig is None:
            raise ValueError("Dashboard not created. Run create_dashboard() first.")

        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save the dashboard
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'{self.strategy.symbol}_Fade_Dashboard_{timestamp}.html')
        self.fig.write_html(filename)
        print(f"\nDashboard has been saved as: {os.path.abspath(filename)}")

def main():
    # Create strategy instance
    strategy = FadeStrategy(symbol="QQQ", lookback_days=30)
    
    # Fetch data and identify signals
    strategy.fetch_data()
    strategy.identify_signals()
    
    # Create and save visualization
    visualizer = FadeVisualizer(strategy)
    visualizer.create_dashboard()
    visualizer.save_dashboard()
    
    # Print statistics
    stats = strategy.get_statistics()
    print("\nStrategy Statistics:")
    print(f"Total Signals: {stats['total_signals']}")
    print(f"Buy Signals: {stats['buy_signals']}")
    print(f"Sell Signals: {stats['sell_signals']}")
    
    print("\nSignals by Strategy:")
    for strategy_name, strategy_stats in stats['strategies'].items():
        print(f"\n{strategy_name}:")
        print(f"Total: {strategy_stats['total']}")
        print(f"Buy: {strategy_stats['buy']}")
        print(f"Sell: {strategy_stats['sell']}")

if __name__ == "__main__":
    main() 