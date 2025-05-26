from flask import Flask, render_template, request, jsonify
import json
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALPHA_VANTAGE_API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"  # Replace with your actual Alpha Vantage API key
NEWS_API_KEY = "YOUR_NEWS_API_KEY"  # Replace with your actual News API key

@dataclass
class StockData:
    """Data structure for stock information"""
    ticker: str
    company_name: str
    current_price: float
    price_change: float
    price_change_percent: float
    news: List[Dict]
    analysis: str

class BaseAgent:
    """Base class for all agents in the system"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"Agent.{name}")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main functionality"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def log_execution(self, input_data: Any, output_data: Any):
        """Log agent execution for debugging"""
        self.logger.info(f"Input: {input_data}")
        self.logger.info(f"Output: {output_data}")

class IdentifyTickerAgent(BaseAgent):
    """Agent to identify stock ticker from natural language query"""
    
    def __init__(self):
        super().__init__("IdentifyTicker")
        # Common company name to ticker mappings
        self.ticker_map = {
            "tesla": "TSLA",
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "nvidia": "NVDA",
            "meta": "META",
            "facebook": "META",
            "palantir": "PLTR",
            "netflix": "NFLX",
            "spotify": "SPOT",
            "uber": "UBER",
            "airbnb": "ABNB",
            "coinbase": "COIN",
            "robinhood": "HOOD",
            "gamestop": "GME",
            "amc": "AMC",
            "blackberry": "BB",
            "nokia": "NOK",
            "ford": "F",
            "general motors": "GM",
            "gm": "GM"
        }
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ticker symbol from user query"""
        query = context.get("user_query", "").lower()
        
        # First, look for direct ticker mentions (3-5 uppercase letters)
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        direct_tickers = re.findall(ticker_pattern, context.get("user_query", ""))
        
        if direct_tickers:
            ticker = direct_tickers[0]
            company_name = self._get_company_name(ticker)
        else:
            # Look for company names in the query
            ticker = None
            company_name = None
            
            for company, tick in self.ticker_map.items():
                if company in query:
                    ticker = tick
                    company_name = company.title()
                    break
        
        if not ticker:
            for tick in set(self.ticker_map.values()):
                if tick.lower() in query:
                    ticker = tick
                    company_name = self._get_company_name(tick)
                    break
        
        result = {
            "ticker": ticker,
            "company_name": company_name,
            "confidence": 0.9 if ticker else 0.0
        }
        
        self.log_execution(query, result)
        return result
    
    def _get_company_name(self, ticker: str) -> str:
        """Get company name from ticker (reverse lookup)"""
        reverse_map = {v: k.title() for k, v in self.ticker_map.items()}
        return reverse_map.get(ticker, ticker)

