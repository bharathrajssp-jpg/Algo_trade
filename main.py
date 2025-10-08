"""
Live Trading Simulation / Algo Trading System
FastAPI Backend with SQLite Database
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
import sqlite3
from pydantic import BaseModel
import ta
from contextlib import asynccontextmanager

# Database initialization
def init_db():
    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy TEXT NOT NULL,
            symbol TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            price REAL NOT NULL,
            shares INTEGER NOT NULL,
            value REAL NOT NULL,
            profit REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cash REAL NOT NULL,
            total_value REAL NOT NULL,
            pnl REAL NOT NULL,
            strategy TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy TEXT NOT NULL,
            symbol TEXT NOT NULL,
            initial_capital REAL NOT NULL,
            final_value REAL NOT NULL,
            total_return REAL NOT NULL,
            total_trades INTEGER NOT NULL,
            win_rate REAL,
            max_drawdown REAL,
            sharpe_ratio REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            parameters TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Algo Trading API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TradeRequest(BaseModel):
    symbol: str
    strategy: str
    trade_type: str
    price: float
    shares: int

class BacktestRequest(BaseModel):
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float = 100000
    parameters: Optional[Dict] = None

class StrategyConfig(BaseModel):
    strategy: str
    parameters: Dict

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Trading Strategies
class TradingStrategy:
    """Base class for trading strategies"""
    
    @staticmethod
    def sma_crossover(data: pd.DataFrame, short_window=20, long_window=50):
        """Simple Moving Average Crossover Strategy"""
        data['SMA_short'] = data['Close'].rolling(window=short_window).mean()
        data['SMA_long'] = data['Close'].rolling(window=long_window).mean()
        
        data['Signal'] = 0
        data.loc[data['SMA_short'] > data['SMA_long'], 'Signal'] = 1
        data.loc[data['SMA_short'] < data['SMA_long'], 'Signal'] = -1
        data['Position'] = data['Signal'].diff()
        
        return data
    
    @staticmethod
    def rsi_strategy(data: pd.DataFrame, period=14, oversold=30, overbought=70):
        """RSI Momentum Strategy"""
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=period).rsi()
        
        data['Signal'] = 0
        data.loc[data['RSI'] < oversold, 'Signal'] = 1  # Buy
        data.loc[data['RSI'] > overbought, 'Signal'] = -1  # Sell
        data['Position'] = data['Signal'].diff()
        
        return data
    
    @staticmethod
    def bollinger_bands(data: pd.DataFrame, period=20, std_dev=2):
        """Bollinger Bands Mean Reversion Strategy"""
        bb = ta.volatility.BollingerBands(data['Close'], window=period, window_dev=std_dev)
        data['BB_upper'] = bb.bollinger_hband()
        data['BB_middle'] = bb.bollinger_mavg()
        data['BB_lower'] = bb.bollinger_lband()
        
        data['Signal'] = 0
        data.loc[data['Close'] < data['BB_lower'], 'Signal'] = 1  # Buy
        data.loc[data['Close'] > data['BB_upper'], 'Signal'] = -1  # Sell
        data['Position'] = data['Signal'].diff()
        
        return data
    
    @staticmethod
    def macd_strategy(data: pd.DataFrame):
        """MACD Strategy"""
        macd = ta.trend.MACD(data['Close'])
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()
        data['MACD_diff'] = macd.macd_diff()
        
        data['Signal'] = 0
        data.loc[data['MACD'] > data['MACD_signal'], 'Signal'] = 1
        data.loc[data['MACD'] < data['MACD_signal'], 'Signal'] = -1
        data['Position'] = data['Signal'].diff()
        
        return data

# Backtesting Engine
class Backtester:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        
    def run(self, data: pd.DataFrame, strategy: str, params: dict = None):
        """Run backtest on historical data"""
        self.cash = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        
        # Apply strategy
        if strategy == 'sma_cross':
            data = TradingStrategy.sma_crossover(data, **params) if params else TradingStrategy.sma_crossover(data)
        elif strategy == 'rsi':
            data = TradingStrategy.rsi_strategy(data, **params) if params else TradingStrategy.rsi_strategy(data)
        elif strategy == 'bollinger':
            data = TradingStrategy.bollinger_bands(data, **params) if params else TradingStrategy.bollinger_bands(data)
        elif strategy == 'macd':
            data = TradingStrategy.macd_strategy(data)
        
        # Execute trades
        for i in range(len(data)):
            if pd.isna(data['Position'].iloc[i]):
                continue
                
            current_price = data['Close'].iloc[i]
            
            # Buy signal
            if data['Position'].iloc[i] == 2 and self.position == 0:
                shares = int(self.cash / current_price)
                if shares > 0:
                    self.position = shares
                    cost = shares * current_price
                    self.cash -= cost
                    self.trades.append({
                        'type': 'BUY',
                        'price': current_price,
                        'shares': shares,
                        'value': cost,
                        'date': data.index[i]
                    })
            
            # Sell signal
            elif data['Position'].iloc[i] == -2 and self.position > 0:
                value = self.position * current_price
                profit = value - (self.trades[-1]['value'] if self.trades else 0)
                self.cash += value
                self.trades.append({
                    'type': 'SELL',
                    'price': current_price,
                    'shares': self.position,
                    'value': value,
                    'profit': profit,
                    'date': data.index[i]
                })
                self.position = 0
            
            # Track equity
            total_value = self.cash + (self.position * current_price)
            self.equity_curve.append({
                'date': data.index[i],
                'value': total_value
            })
        
        # Calculate metrics
        final_value = self.cash + (self.position * data['Close'].iloc[-1])
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        winning_trades = [t for t in self.trades if t['type'] == 'SELL' and t.get('profit', 0) > 0]
        win_rate = (len(winning_trades) / len([t for t in self.trades if t['type'] == 'SELL'])) * 100 if self.trades else 0
        
        # Calculate max drawdown
        equity_values = [e['value'] for e in self.equity_curve]
        max_drawdown = 0
        peak = equity_values[0]
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate Sharpe ratio
        returns = pd.Series(equity_values).pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 0 and returns.std() > 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Algo Trading API",
        "version": "1.0.0",
        "endpoints": [
            "/api/historical/{symbol}",
            "/api/backtest",
            "/api/trades",
            "/api/portfolio",
            "/ws/live"
        ]
    }

@app.get("/api/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d"
):
    """Fetch historical data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            raise HTTPException(status_code=404, detail="No data found for symbol")
        
        # Convert to JSON-friendly format
        data.reset_index(inplace=True)
        data['Date'] = data['Date'].astype(str)
        
        return {
            "symbol": symbol,
            "data": data.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtest on historical data"""
    try:
        # Fetch data
        ticker = yf.Ticker(request.symbol)
        data = ticker.history(start=request.start_date, end=request.end_date)
        
        if data.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Run backtest
        backtester = Backtester(request.initial_capital)
        results = backtester.run(data, request.strategy, request.parameters)
        
        # Save to database
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO backtest_results 
            (strategy, symbol, initial_capital, final_value, total_return, 
             total_trades, win_rate, max_drawdown, sharpe_ratio, parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.strategy,
            request.symbol,
            results['initial_capital'],
            results['final_value'],
            results['total_return'],
            results['total_trades'],
            results['win_rate'],
            results['max_drawdown'],
            results['sharpe_ratio'],
            json.dumps(request.parameters) if request.parameters else None
        ))
        conn.commit()
        conn.close()
        
        # Format dates for JSON
        for trade in results['trades']:
            trade['date'] = str(trade['date'])
        for point in results['equity_curve']:
            point['date'] = str(point['date'])
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trades")
async def log_trade(trade: TradeRequest):
    """Log a trade to database"""
    try:
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        
        value = trade.price * trade.shares
        
        cursor.execute('''
            INSERT INTO trades (strategy, symbol, trade_type, price, shares, value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (trade.strategy, trade.symbol, trade.trade_type, trade.price, trade.shares, value))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": trade_id, "message": "Trade logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades")
async def get_trades(strategy: Optional[str] = None, limit: int = 100):
    """Get trade history"""
    try:
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        
        if strategy:
            cursor.execute('''
                SELECT * FROM trades 
                WHERE strategy = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (strategy, limit))
        else:
            cursor.execute('''
                SELECT * FROM trades 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        trades = cursor.fetchall()
        conn.close()
        
        return {
            "trades": [
                {
                    "id": t[0],
                    "strategy": t[1],
                    "symbol": t[2],
                    "trade_type": t[3],
                    "price": t[4],
                    "shares": t[5],
                    "value": t[6],
                    "profit": t[7],
                    "timestamp": t[8]
                } for t in trades
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    try:
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM portfolio 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        portfolio = cursor.fetchone()
        conn.close()
        
        if portfolio:
            return {
                "cash": portfolio[1],
                "total_value": portfolio[2],
                "pnl": portfolio[3],
                "strategy": portfolio[4],
                "timestamp": portfolio[5]
            }
        else:
            return {
                "cash": 100000,
                "total_value": 100000,
                "pnl": 0,
                "strategy": None,
                "timestamp": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio")
async def update_portfolio(
    cash: float,
    total_value: float,
    pnl: float,
    strategy: str
):
    """Update portfolio status"""
    try:
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO portfolio (cash, total_value, pnl, strategy)
            VALUES (?, ?, ?, ?)
        ''', (cash, total_value, pnl, strategy))
        
        conn.commit()
        conn.close()
        
        return {"message": "Portfolio updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest/results")
async def get_backtest_results(limit: int = 10):
    """Get historical backtest results"""
    try:
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM backtest_results 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return {
            "results": [
                {
                    "id": r[0],
                    "strategy": r[1],
                    "symbol": r[2],
                    "initial_capital": r[3],
                    "final_value": r[4],
                    "total_return": r[5],
                    "total_trades": r[6],
                    "win_rate": r[7],
                    "max_drawdown": r[8],
                    "sharpe_ratio": r[9],
                    "timestamp": r[10],
                    "parameters": json.loads(r[11]) if r[11] else None
                } for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for live data streaming
@app.websocket("/ws/live/{symbol}")
async def websocket_live_data(websocket: WebSocket, symbol: str):
    """Stream live price data via WebSocket"""
    await manager.connect(websocket)
    try:
        while True:
            # Fetch current price
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                latest = data.iloc[-1]
                message = {
                    "symbol": symbol,
                    "price": float(latest['Close']),
                    "volume": int(latest['Volume']),
                    "timestamp": datetime.now().isoformat()
                }
                await manager.broadcast(message)
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)