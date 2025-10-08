🚀 Live Trading Simulation / Algo Trading System
A comprehensive algorithmic trading system with backtesting, paper trading, and live data visualization.

📋 Table of Contents
Features
Tech Stack
System Architecture
Installation Guide
Database Setup
Running the Application
API Documentation
Testing
Deployment
Development Notes
✨ Features
Core Features
✅ Live & Historical Data Feeds - yfinance integration for real-time data
✅ Multiple Trading Strategies
Moving Average Crossover (SMA/EMA)
RSI Momentum Strategy
Bollinger Bands Mean Reversion
MACD Strategy
✅ Backtesting Engine - Test strategies on historical data
✅ Paper Trading - Simulate trades with virtual money
✅ Real-time Dashboard - React-based visualization with charts
✅ Database Integration - PostgreSQL/SQLite for trade logs
✅ WebSocket Support - Live data streaming
✅ REST API - Complete RESTful endpoints
Bonus Features
🎯 Risk Management (Stop Loss, Max Drawdown)
📊 Performance Metrics (Sharpe Ratio, Win Rate, Max Drawdown)
🐳 Docker Support
📈 Multiple Timeframes
💾 Trade History & Portfolio Tracking
🛠️ Tech Stack
Backend:

FastAPI (Python 3.11+)
SQLAlchemy (ORM)
PostgreSQL / SQLite
yfinance (Market Data)
Pandas & NumPy (Data Analysis)
WebSockets (Real-time updates)
Frontend:

React 18
Recharts (Visualization)
Lucide Icons
Tailwind CSS
DevOps:

Docker & Docker Compose
Uvicorn (ASGI Server)
🏗️ System Architecture
┌─────────────────────────────────────────────────────────────┐
│                     Client Browser                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │   React Dashboard (Real-time Charts & Controls)    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────┬───────────────┘
                      │                       │
                 HTTP/REST              WebSocket
                      │                       │
┌─────────────────────┴───────────────────────┴───────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Trading    │  │  Backtester  │  │  Paper Trader   │  │
│  │  Strategies  │  │    Engine    │  │     Engine      │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Database   │  │  yfinance    │  │  Risk Manager   │  │
│  │     ORM      │  │   API        │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   PostgreSQL /    │
                    │     SQLite        │
                    └───────────────────┘
📦 Installation Guide
Prerequisites
Python 3.11 or higher
pip (Python package manager)
PostgreSQL (optional, SQLite is default)
Git
Docker (optional)
Step 1: Clone the Repository
bash
git clone https://github.com/yourusername/algo-trading-system.git
cd algo-trading-system
Step 2: Create Virtual Environment
bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
Step 3: Install Dependencies
bash
pip install --upgrade pip
pip install -r requirements.txt
Step 4: Setup Environment Variables
bash
# Copy example env file
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use any text editor
🗄️ Database Setup
Option 1: SQLite (Easiest - No Setup Required)
SQLite is the default and requires no additional setup. The database file will be created automatically.

bash
# The .env file should have:
DATABASE_URL=sqlite:///./trading_system.db
Option 2: PostgreSQL (Recommended for Production)
Install PostgreSQL
On Ubuntu/Debian:

bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
On macOS:

bash
brew install postgresql
brew services start postgresql
On Windows: Download from https://www.postgresql.org/download/windows/

Create Database
bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE trading_db;
CREATE USER trading_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
\q
Update .env File
bash
DATABASE_URL=postgresql://trading_user:your_password@localhost:5432/trading_db
Initialize Database
bash
# Run database initialization
python database.py
You should see:

✓ Database tables created successfully
🚀 Running the Application
Method 1: Direct Python Execution
Start the Backend Server
bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the FastAPI server
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
You should see:

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
Access the Application
API Documentation: http://localhost:8000/docs
Alternative Docs: http://localhost:8000/redoc
Health Check: http://localhost:8000/
Method 2: Docker (Recommended)
Using Docker Compose
bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
This will start:

FastAPI backend on port 8000
PostgreSQL on port 5432
pgAdmin on port 5050 (optional)
Using Docker Only
bash
# Build image
docker build -t trading-system .

# Run container with SQLite
docker run -p 8000:8000 trading-system

# Run container with PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  trading-system
📊 Testing the System
Run Backtest Tests
bash
# Test all strategies
python test_backtest.py
This will:

Test MA Crossover strategy on AAPL
Test RSI strategy on MSFT
Test Bollinger Bands on GOOGL
Compare all strategies side-by-side
Example Output:
==================================================
Testing MA Crossover Strategy
==================================================
Fetching data for AAPL...
Running backtest...

Strategy: MA_CROSSOVER
Initial Capital: $100,000.00
Final Capital: $112,450.00
Total Return: $12,450.00 (12.45%)
Number of Trades: 8

Performance Metrics:
  total_return: 12.45
  sharpe_ratio: 1.32
  max_drawdown: -8.34
  win_rate: 62.5
  avg_trade_return: 3.2
Test API Endpoints
bash
# Test health check
curl http://localhost:8000/

# Get current price
curl http://localhost:8000/api/market/price/AAPL

# Get historical data
curl http://localhost:8000/api/market/historical/AAPL?period=1mo

