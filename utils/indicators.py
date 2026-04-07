import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

class TechnicalIndicators:
    """Calculate various technical indicators for stock analysis"""
    
    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame, windows: list = [5, 10, 20, 50, 200]) -> pd.DataFrame:
        """Calculate Simple Moving Averages (SMA)"""
        df = df.copy()
        for window in windows:
            df[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()
        return df
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, windows: list = [9, 12, 26, 50]) -> pd.DataFrame:
        """Calculate Exponential Moving Averages (EMA)"""
        df = df.copy()
        for window in windows:
            df[f'EMA_{window}'] = df['Close'].ewm(span=window, adjust=False).mean()
        return df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Relative Strength Index (RSI)"""
        df = df.copy()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        df = df.copy()
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        return df
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df = df.copy()
        df['BB_Middle'] = df['Close'].rolling(window=period).mean()
        bb_std = df['Close'].rolling(window=period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * std_dev)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * std_dev)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        return df
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """Calculate Stochastic Oscillator"""
        df = df.copy()
        low_min = df['Low'].rolling(window=k_period).min()
        high_max = df['High'].rolling(window=k_period).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()
        return df
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Average True Range (ATR) for volatility"""
        df = df.copy()
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(window=period).mean()
        return df
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate On-Balance Volume (OBV)"""
        df = df.copy()
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        return df
    
    @staticmethod
    def calculate_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Ichimoku Cloud components"""
        df = df.copy()
        # Tenkan-sen (Conversion Line)
        period_9_high = df['High'].rolling(window=9).max()
        period_9_low = df['Low'].rolling(window=9).min()
        df['Ichimoku_Tenkan'] = (period_9_high + period_9_low) / 2
        
        # Kijun-sen (Base Line)
        period_26_high = df['High'].rolling(window=26).max()
        period_26_low = df['Low'].rolling(window=26).min()
        df['Ichimoku_Kijun'] = (period_26_high + period_26_low) / 2
        
        # Senkou Span A (Leading Span A)
        df['Ichimoku_Senkou_A'] = ((df['Ichimoku_Tenkan'] + df['Ichimoku_Kijun']) / 2).shift(26)
        
        # Senkou Span B (Leading Span B)
        period_52_high = df['High'].rolling(window=52).max()
        period_52_low = df['Low'].rolling(window=52).min()
        df['Ichimoku_Senkou_B'] = ((period_52_high + period_52_low) / 2).shift(26)
        
        # Chikou Span (Lagging Span)
        df['Ichimoku_Chikou'] = df['Close'].shift(-26)
        
        return df
    
    @staticmethod
    def calculate_fibonacci(df: pd.DataFrame) -> Dict:
        """Calculate Fibonacci retracement levels"""
        max_price = df['High'].max()
        min_price = df['Low'].min()
        diff = max_price - min_price
        
        return {
            'max': max_price,
            'min': min_price,
            'fib_236': max_price - diff * 0.236,
            'fib_382': max_price - diff * 0.382,
            'fib_500': max_price - diff * 0.5,
            'fib_618': max_price - diff * 0.618,
            'fib_786': max_price - diff * 0.786
        }
    
    @staticmethod
    def calculate_pivot_points(df: pd.DataFrame) -> Dict:
        """Calculate pivot points for support and resistance"""
        last_day = df.iloc[-1]
        high = last_day['High']
        low = last_day['Low']
        close = last_day['Close']
        
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'resistance_1': r1,
            'resistance_2': r2,
            'resistance_3': r3,
            'support_1': s1,
            'support_2': s2,
            'support_3': s3
        }
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators at once"""
        df = df.copy()
        
        # Apply all calculations
        df = TechnicalIndicators.calculate_moving_averages(df)
        df = TechnicalIndicators.calculate_ema(df)
        df = TechnicalIndicators.calculate_rsi(df)
        df = TechnicalIndicators.calculate_macd(df)
        df = TechnicalIndicators.calculate_bollinger_bands(df)
        df = TechnicalIndicators.calculate_stochastic(df)
        df = TechnicalIndicators.calculate_atr(df)
        df = TechnicalIndicators.calculate_obv(df)
        
        return df
    
    @staticmethod
    def get_trading_signals(df: pd.DataFrame) -> Dict:
        """Generate trading signals based on multiple indicators"""
        signals = []
        confidence = 0
        
        # RSI signals
        latest_rsi = df['RSI'].iloc[-1]
        if latest_rsi < 30:
            signals.append(('BUY', 'RSI Oversold', 0.8))
            confidence += 0.2
        elif latest_rsi > 70:
            signals.append(('SELL', 'RSI Overbought', 0.8))
            confidence -= 0.2
        
        # MACD signals
        latest_macd = df['MACD'].iloc[-1]
        latest_signal = df['MACD_Signal'].iloc[-1]
        prev_macd = df['MACD'].iloc[-2]
        prev_signal = df['MACD_Signal'].iloc[-2]
        
        if latest_macd > latest_signal and prev_macd <= prev_signal:
            signals.append(('BUY', 'MACD Bullish Crossover', 0.7))
            confidence += 0.15
        elif latest_macd < latest_signal and prev_macd >= prev_signal:
            signals.append(('SELL', 'MACD Bearish Crossover', 0.7))
            confidence -= 0.15
        
        # Moving Average signals
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            signals.append(('BUY', 'Golden Cross Setup', 0.75))
            confidence += 0.15
        elif current_price < sma_20 < sma_50:
            signals.append(('SELL', 'Death Cross Setup', 0.75))
            confidence -= 0.15
        
        # Bollinger Bands signals
        bb_lower = df['BB_Lower'].iloc[-1]
        bb_upper = df['BB_Upper'].iloc[-1]
        
        if current_price <= bb_lower:
            signals.append(('BUY', 'Price at Lower Band', 0.6))
            confidence += 0.1
        elif current_price >= bb_upper:
            signals.append(('SELL', 'Price at Upper Band', 0.6))
            confidence -= 0.1
        
        # Determine overall signal
        if confidence > 0.3:
            overall = 'STRONG BUY' if confidence > 0.5 else 'BUY'
        elif confidence < -0.3:
            overall = 'STRONG SELL' if confidence < -0.5 else 'SELL'
        else:
            overall = 'NEUTRAL'
        
        return {
            'overall_signal': overall,
            'confidence': abs(confidence),
            'individual_signals': signals,
            'signal_count': len(signals)
        }
    
    @staticmethod
    def calculate_risk_metrics(df: pd.DataFrame) -> Dict:
        """Calculate risk metrics for portfolio analysis"""
        returns = df['Close'].pct_change().dropna()
        
        # Annualized metrics (252 trading days)
        annual_return = returns.mean() * 252 * 100
        annual_volatility = returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (annual_return / annual_volatility) if annual_volatility != 0 else 0
        
        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) * 100
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) * 100
        sortino_ratio = (annual_return / downside_deviation) if downside_deviation != 0 else 0
        
        # Calmar Ratio
        calmar_ratio = (annual_return / abs(max_drawdown)) if max_drawdown != 0 else 0
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio
        }