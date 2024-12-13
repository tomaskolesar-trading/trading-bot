from fastapi import FastAPI
from backend.ml_models import MLPredictor
from backend.trading_strategy import TradingStrategy
import yfinance as yf
from datetime import datetime
import logging
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Trading Bot API")

# Add CORS middleware
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

# Initialize ML model and trading bot
ml_predictor = MLPredictor()
trading_bot = TradingStrategy(initial_balance=1000)

# Track monitored symbols
MONITORED_SYMBOLS = ["AAPL", "MSFT", "GOOGL"]

@app.get("/")
async def root():
   """Root endpoint showing bot status"""
   return {
       "status": "Trading Bot Active",
       "balance": trading_bot.get_total_value(),
       "positions": trading_bot.positions
   }

@app.get("/stocks")
async def get_stocks():
   """Get analysis for all monitored stocks"""
   try:
       results = []
       for symbol in MONITORED_SYMBOLS:
           stock = yf.Ticker(symbol)
           hist = stock.history(period="60d")
           
           if hist.empty:
               continue
           
           current_price = float(hist['Close'].iloc[-1])
           
           # Update position if we hold this stock
           if symbol in trading_bot.positions:
               trading_bot.update_positions(symbol, current_price)
           
           # Get predictions
           predictions = ml_predictor.predict(hist)
           technical_indicators = {
               "current_price": current_price,
               "sma20": float(hist['Close'].rolling(window=20).mean().iloc[-1]),
               "rsi": float(ml_predictor._calculate_rsi(hist['Close']).iloc[-1]),
               "macd": float(ml_predictor._calculate_macd(hist['Close']).iloc[-1])
           }
           
           # Get trading decision
           trading_decision = trading_bot.should_buy(predictions, technical_indicators)
           
           results.append({
               "symbol": symbol,
               "price": current_price,
               "predictions": predictions,
               "technical_indicators": technical_indicators,
               "trading_decision": trading_decision,
               "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           })
           
       return results
   except Exception as e:
       logger.error(f"Error getting stocks: {str(e)}")
       return {"error": str(e)}

@app.get("/portfolio")
async def get_portfolio():
   """Get current portfolio status"""
   total_value = trading_bot.get_total_value()
   return {
       "total_value": total_value,
       "cash_balance": trading_bot.balance,
       "positions": trading_bot.positions,
       "trades": trading_bot.trades[-10:],  # Last 10 trades
       "performance": {
           "initial_balance": trading_bot.initial_balance,
           "current_total": total_value,
           "return_pct": ((total_value - trading_bot.initial_balance) / trading_bot.initial_balance) * 100
       }
   }

@app.post("/trade/{symbol}")
async def execute_trade(symbol: str, action: str, quantity: int):
   """Execute a buy or sell trade"""
   try:
       symbol = symbol.upper()
       stock = yf.Ticker(symbol)
       current_price = float(stock.history(period="1d")['Close'].iloc[-1])
       
       success = trading_bot.execute_trade(symbol, action, quantity, current_price)
       
       return {
           "success": success,
           "trade_details": {
               "symbol": symbol,
               "action": action,
               "quantity": quantity,
               "price": current_price,
               "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           },
           "portfolio_update": {
               "new_balance": trading_bot.balance,
               "positions": trading_bot.positions
           }
       }
   except Exception as e:
       logger.error(f"Error executing trade: {str(e)}")
       return {"error": str(e)}

@app.post("/add_symbol/{symbol}")
async def add_symbol(symbol: str):
   """Add new symbol to monitoring list"""
   try:
       symbol = symbol.upper()
       if symbol not in MONITORED_SYMBOLS:
           stock = yf.Ticker(symbol)
           hist = stock.history(period="1d")
           if not hist.empty:
               MONITORED_SYMBOLS.append(symbol)
               return {
                   "message": f"Added {symbol} to monitored symbols",
                   "monitored_symbols": MONITORED_SYMBOLS
               }
       return {"error": "Symbol already monitored or invalid"}
   except Exception as e:
       logger.error(f"Error adding symbol: {str(e)}")
       return {"error": str(e)}

@app.delete("/remove_symbol/{symbol}")
async def remove_symbol(symbol: str):
   """Remove symbol from monitoring list"""
   try:
       symbol = symbol.upper()
       if symbol in MONITORED_SYMBOLS:
           MONITORED_SYMBOLS.remove(symbol)
           return {
               "message": f"Removed {symbol} from monitored symbols",
               "monitored_symbols": MONITORED_SYMBOLS
           }
       return {"error": "Symbol not found"}
   except Exception as e:
       logger.error(f"Error removing symbol: {str(e)}")
       return {"error": str(e)}

@app.get("/health")
async def health_check():
   """Health check endpoint"""
   return {
       "status": "healthy",
       "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
       "monitored_symbols": len(MONITORED_SYMBOLS),
       "active_positions": len(trading_bot.positions)
   }