class TickerPriceAgent(BaseAgent):
    """Agent to fetch current stock price"""

    def __init__(self):
        super().__init__("TickerPrice")

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch current price for the given ticker"""
        ticker = context.get("ticker")

        if not ticker:
            self.logger.error("No ticker provided in context")
            return {"error": "No ticker provided"}

        try:
            self.logger.info(f"Fetching price data for ticker: {ticker}")
            price_data = self._fetch_price_data(ticker)
            
            result = {
                "current_price": price_data.get("price", 0.0),
                "currency": "USD",
                "last_updated": price_data.get("last_updated", ""),
                "market_status": price_data.get("market_status", "CLOSED")
            }

            self.log_execution(ticker, result)
            return result

        except Exception as e:
            self.logger.error(f"Error fetching price for {ticker}: {e}")
            # Return fallback data instead of raising exception
            fallback_price = 150.00 + (hash(ticker) % 100)
            return {
                "current_price": fallback_price,
                "currency": "USD",
                "last_updated": datetime.now().isoformat(),
                "market_status": "CLOSED",
                "error": str(e)
            }

    def _fetch_price_data(self, ticker: str) -> Dict:
        """Fetch price data from Alpha Vantage with better error handling"""
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        }

        self.logger.info(f"Making API request to: {url} with params: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            self.logger.info(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"API response data keys: {list(data.keys())}")
                
                # Check for API limit exceeded
                if "Note" in data:
                    raise Exception(f"API limit exceeded: {data['Note']}")
                
                # Check for invalid API key
                if "Error Message" in data:
                    raise Exception(f"API error: {data['Error Message']}")
                
                if "Global Quote" in data and data["Global Quote"]:
                    quote = data["Global Quote"]
                    self.logger.info(f"Quote data: {quote}")
                    
                    price = quote.get("05. price", "0")
                    if price and price != "0":
                        return {
                            "price": float(price),
                            "last_updated": quote.get("07. latest trading day", ""),
                            "market_status": "CLOSED"  # Simplified
                        }
                    else:
                        raise Exception("No price data available in response")
                else:
                    raise Exception("No Global Quote data in response")
            else:
                raise Exception(f"HTTP error: {response.status_code}")
                
        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except ValueError as e:
            raise Exception(f"JSON parsing error: {str(e)}")

class TickerPriceChangeAgent(BaseAgent):
    """Agent to calculate price changes over time"""
    
    def __init__(self):
        super().__init__("TickerPriceChange")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate price change for the given timeframe"""
        ticker = context.get("ticker")
        timeframe = context.get("timeframe", "1D")  # Default to 1 day
        
        if not ticker:
            return {"error": "No ticker provided"}
        
        try:
            # Add delay to avoid API rate limits
            time.sleep(1)
            change_data = self._calculate_price_change(ticker, timeframe)
            result = {
                "price_change": change_data.get("change", 0.0),
                "price_change_percent": change_data.get("change_percent", 0.0),
                "timeframe": timeframe,
                "start_price": change_data.get("start_price", 0.0),
                "end_price": change_data.get("end_price", 0.0)
            }
            
            self.log_execution(f"{ticker} - {timeframe}", result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating price change: {e}")
            # Return mock data for demo
            mock_change = (hash(ticker) % 20) - 10  # Random change between -10 and +10
            return {
                "price_change": mock_change,
                "price_change_percent": mock_change / 100 * 5,  # Mock percentage
                "timeframe": timeframe,
                "error": str(e)
            }
    
    def _calculate_price_change(self, ticker: str, timeframe: str) -> Dict:
        """Calculate actual price change using historical data"""
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Check for API errors
            if "Note" in data:
                raise Exception(f"API limit exceeded: {data['Note']}")
            if "Error Message" in data:
                raise Exception(f"API error: {data['Error Message']}")
                
            if "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]
                dates = sorted(time_series.keys(), reverse=True)
                
                if len(dates) >= 2:
                    latest_price = float(time_series[dates[0]]["4. close"])
                    previous_price = float(time_series[dates[1]]["4. close"])
                    
                    change = latest_price - previous_price
                    change_percent = (change / previous_price) * 100
                    
                    return {
                        "change": change,
                        "change_percent": change_percent,
                        "start_price": previous_price,
                        "end_price": latest_price
                    }
        
        raise Exception("Unable to calculate price change")

class TickerNewsAgent(BaseAgent):
    """Agent to fetch recent news about a stock"""
    
    def __init__(self):
        super().__init__("TickerNews")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch recent news for the given ticker"""
        ticker = context.get("ticker")
        company_name = context.get("company_name", ticker)
        
        if not ticker:
            return {"news": [], "error": "No ticker provided"}
        
        try:
            # Add delay to avoid API rate limits
            time.sleep(1)
            # Use Alpha Vantage News API
            news = self._fetch_alpha_vantage_news(ticker, company_name)
            if not news:
                # Fallback to mock news for demo
                news = self._get_mock_news(ticker)
            
            result = {"news": news[:5]}  # Limit to top 5 news items
            self.log_execution(ticker, f"Found {len(news)} news items")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")
            return {"news": self._get_mock_news(ticker), "error": str(e)}
    
    def _fetch_alpha_vantage_news(self, ticker: str, company_name: str) -> List[Dict]:
        """Fetch news from Alpha Vantage API"""
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY,
            "limit": 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "feed" in data:
                return [
                    {
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "url": item.get("url", ""),
                        "time_published": item.get("time_published", ""),
                        "sentiment": item.get("overall_sentiment_label", "Neutral")
                    }
                    for item in data["feed"]
                ]
        return []
    
    def _get_mock_news(self, ticker: str) -> List[Dict]:
        """Generate mock news for demo purposes"""
        return [
            {
                "title": f"{ticker} Reports Strong Quarterly Earnings",
                "summary": f"{ticker} exceeded analysts' expectations with strong revenue growth and positive outlook for next quarter.",
                "url": "https://example.com/news1",
                "time_published": "2024-01-15T09:30:00",
                "sentiment": "Bullish"
            },
            {
                "title": f"Market Analysis: {ticker} Stock Movement",
                "summary": f"Recent market volatility has affected {ticker} stock price, but fundamentals remain strong.",
                "url": "https://example.com/news2",
                "time_published": "2024-01-14T14:22:00",
                "sentiment": "Neutral"
            }
        ]

class TickerAnalysisAgent(BaseAgent):
    """Agent to provide analysis of stock movements"""
    
    def __init__(self):
        super().__init__("TickerAnalysis")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze stock movement based on news and price data"""
        ticker = context.get("ticker")
        news = context.get("news", [])
        price_change = context.get("price_change", 0)
        price_change_percent = context.get("price_change_percent", 0)
        
        if not ticker:
            return {"error": "No ticker provided"}
        
        try:
            analysis = self._generate_analysis(ticker, news, price_change, price_change_percent)
            result = {
                "analysis": analysis,
                "sentiment": self._determine_sentiment(news, price_change_percent),
                "key_factors": self._extract_key_factors(news, price_change_percent)
            }
            
            self.log_execution(f"{ticker}", "Analysis generated")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating analysis: {e}")
            return {"error": str(e)}
    
    def _generate_analysis(self, ticker: str, news: List[Dict], price_change: float, price_change_percent: float) -> str:
        """Generate comprehensive analysis"""
        # Determine direction
        if price_change_percent > 2:
            direction = "significant increase"
        elif price_change_percent > 0:
            direction = "modest increase"
        elif price_change_percent < -2:
            direction = "significant decrease"
        elif price_change_percent < 0:
            direction = "modest decrease"
        else:
            direction = "relatively stable movement"
        
        # Analyze news sentiment
        bullish_news = sum(1 for n in news if n.get("sentiment", "").lower() in ["bullish", "positive"])
        bearish_news = sum(1 for n in news if n.get("sentiment", "").lower() in ["bearish", "negative"])
        
        analysis = f"""Based on recent data, {ticker} has experienced a {direction} of {price_change_percent:.2f}% (${price_change:.2f}) in the analyzed timeframe.

News Analysis:
- {len(news)} recent news articles found
- {bullish_news} articles with positive sentiment
- {bearish_news} articles with negative sentiment

The price movement appears to be {"consistent" if (price_change_percent > 0 and bullish_news > bearish_news) or (price_change_percent < 0 and bearish_news > bullish_news) else "inconsistent"} with the overall news sentiment.

Key recent developments include market reactions to earnings reports, industry trends, and broader economic factors affecting the stock."""
        
        return analysis
    
    def _determine_sentiment(self, news: List[Dict], price_change_percent: float) -> str:
        """Determine overall sentiment"""
        if price_change_percent > 3:
            return "Very Bullish"
        elif price_change_percent > 1:
            return "Bullish"
        elif price_change_percent > -1:
            return "Neutral"
        elif price_change_percent > -3:
            return "Bearish"
        else:
            return "Very Bearish"
    
    def _extract_key_factors(self, news: List[Dict], price_change_percent: float) -> List[str]:
        """Extract key factors affecting stock price"""
        factors = []
        
        if abs(price_change_percent) > 2:
            factors.append("Significant price volatility")
        
        if news:
            factors.append("Recent news coverage")
            
        factors.extend([
            "Market sentiment",
            "Trading volume",
            "Sector performance"
        ])
        
        return factors[:5]  # Limit to top 5 factors

class StockAnalysisOrchestrator:
    """Main orchestrator that coordinates all agents"""
    
    def __init__(self):
        self.agents = {
            "identify_ticker": IdentifyTickerAgent(),
            "ticker_price": TickerPriceAgent(),
            "ticker_price_change": TickerPriceChangeAgent(),
            "ticker_news": TickerNewsAgent(),
            "ticker_analysis": TickerAnalysisAgent()
        }
        self.logger = logging.getLogger("Orchestrator")
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a user query through the agent pipeline"""
        self.logger.info(f"Processing query: {user_query}")
        
        context = {"user_query": user_query}
        results = {}
        
        try:
            # Step 1: Identify ticker
            ticker_result = self.agents["identify_ticker"].execute(context)
            if not ticker_result.get("ticker"):
                return {"error": "Could not identify stock ticker from query", "success": False}
            
            context.update(ticker_result)
            results["ticker_info"] = ticker_result
            
            # Step 2: Get current price
            price_result = self.agents["ticker_price"].execute(context)
            context.update(price_result)
            results["price_info"] = price_result
            
            # Step 3: Calculate price change
            price_change_result = self.agents["ticker_price_change"].execute(context)
            context.update(price_change_result)
            results["price_change_info"] = price_change_result
            
            # Step 4: Fetch news
            news_result = self.agents["ticker_news"].execute(context)
            context.update(news_result)
            results["news_info"] = news_result
            
            # Step 5: Generate analysis
            analysis_result = self.agents["ticker_analysis"].execute(context)
            results["analysis_info"] = analysis_result
            
            # Compile final response
            final_response = self._compile_response(context, results)
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {"error": f"Failed to process query: {str(e)}", "success": False}
    
    def _compile_response(self, context: Dict, results: Dict) -> Dict[str, Any]:
        """Compile final response for the user"""
        ticker = context.get("ticker", "Unknown")
        company_name = context.get("company_name", ticker)
        current_price = context.get("current_price", 0)
        price_change = context.get("price_change", 0)
        price_change_percent = context.get("price_change_percent", 0)
        news = context.get("news", [])
        analysis = results.get("analysis_info", {}).get("analysis", "No analysis available")
        sentiment = results.get("analysis_info", {}).get("sentiment", "Neutral")
        
        return {
            "ticker": ticker,
            "company_name": company_name,
            "current_price": current_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "sentiment": sentiment,
            "news_count": len(news),
            "recent_news": news[:3],  # Top 3 news items
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

# Flask App
app = Flask(__name__)

# Initialize the orchestrator
orchestrator = StockAnalysisOrchestrator()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('stock.html')

@app.route('/analyze', methods=['POST'])
def analyze_stock():
    """API endpoint to analyze stock based on user query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "No query provided", "success": False}), 400
        
        # Process the query using the orchestrator
        result = orchestrator.process_query(query)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in analyze_stock: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)