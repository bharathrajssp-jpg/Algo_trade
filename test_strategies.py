"""
Test script for trading strategies
Run this to validate strategies and generate sample data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import TradingStrategy, Backtester
    from risk_manager import RiskManager, apply_risk_management
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure main.py and risk_manager.py are in the same directory")
    sys.exit(1)


def test_strategy(symbol='AAPL', strategy='sma_cross', with_risk_mgmt=False):
    """Test a trading strategy on historical data"""
    
    print(f"\n{'='*70}")
    print(f"Testing {strategy.upper()} Strategy on {symbol}")
    if with_risk_mgmt:
        print(f"With Risk Management Enabled")
    print(f"{'='*70}\n")
    
    # Fetch data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    
    if data.empty:
        print(f"Error: No data found for {symbol}")
        return None
    
    print(f"Data fetched: {len(data)} rows")
    print(f"Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}\n")
    
    # Run backtest
    backtester = Backtester(initial_capital=100000)
    results = backtester.run(data, strategy)
    
    # Apply risk management if requested
    if with_risk_mgmt and results['trades']:
        risk_manager = RiskManager(
            initial_capital=100000,
            max_position_size=0.2,
            stop_loss_pct=0.05,
            take_profit_pct=0.10,
            max_drawdown_pct=0.20
        )
        
        managed_trades = apply_risk_management(
            results['trades'],
            data,
            risk_manager
        )
        
        print(f"Risk Management Applied:")
        print(f"  Original trades: {len(results['trades'])}")
        print(f"  Managed trades: {len(managed_trades)}")
        print()
    
    # Print results
    print(f"{'BACKTEST RESULTS':^70}")
    print(f"{'-'*70}")
    print(f"Initial Capital:     ${results['initial_capital']:>15,.2f}")
    print(f"Final Value:         ${results['final_value']:>15,.2f}")
    print(f"Total Return:        {results['total_return']:>15.2f}%")
    print(f"Total Trades:        {results['total_trades']:>15}")
    print(f"Win Rate:            {results['win_rate']:>15.2f}%")
    print(f"Max Drawdown:        {results['max_drawdown']:>15.2f}%")
    print(f"Sharpe Ratio:        {results['sharpe_ratio']:>15.2f}")
    print(f"{'-'*70}\n")
    
    # Show recent trades
    if results['trades']:
        print(f"{'RECENT TRADES (Last 10)':^70}")
        print(f"{'-'*70}")
        print(f"{'Type':<6} {'Date':<12} {'Price':>10} {'Shares':>8} {'Value':>12} {'Profit':>12}")
        print(f"{'-'*70}")
        
        for trade in results['trades'][-10:]:
            date_str = str(trade['date'])[:10] if 'date' in trade else 'N/A'
            profit_str = f"${trade.get('profit', 0):,.2f}" if 'profit' in trade else '-'
            
            print(f"{trade['type']:<6} {date_str:<12} "
                  f"${trade['price']:>9.2f} {trade['shares']:>8} "
                  f"${trade['value']:>11,.2f} {profit_str:>12}")
        
        print(f"{'-'*70}\n")
    
    # Equity curve summary
    if results['equity_curve']:
        print(f"{'EQUITY CURVE SUMMARY':^70}")
        print(f"{'-'*70}")
        
        equity_values = [e['value'] for e in results['equity_curve']]
        
        print(f"Starting Equity:     ${equity_values[0]:>15,.2f}")
        print(f"Peak Equity:         ${max(equity_values):>15,.2f}")
        print(f"Final Equity:        ${equity_values[-1]:>15,.2f}")
        print(f"Lowest Point:        ${min(equity_values):>15,.2f}")
        print(f"{'-'*70}\n")
    
    return results


def compare_strategies(symbol='AAPL'):
    """Compare all strategies on the same symbol"""
    
    strategies = ['sma_cross', 'rsi', 'bollinger', 'macd']
    results_summary = []
    
    print(f"\n{'='*70}")
    print(f"STRATEGY COMPARISON FOR {symbol}")
    print(f"{'='*70}\n")
    
    for strategy in strategies:
        print(f"Running {strategy}...")
        try:
            results = test_strategy(symbol, strategy, with_risk_mgmt=False)
            if results:
                results_summary.append({
                    'Strategy': strategy.upper(),
                    'Return': f"{results['total_return']:.2f}%",
                    'Trades': results['total_trades'],
                    'Win Rate': f"{results['win_rate']:.2f}%",
                    'Sharpe': f"{results['sharpe_ratio']:.2f}",
                    'Max DD': f"{results['max_drawdown']:.2f}%"
                })
        except Exception as e:
            print(f"Error testing {strategy}: {e}\n")
    
    # Print comparison table
    if results_summary:
        print(f"\n{'STRATEGY COMPARISON SUMMARY':^70}")
        print(f"{'='*70}")
        print(f"{'Strategy':<15} {'Return':>12} {'Trades':>8} {'Win Rate':>10} {'Sharpe':>8} {'Max DD':>10}")
        print(f"{'-'*70}")
        
        for result in results_summary:
            print(f"{result['Strategy']:<15} {result['Return']:>12} "
                  f"{result['Trades']:>8} {result['Win Rate']:>10} "
                  f"{result['Sharpe']:>8} {result['Max DD']:>10}")
        
        print(f"{'='*70}\n")


def test_multiple_symbols():
    """Test best strategy on multiple symbols"""
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    strategy = 'sma_cross'  # Use SMA as default
    
    print(f"\n{'='*70}")
    print(f"MULTI-SYMBOL TEST - {strategy.upper()} Strategy")
    print(f"{'='*70}\n")
    
    results_summary = []
    
    for symbol in symbols:
        print(f"Testing {symbol}...")
        try:
            results = test_strategy(symbol, strategy, with_risk_mgmt=False)
            if results:
                results_summary.append({
                    'Symbol': symbol,
                    'Return': f"{results['total_return']:.2f}%",
                    'Trades': results['total_trades'],
                    'Win Rate': f"{results['win_rate']:.2f}%",
                    'Final Value': f"${results['final_value']:,.2f}"
                })
        except Exception as e:
            print(f"Error testing {symbol}: {e}\n")
    
    # Print comparison table
    if results_summary:
        print(f"\n{'MULTI-SYMBOL COMPARISON':^70}")
        print(f"{'='*70}")
        print(f"{'Symbol':<10} {'Return':>12} {'Trades':>8} {'Win Rate':>10} {'Final Value':>15}")
        print(f"{'-'*70}")
        
        for result in results_summary:
            print(f"{result['Symbol']:<10} {result['Return']:>12} "
                  f"{result['Trades']:>8} {result['Win Rate']:>10} "
                  f"{result['Final Value']:>15}")
        
        print(f"{'='*70}\n")


def run_interactive_test():
    """Interactive mode for testing"""
    
    print("\n" + "="*70)
    print(" "*20 + "ALGO TRADING STRATEGY TESTER")
    print("="*70 + "\n")
    
    print("Select test mode:")
    print("1. Test single strategy on one symbol")
    print("2. Compare all strategies on one symbol")
    print("3. Test one strategy on multiple symbols")
    print("4. Quick demo (AAPL with all strategies)")
    print("5. Exit\n")
    
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == '1':
        symbol = input("\nEnter symbol (default: AAPL): ").strip().upper() or 'AAPL'
        print("\nAvailable strategies:")
        print("  1. sma_cross (SMA Crossover)")
        print("  2. rsi (RSI Momentum)")
        print("  3. bollinger (Bollinger Bands)")
        print("  4. macd (MACD)")
        
        strategy_choice = input("\nEnter strategy number (1-4): ").strip()
        strategies = ['sma_cross', 'rsi', 'bollinger', 'macd']
        strategy = strategies[int(strategy_choice) - 1] if strategy_choice in ['1','2','3','4'] else 'sma_cross'
        
        risk_mgmt = input("\nApply risk management? (y/n): ").strip().lower() == 'y'
        
        test_strategy(symbol, strategy, with_risk_mgmt=risk_mgmt)
    
    elif choice == '2':
        symbol = input("\nEnter symbol (default: AAPL): ").strip().upper() or 'AAPL'
        compare_strategies(symbol)
    
    elif choice == '3':
        symbols_input = input("\nEnter symbols (comma-separated, default: AAPL,MSFT,GOOGL): ").strip()
        if symbols_input:
            symbols = [s.strip().upper() for s in symbols_input.split(',')]
        else:
            symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        strategy = input("\nEnter strategy (default: sma_cross): ").strip() or 'sma_cross'
        
        for symbol in symbols:
            test_strategy(symbol, strategy, with_risk_mgmt=False)
    
    elif choice == '4':
        compare_strategies('AAPL')
    
    elif choice == '5':
        print("\nExiting... Happy trading! 📈\n")
        return
    
    else:
        print("\nInvalid choice. Please run again.\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Algo Trading Strategy Tester')
    parser.add_argument('--symbol', type=str, default='AAPL', help='Stock symbol')
    parser.add_argument('--strategy', type=str, default='sma_cross', 
                       choices=['sma_cross', 'rsi', 'bollinger', 'macd'],
                       help='Trading strategy')
    parser.add_argument('--compare', action='store_true', help='Compare all strategies')
    parser.add_argument('--multi', action='store_true', help='Test multiple symbols')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--risk-mgmt', action='store_true', help='Enable risk management')
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            run_interactive_test()
        elif args.compare:
            compare_strategies(args.symbol)
        elif args.multi:
            test_multiple_symbols()
        else:
            test_strategy(args.symbol, args.strategy, with_risk_mgmt=args.risk_mgmt)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...\n")
    except Exception as e:
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()