# Get portfolio
curl http://localhost:8000/api/portfolio

# Get trade history
curl http://localhost:8000/api/trades
Run Backtest via API
bash
curl -X POST http://localhost:8000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "strategy": "MA_CROSSOVER",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000,
    "params": {
      "short_window": 20,
      "long_window": 50
    }
  }'
📡 API Documentation
Market Data Endpoints
Get Current Price
http
GET /api/market/price/{symbol}
Response:

json
{
  "symbol": "AAPL",
  "price": 175.43,
  "timestamp": "2024-01-15T10:30:00"
}
Get Historical Data
http
GET /api/market/historical/{symbol}?period=1mo&interval=1d
Trading Endpoints
Execute Trade
http
POST /api/trade
Content-Type: application/json

{
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 10,
  "price": 175.43
}
Get Portfolio
http
GET /api/portfolio
Response:

json
{
  "cash": 98000.00,
  "positions": {
    "AAPL": {
      "quantity": 10,
      "current_price": 175.43,
      "value": 1754.30
    }
  },
  "total_value": 99754.30,
  "pnl": -245.70,
  "pnl_percent": -0.25
}
Backtesting Endpoints
Run Backtest
http
POST /api/backtest
Content-Type: application/json

{
  "symbol": "AAPL",
  "strategy": "MA_CROSSOVER",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 100000,
  "params": {
    "short_window": 20,
    "long_window": 50
  }
}
WebSocket Endpoints
Live Price Feed
javascript
const ws = new WebSocket('ws://localhost:8000/ws/live/AAPL');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
🔍 Database Schema
Tables
trades
sql
- id: INTEGER (Primary Key)
- symbol: VARCHAR(10)
- action: VARCHAR(10) (BUY/SELL)
- quantity: INTEGER
- price: FLOAT
- total: FLOAT
- status: VARCHAR(20)
- timestamp: DATETIME
- strategy_name: VARCHAR(50)
- notes: TEXT
portfolio
sql
- id: INTEGER (Primary Key)
- cash: FLOAT
- positions: TEXT (JSON)
- total_value: FLOAT
- pnl: FLOAT
- pnl_percent: FLOAT
- timestamp: DATETIME
strategies
sql
- id: INTEGER (Primary Key)
- name: VARCHAR(50)
- symbol: VARCHAR(10)
- params: TEXT (JSON)
- enabled: BOOLEAN
- backtest_results: TEXT (JSON)
- created_at: DATETIME
- updated_at: DATETIME
Query Examples
python
from database import SessionLocal, Trade, Portfolio

# Get session
db = SessionLocal()

# Get all trades for AAPL
trades = db.query(Trade).filter(Trade.symbol == "AAPL").all()

# Get latest portfolio snapshot
portfolio = db.query(Portfolio).order_by(Portfolio.timestamp.desc()).first()

# Close session
db.close()
🚢 Deployment
Deploy to Railway
Install Railway CLI:
bash
npm install -g @railway/cli
Login and deploy:
bash
railway login
railway init
railway up
Add PostgreSQL:
bash
railway add postgresql
Deploy to Render
Create render.yaml:
yaml
services:
  - type: web
    name: trading-system
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 127.0.0.1 --port $PORT
Connect GitHub repo to Render
Deploy from dashboard
Deploy to Heroku
bash
heroku login
heroku create trading-system
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
📝 Development Notes
Development Approach
Architecture Design: Started with modular design separating concerns (strategies, backtesting, paper trading)
Database First: Designed schema to support all features before implementation
Strategy Pattern: Used abstract base class for strategies to allow easy extension
Testing: Built test script before API to validate core logic
API Layer: FastAPI for modern, async endpoints with automatic documentation
Real-time: WebSockets for live data streaming
Docker: Containerization for easy deployment
Technologies Chosen
FastAPI: Modern, fast, with automatic docs
SQLAlchemy: Database ORM supporting multiple databases
yfinance: Free market data without API keys
Pandas: Industry standard for financial data
Docker: Easy deployment and reproducibility
WebSockets: Real-time data streaming
Challenges & Learnings
Data Quality: yfinance can be unreliable; added error handling
Websocket Management: Proper connection lifecycle management
Backtesting Accuracy: Commission and slippage significantly impact results
Database Choice: SQLite for development, PostgreSQL for production
Risk Management: Stop-loss implementation requires careful state management
Future Enhancements
 Machine Learning price prediction (LSTM)
 More strategies (Pairs trading, Arbitrage)
 Real broker integration (Alpaca, Interactive Brokers)
 Advanced risk management (VaR, Kelly Criterion)
 Portfolio optimization
 Multi-asset support
 Telegram/Discord notifications
 Advanced charting (TradingView integration)
🤝 Contributing
Contributions welcome! Please:

Fork the repository
Create a feature branch
Make your changes
Add tests
Submit a pull request
📄 License
MIT License - feel free to use for learning and commercial purposes.


🎯 Quick Start Checklist
 Python 3.11+ installed
 Virtual environment created
 Dependencies installed (pip install -r requirements.txt)
 .env file configured
 Database initialized (python database.py)
 Tests passed (python test_backtest.py)
 Server running (python main.py)
 API docs accessible (http://localhost:8000/docs)
 First backtest completed
**Built with

