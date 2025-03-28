import os
import sys
from datetime import datetime
from strategies.fade_strategy import FadeStrategy
from visualization.fade_visualizer import FadeVisualizer

def main():
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create strategy instance
    strategy = FadeStrategy(symbol="QQQ", lookback_days=30)
    
    try:
        # Fetch data and identify signals
        print("Fetching data...")
        strategy.fetch_data()
        
        print("Identifying signals...")
        strategy.identify_signals()
        
        # Create and save visualization
        print("Creating visualization...")
        visualizer = FadeVisualizer(strategy)
        visualizer.create_dashboard()
        visualizer.save_dashboard(output_dir)
        
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
            
        print("\nAnalysis completed successfully!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 