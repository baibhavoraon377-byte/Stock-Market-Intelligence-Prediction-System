import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import streamlit as st

class StockDataFetcher:
    """Handle all yfinance data fetching operations"""
    
    def __init__(self):
        self.cache_duration = 60  # Cache duration in seconds
        self.rate_limit_delay = 0.5  # Delay between API calls
        
    @st.cache_data(ttl=60)
    def get_live_price(_self, symbol: str) -> Optional[float]:
        """Fetch current live price for a stock"""
        try:
            stock = yf.Ticker(symbol)
            # Try to get real-time data
            current_data = stock.history(period="1d", interval="1m")
            if not current_data.empty:
                price = current_data['Close'].iloc[-1]
            else:
                # Fallback to info
                price = stock.info.get('regularMarketPrice', 
                                      stock.info.get('currentPrice', 
                                                    stock.info.get('previousClose', 0)))
            return price
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    @st.cache_data(ttl=300)
    def get_historical_data(_self, symbol: str, period: str = "1mo", 
                            interval: str = "1d") -> Optional[pd.DataFrame]:
        """Fetch historical stock data"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period, interval=interval)
            if hist.empty:
                return None
            return hist
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    @st.cache_data(ttl=3600)
    def get_company_info(_self, symbol: str) -> Dict:
        """Fetch company information"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'N/A'),
                'website': info.get('website', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'eps': info.get('trailingEps', 'N/A'),
                'dividend_yield': info.get('dividendYield', 0),
                '52w_high': info.get('fiftyTwoWeekHigh', 0),
                '52w_low': info.get('fiftyTwoWeekLow', 0),
                'avg_volume': info.get('averageVolume', 0),
                'beta': info.get('beta', 1.0),
            }
        except Exception as e:
            print(f"Error fetching info for {symbol}: {e}")
            return {}
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict:
        """Fetch data for multiple stocks simultaneously"""
        stocks_data = {}
        for symbol in symbols:
            data = self.get_stock_summary(symbol)
            if data:
                stocks_data[symbol] = data
            time.sleep(self.rate_limit_delay)
        return stocks_data
    
    @st.cache_data(ttl=60)
    def get_stock_summary(_self, symbol: str) -> Optional[Dict]:
        """Get comprehensive stock summary"""
        try:
            stock = yf.Ticker(symbol)
            
            # Get current price
            current_price = _self.get_live_price(symbol)
            if current_price is None:
                return None
            
            # Get historical data for daily metrics
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                day_high = hist['High'].iloc[-1]
                day_low = hist['Low'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
            else:
                change = 0
                change_percent = 0
                day_high = current_price
                day_low = current_price
                volume = 0
                open_price = current_price
            
            # Get 30-day historical data for charts
            hist_30d = stock.history(period="1mo")
            
            return {
                'symbol': symbol,
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'open': open_price,
                'high': day_high,
                'low': day_low,
                'volume': volume,
                'history': hist_30d,
                'info': _self.get_company_info(symbol),
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error getting summary for {symbol}: {e}")
            return None
    
    def get_intraday_data(self, symbol: str, interval: str = "5m") -> Optional[pd.DataFrame]:
        """Fetch intraday data for real-time charts"""
        try:
            stock = yf.Ticker(symbol)
            # Map interval to yfinance format
            interval_map = {
                "1m": "1m",
                "5m": "5m", 
                "15m": "15m",
                "30m": "30m",
                "1h": "60m"
            }
            yf_interval = interval_map.get(interval, "5m")
            data = stock.history(period="1d", interval=yf_interval)
            return data if not data.empty else None
        except Exception as e:
            print(f"Error fetching intraday data: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search for stocks by ticker or name"""
        try:
            # This is a simple implementation - you can enhance with yfinance Ticker object
            ticker = yf.Ticker(query.upper())
            info = ticker.info
            if info and 'symbol' in info:
                return [{
                    'symbol': info.get('symbol', query),
                    'name': info.get('longName', query),
                    'type': info.get('quoteType', 'EQUITY')
                }]
            return []
        except:
            return []
    
    def get_market_movers(self, move_type: str = "gainers") -> List[Dict]:
        """Get market movers (gainers/losers) - Note: Requires additional API"""
        # This is a placeholder - you might want to use a different API for this
        # For now, return sample data
        sample_movers = {
            "gainers": [
                {"symbol": "NVDA", "change": 8.5, "price": 485.20},
                {"symbol": "TSLA", "change": 5.2, "price": 245.80},
                {"symbol": "META", "change": 3.8, "price": 335.60},
            ],
            "losers": [
                {"symbol": "PYPL", "change": -4.2, "price": 62.30},
                {"symbol": "NFLX", "change": -2.8, "price": 475.50},
                {"symbol": "AMD", "change": -1.9, "price": 145.20},
            ]
        }
        return sample_movers.get(move_type, [])
    
    def get_options_data(self, symbol: str) -> Optional[Dict]:
        """Fetch options data for a stock"""
        try:
            stock = yf.Ticker(symbol)
            expirations = stock.options
            if not expirations:
                return None
            
            # Get nearest expiration
            nearest_exp = expirations[0]
            calls = stock.option_chain(nearest_exp).calls
            puts = stock.option_chain(nearest_exp).puts
            
            return {
                'expirations': expirations,
                'calls': calls,
                'puts': puts,
                'nearest_expiration': nearest_exp
            }
        except Exception as e:
            print(f"Error fetching options: {e}")
            return None


class PortfolioManager:
    """Manage portfolio operations"""
    
    def __init__(self, data_fetcher: StockDataFetcher):
        self.data_fetcher = data_fetcher
        self.portfolio_file = "portfolio_data.json"
    
    def calculate_portfolio_value(self, holdings: List[Dict]) -> Dict:
        """Calculate current portfolio value and metrics"""
        total_value = 0
        total_invested = 0
        holdings_data = []
        
        for holding in holdings:
            current_price = self.data_fetcher.get_live_price(holding['symbol'])
            if current_price:
                current_value = holding['shares'] * current_price
                invested_value = holding['shares'] * holding['buy_price']
                pnl = current_value - invested_value
                pnl_percent = (pnl / invested_value) * 100 if invested_value > 0 else 0
                
                total_value += current_value
                total_invested += invested_value
                
                holdings_data.append({
                    **holding,
                    'current_price': current_price,
                    'current_value': current_value,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'allocation': 0  # Will calculate after total
                })
        
        # Calculate allocations
        for holding in holdings_data:
            holding['allocation'] = (holding['current_value'] / total_value) * 100 if total_value > 0 else 0
        
        total_pnl = total_value - total_invested
        total_pnl_percent = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
        
        return {
            'total_value': total_value,
            'total_invested': total_invested,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'holdings': holdings_data
        }
    
    def get_portfolio_performance_history(self, holdings: List[Dict], days: int = 30) -> pd.DataFrame:
        """Get historical performance of portfolio"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        performance = []
        
        for date in dates:
            # Calculate portfolio value on each date (simplified)
            # In production, you'd need historical prices for each holding
            value = sum(h['shares'] * h['buy_price'] for h in holdings)
            performance.append({
                'date': date,
                'value': value
            })
        
        return pd.DataFrame(performance)


# Create singleton instances
@st.cache_resource
def get_stock_fetcher():
    return StockDataFetcher()

@st.cache_resource
def get_portfolio_manager():
    fetcher = get_stock_fetcher()
    return PortfolioManager(fetcher)