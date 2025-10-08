import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, Bar, BarChart } from 'recharts';
import { TrendingUp, TrendingDown, Activity, DollarSign, Target, AlertCircle } from 'lucide-react';

const TradingDashboard = () => {
  const [priceData, setPriceData] = useState([]);
  const [trades, setTrades] = useState([]);
  const [portfolio, setPortfolio] = useState({
    cash: 100000,
    positions: {},
    totalValue: 100000,
    pnl: 0,
    trades: 0
  });
  const [selectedStrategy, setSelectedStrategy] = useState('sma_cross');
  const [isLive, setIsLive] = useState(false);
  const [indicators, setIndicators] = useState({});

  // Generate initial historical data
  useEffect(() => {
    const generateHistoricalData = () => {
      const data = [];
      let price = 100;
      const now = Date.now();
      
      for (let i = 100; i >= 0; i--) {
        const timestamp = now - i * 60000; // 1 minute intervals
        price += (Math.random() - 0.48) * 2;
        price = Math.max(50, Math.min(150, price));
        
        data.push({
          timestamp,
          time: new Date(timestamp).toLocaleTimeString(),
          price: parseFloat(price.toFixed(2)),
          volume: Math.floor(Math.random() * 10000) + 5000
        });
      }
      
      return data;
    };

    const initialData = generateHistoricalData();
    setPriceData(initialData);
    calculateIndicators(initialData);
    runBacktest(initialData);
  }, []);

  // Calculate technical indicators
  const calculateIndicators = (data) => {
    if (data.length < 50) return;

    const prices = data.map(d => d.price);
    const sma20 = calculateSMA(prices, 20);
    const sma50 = calculateSMA(prices, 50);
    const rsi = calculateRSI(prices, 14);
    const bb = calculateBollingerBands(prices, 20);

    const newIndicators = data.map((item, i) => ({
      ...item,
      sma20: sma20[i],
      sma50: sma50[i],
      rsi: rsi[i],
      bbUpper: bb.upper[i],
      bbMiddle: bb.middle[i],
      bbLower: bb.lower[i]
    }));

    setPriceData(newIndicators);
    setIndicators({
      currentRSI: rsi[rsi.length - 1],
      currentSMA20: sma20[sma20.length - 1],
      currentSMA50: sma50[sma50.length - 1]
    });
  };

  const calculateSMA = (prices, period) => {
    const sma = [];
    for (let i = 0; i < prices.length; i++) {
      if (i < period - 1) {
        sma.push(null);
      } else {
        const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        sma.push(parseFloat((sum / period).toFixed(2)));
      }
    }
    return sma;
  };

  const calculateRSI = (prices, period = 14) => {
    const rsi = [];
    const gains = [];
    const losses = [];

    for (let i = 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? -change : 0);
    }

    for (let i = 0; i < prices.length; i++) {
      if (i < period) {
        rsi.push(null);
      } else {
        const avgGain = gains.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
        const avgLoss = losses.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
        const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
        rsi.push(parseFloat((100 - (100 / (1 + rs))).toFixed(2)));
      }
    }

    return rsi;
  };

  const calculateBollingerBands = (prices, period = 20) => {
    const sma = calculateSMA(prices, period);
    const upper = [];
    const middle = [];
    const lower = [];

    for (let i = 0; i < prices.length; i++) {
      if (i < period - 1 || !sma[i]) {
        upper.push(null);
        middle.push(null);
        lower.push(null);
      } else {
        const slice = prices.slice(i - period + 1, i + 1);
        const std = Math.sqrt(
          slice.reduce((sum, val) => sum + Math.pow(val - sma[i], 2), 0) / period
        );
        upper.push(parseFloat((sma[i] + 2 * std).toFixed(2)));
        middle.push(sma[i]);
        lower.push(parseFloat((sma[i] - 2 * std).toFixed(2)));
      }
    }

    return { upper, middle, lower };
  };

  // Strategy implementations
  const generateSignals = (data, strategy) => {
    const signals = [];
    
    for (let i = 1; i < data.length; i++) {
      const current = data[i];
      const previous = data[i - 1];

      if (strategy === 'sma_cross' && current.sma20 && current.sma50) {
        if (previous.sma20 <= previous.sma50 && current.sma20 > current.sma50) {
          signals.push({ ...current, signal: 'BUY', index: i });
        } else if (previous.sma20 >= previous.sma50 && current.sma20 < current.sma50) {
          signals.push({ ...current, signal: 'SELL', index: i });
        }
      } else if (strategy === 'rsi' && current.rsi) {
        if (previous.rsi <= 30 && current.rsi > 30) {
          signals.push({ ...current, signal: 'BUY', index: i });
        } else if (previous.rsi >= 70 && current.rsi < 70) {
          signals.push({ ...current, signal: 'SELL', index: i });
        }
      } else if (strategy === 'bollinger' && current.bbLower && current.bbUpper) {
        if (previous.price <= previous.bbLower && current.price > current.bbLower) {
          signals.push({ ...current, signal: 'BUY', index: i });
        } else if (previous.price >= previous.bbUpper && current.price < current.bbUpper) {
          signals.push({ ...current, signal: 'SELL', index: i });
        }
      }
    }

    return signals;
  };

  // Backtesting engine
  const runBacktest = (data) => {
    let cash = 100000;
    let position = 0;
    let entryPrice = 0;
    const tradeLog = [];
    let totalTrades = 0;

    const signals = generateSignals(data, selectedStrategy);

    signals.forEach(signal => {
      if (signal.signal === 'BUY' && position === 0) {
        const shares = Math.floor(cash / signal.price);
        if (shares > 0) {
          position = shares;
          entryPrice = signal.price;
          cash -= shares * signal.price;
          totalTrades++;
          tradeLog.push({
            type: 'BUY',
            price: signal.price,
            time: signal.time,
            shares,
            value: shares * signal.price
          });
        }
      } else if (signal.signal === 'SELL' && position > 0) {
        const saleValue = position * signal.price;
        const profit = (signal.price - entryPrice) * position;
        cash += saleValue;
        tradeLog.push({
          type: 'SELL',
          price: signal.price,
          time: signal.time,
          shares: position,
          value: saleValue,
          profit: parseFloat(profit.toFixed(2))
        });
        position = 0;
        entryPrice = 0;
        totalTrades++;
      }
    });

    const finalValue = cash + (position * data[data.length - 1].price);
    const totalPnL = finalValue - 100000;

    setPortfolio({
      cash: parseFloat(cash.toFixed(2)),
      positions: position > 0 ? { shares: position, entryPrice } : {},
      totalValue: parseFloat(finalValue.toFixed(2)),
      pnl: parseFloat(totalPnL.toFixed(2)),
      trades: totalTrades
    });

    setTrades(tradeLog);
  };

  // Live trading simulation
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      setPriceData(prev => {
        const lastPrice = prev[prev.length - 1].price;
        const newPrice = lastPrice + (Math.random() - 0.48) * 2;
        const bounded = Math.max(50, Math.min(150, parseFloat(newPrice.toFixed(2))));
        
        const newData = [...prev.slice(-100), {
          timestamp: Date.now(),
          time: new Date().toLocaleTimeString(),
          price: bounded,
          volume: Math.floor(Math.random() * 10000) + 5000
        }];

        calculateIndicators(newData);
        return newData;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isLive]);

  const currentPrice = priceData[priceData.length - 1]?.price || 0;
  const priceChange = priceData.length > 1 
    ? priceData[priceData.length - 1].price - priceData[priceData.length - 2].price 
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Live Trading Simulation
          </h1>
          <p className="text-gray-400">Real-time algorithmic trading dashboard with multiple strategies</p>
        </div>

        {/* Control Panel */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6 flex flex-wrap gap-4 items-center border border-gray-700">
          <div>
            <label className="text-sm text-gray-400 block mb-1">Strategy</label>
            <select 
              value={selectedStrategy}
              onChange={(e) => {
                setSelectedStrategy(e.target.value);
                runBacktest(priceData);
              }}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="sma_cross">SMA Crossover</option>
              <option value="rsi">RSI Momentum</option>
              <option value="bollinger">Bollinger Bands</option>
            </select>
          </div>
          
          <button
            onClick={() => setIsLive(!isLive)}
            className={`px-6 py-2 rounded font-semibold transition-all ${
              isLive 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {isLive ? 'Stop Live Feed' : 'Start Live Feed'}
          </button>

          <button
            onClick={() => runBacktest(priceData)}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold transition-all"
          >
            Run Backtest
          </button>

          {isLive && (
            <div className="flex items-center gap-2 ml-auto">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-400 font-semibold">LIVE</span>
            </div>
          )}
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg p-4 border border-blue-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-100 text-sm">Current Price</span>
              <DollarSign className="w-5 h-5 text-blue-200" />
            </div>
            <div className="text-2xl font-bold">${currentPrice.toFixed(2)}</div>
            <div className={`text-sm flex items-center gap-1 ${priceChange >= 0 ? 'text-green-300' : 'text-red-300'}`}>
              {priceChange >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-lg p-4 border border-green-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-green-100 text-sm">Total P&L</span>
              <Activity className="w-5 h-5 text-green-200" />
            </div>
            <div className="text-2xl font-bold">${portfolio.pnl.toFixed(2)}</div>
            <div className={`text-sm ${portfolio.pnl >= 0 ? 'text-green-300' : 'text-red-300'}`}>
              {((portfolio.pnl / 100000) * 100).toFixed(2)}% return
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg p-4 border border-purple-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-purple-100 text-sm">Portfolio Value</span>
              <Target className="w-5 h-5 text-purple-200" />
            </div>
            <div className="text-2xl font-bold">${portfolio.totalValue.toFixed(2)}</div>
            <div className="text-sm text-purple-300">Cash: ${portfolio.cash.toFixed(2)}</div>
          </div>

          <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-lg p-4 border border-orange-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-orange-100 text-sm">Total Trades</span>
              <AlertCircle className="w-5 h-5 text-orange-200" />
            </div>
            <div className="text-2xl font-bold">{portfolio.trades}</div>
            <div className="text-sm text-orange-300">
              {portfolio.positions.shares ? `Position: ${portfolio.positions.shares} shares` : 'No open position'}
            </div>
          </div>
        </div>

        {/* Price Chart with Indicators */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
          <h2 className="text-xl font-bold mb-4">Price Chart with Strategy Signals</h2>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={priceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" domain={['auto', 'auto']} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#9CA3AF' }}
              />
              <Legend />
              <Line type="monotone" dataKey="price" stroke="#3B82F6" strokeWidth={2} dot={false} name="Price" />
              {selectedStrategy === 'sma_cross' && (
                <>
                  <Line type="monotone" dataKey="sma20" stroke="#10B981" strokeWidth={1} dot={false} name="SMA 20" />
                  <Line type="monotone" dataKey="sma50" stroke="#F59E0B" strokeWidth={1} dot={false} name="SMA 50" />
                </>
              )}
              {selectedStrategy === 'bollinger' && (
                <>
                  <Line type="monotone" dataKey="bbUpper" stroke="#EF4444" strokeWidth={1} dot={false} name="BB Upper" strokeDasharray="3 3" />
                  <Line type="monotone" dataKey="bbMiddle" stroke="#8B5CF6" strokeWidth={1} dot={false} name="BB Middle" />
                  <Line type="monotone" dataKey="bbLower" stroke="#EF4444" strokeWidth={1} dot={false} name="BB Lower" strokeDasharray="3 3" />
                </>
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* RSI Indicator */}
        {selectedStrategy === 'rsi' && indicators.currentRSI && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
            <h2 className="text-xl font-bold mb-4">RSI Indicator</h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                  labelStyle={{ color: '#9CA3AF' }}
                />
                <Line type="monotone" dataKey="rsi" stroke="#8B5CF6" strokeWidth={2} dot={false} name="RSI" />
                <Line type="monotone" dataKey={() => 70} stroke="#EF4444" strokeWidth={1} strokeDasharray="3 3" name="Overbought" />
                <Line type="monotone" dataKey={() => 30} stroke="#10B981" strokeWidth={1} strokeDasharray="3 3" name="Oversold" />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-4 text-center">
              <span className="text-gray-400">Current RSI: </span>
              <span className={`font-bold text-lg ${
                indicators.currentRSI > 70 ? 'text-red-400' :
                indicators.currentRSI < 30 ? 'text-green-400' :
                'text-yellow-400'
              }`}>
                {indicators.currentRSI.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {/* Trade History */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold mb-4">Trade History</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2 px-4 text-gray-400">Type</th>
                  <th className="text-left py-2 px-4 text-gray-400">Time</th>
                  <th className="text-left py-2 px-4 text-gray-400">Price</th>
                  <th className="text-left py-2 px-4 text-gray-400">Shares</th>
                  <th className="text-left py-2 px-4 text-gray-400">Value</th>
                  <th className="text-left py-2 px-4 text-gray-400">P&L</th>
                </tr>
              </thead>
              <tbody>
                {trades.slice(-10).reverse().map((trade, idx) => (
                  <tr key={idx} className="border-b border-gray-700 hover:bg-gray-750">
                    <td className="py-2 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        trade.type === 'BUY' ? 'bg-green-600' : 'bg-red-600'
                      }`}>
                        {trade.type}
                      </span>
                    </td>
                    <td className="py-2 px-4 text-sm">{trade.time}</td>
                    <td className="py-2 px-4">${trade.price.toFixed(2)}</td>
                    <td className="py-2 px-4">{trade.shares}</td>
                    <td className="py-2 px-4">${trade.value.toFixed(2)}</td>
                    <td className={`py-2 px-4 font-semibold ${
                      trade.profit > 0 ? 'text-green-400' :
                      trade.profit < 0 ? 'text-red-400' :
                      'text-gray-400'
                    }`}>
                      {trade.profit ? `$${trade.profit.toFixed(2)}` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard;