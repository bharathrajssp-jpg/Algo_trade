"""
Risk Management Module
Implements stop-loss, take-profit, position sizing, and drawdown limits
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

class RiskManager:
    def __init__(
        self,
        initial_capital: float = 100000,
        max_position_size: float = 0.2,  # 20% of portfolio
        stop_loss_pct: float = 0.05,      # 5% stop loss
        take_profit_pct: float = 0.10,    # 10% take profit
        max_drawdown_pct: float = 0.20    # 20% max drawdown
    ):
        self.initial_capital = initial_capital
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        
        self.peak_value = initial_capital
        self.current_drawdown = 0
    
    def calculate_position_size(
        self,
        current_capital: float,
        current_price: float,
        volatility: Optional[float] = None
    ) -> int:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            current_capital: Available capital
            current_price: Current asset price
            volatility: Asset volatility (optional, for Kelly Criterion)
        
        Returns:
            Number of shares to buy
        """
        # Basic position sizing (percentage of portfolio)
        max_investment = current_capital * self.max_position_size
        shares = int(max_investment / current_price)
        
        # Adjust for volatility if provided (simplified Kelly Criterion)
        if volatility and volatility > 0:
            kelly_fraction = min(0.25, 1 / volatility)  # Cap at 25%
            shares = int(shares * kelly_fraction)
        
        return max(0, shares)
    
    def check_stop_loss(
        self,
        entry_price: float,
        current_price: float
    ) -> bool:
        """Check if stop loss is triggered"""
        loss_pct = (entry_price - current_price) / entry_price
        return loss_pct >= self.stop_loss_pct
    
    def check_take_profit(
        self,
        entry_price: float,
        current_price: float
    ) -> bool:
        """Check if take profit is triggered"""
        profit_pct = (current_price - entry_price) / entry_price
        return profit_pct >= self.take_profit_pct
    
    def update_drawdown(self, current_value: float) -> Dict:
        """
        Update and check maximum drawdown
        
        Returns:
            Dictionary with drawdown info and trading halt status
        """
        # Update peak
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        # Calculate current drawdown
        self.current_drawdown = (self.peak_value - current_value) / self.peak_value
        
        # Check if max drawdown exceeded
        halt_trading = self.current_drawdown >= self.max_drawdown_pct
        
        return {
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown_pct,
            'peak_value': self.peak_value,
            'halt_trading': halt_trading
        }
    
    def calculate_risk_reward_ratio(
        self,
        entry_price: float,
        target_price: float,
        stop_loss_price: float
    ) -> float:
        """Calculate risk/reward ratio"""
        potential_profit = target_price - entry_price
        potential_loss = entry_price - stop_loss_price
        
        if potential_loss <= 0:
            return 0
        
        return potential_profit / potential_loss
    
    def should_enter_trade(
        self,
        current_capital: float,
        entry_price: float,
        target_price: float
    ) -> Dict:
        """
        Determine if trade should be entered based on risk parameters
        
        Returns:
            Dictionary with decision and reasoning
        """
        # Calculate stop loss and take profit prices
        stop_loss_price = entry_price * (1 - self.stop_loss_pct)
        
        # Check drawdown
        drawdown_info = self.update_drawdown(current_capital)
        if drawdown_info['halt_trading']:
            return {
                'enter': False,
                'reason': 'Maximum drawdown exceeded',
                'drawdown': drawdown_info['current_drawdown']
            }
        
        # Calculate risk/reward
        risk_reward = self.calculate_risk_reward_ratio(
            entry_price,
            target_price,
            stop_loss_price
        )
        
        # Require at least 2:1 risk/reward ratio
        if risk_reward < 2.0:
            return {
                'enter': False,
                'reason': f'Poor risk/reward ratio: {risk_reward:.2f}',
                'risk_reward': risk_reward
            }
        
        # Calculate position size
        position_size = self.calculate_position_size(current_capital, entry_price)
        
        if position_size == 0:
            return {
                'enter': False,
                'reason': 'Insufficient capital for position',
                'required': entry_price
            }
        
        return {
            'enter': True,
            'position_size': position_size,
            'stop_loss_price': stop_loss_price,
            'risk_reward': risk_reward,
            'max_loss': position_size * entry_price * self.stop_loss_pct
        }


class AdvancedRiskMetrics:
    """Calculate advanced risk metrics for portfolio analysis"""
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR)"""
        var = AdvancedRiskMetrics.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Sortino Ratio (downside risk adjusted return)"""
        excess_returns = returns - risk_free_rate / periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return 0
        
        downside_std = np.sqrt(np.mean(downside_returns ** 2))
        
        if downside_std == 0:
            return 0
        
        return (excess_returns.mean() / downside_std) * np.sqrt(periods_per_year)
    
    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Calmar Ratio (return / max drawdown)"""
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        if max_drawdown == 0:
            return 0
        
        annualized_return = (cumulative_returns.iloc[-1] ** (periods_per_year / len(returns))) - 1
        return annualized_return / max_drawdown
    
    @staticmethod
    def calculate_beta(
        asset_returns: pd.Series,
        market_returns: pd.Series
    ) -> float:
        """Calculate Beta (systematic risk)"""
        covariance = np.cov(asset_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 0
        
        return covariance / market_variance
    
    @staticmethod
    def calculate_information_ratio(
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """Calculate Information Ratio"""
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = active_returns.std()
        
        if tracking_error == 0:
            return 0
        
        return active_returns.mean() / tracking_error


def apply_risk_management(
    trades: list,
    prices: pd.DataFrame,
    risk_manager: RiskManager
) -> list:
    """
    Apply risk management rules to a list of trades
    
    Args:
        trades: List of trade signals
        prices: DataFrame with price data
        risk_manager: RiskManager instance
    
    Returns:
        Filtered list of trades with risk management applied
    """
    managed_trades = []
    current_position = None
    
    for trade in trades:
        if trade['type'] == 'BUY':
            # Check if we should enter
            target_price = trade['price'] * (1 + risk_manager.take_profit_pct)
            decision = risk_manager.should_enter_trade(
                trade.get('available_capital', 100000),
                trade['price'],
                target_price
            )
            
            if decision['enter']:
                trade['position_size'] = decision['position_size']
                trade['stop_loss_price'] = decision['stop_loss_price']
                trade['risk_reward'] = decision['risk_reward']
                managed_trades.append(trade)
                current_position = trade
        
        elif trade['type'] == 'SELL' and current_position:
            # Check stop loss and take profit
            if risk_manager.check_stop_loss(current_position['price'], trade['price']):
                trade['exit_reason'] = 'stop_loss'
            elif risk_manager.check_take_profit(current_position['price'], trade['price']):
                trade['exit_reason'] = 'take_profit'
            else:
                trade['exit_reason'] = 'signal'
            
            managed_trades.append(trade)
            current_position = None
    
    return managed_trades