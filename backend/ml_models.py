import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import yfinance as yf

class MLPredictor:
    def __init__(self):
        # Initialize models
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.lr_model = LinearRegression()
        
        # Pre-train models with historical data
        self._pretrain_models()
        
    def _pretrain_models(self):
        """Pre-train models with AAPL historical data"""
        try:
            # Get training data (using AAPL as it's liquid and has good history)
            stock = yf.Ticker("AAPL")
            hist = stock.history(period="1y")  # 1 year of data
            
            # Prepare features and target
            features = self.prepare_data(hist)
            # Target is next day's price
            target = hist['Close'].shift(-1)[:-1]  # Remove last row as we won't have next day's price
            features = features[:-1]  # Remove last row to match target
            
            # Train models
            self.rf_model.fit(features, target)
            self.lr_model.fit(features, target)
            
        except Exception as e:
            print(f"Error in pre-training: {str(e)}")
        
    def prepare_data(self, df):
        # Calculate technical indicators
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['RSI'] = self._calculate_rsi(df['Close'])
        df['MACD'] = self._calculate_macd(df['Close'])
        
        # Fill NaN values that occur due to rolling calculations
        df = df.fillna(method='bfill')
        
        # Prepare features
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA20', 'RSI', 'MACD']
        return df[features]
    
    def _calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices, fast=12, slow=26):
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        return exp1 - exp2
        
    def predict(self, df):
        try:
            features = self.prepare_data(df)
            
            # Make predictions using the last row of data
            rf_pred = self.rf_model.predict(features.iloc[-1:])
            lr_pred = self.lr_model.predict(features.iloc[-1:])
                
            # Ensemble prediction (average of both models)
            final_pred = (rf_pred[0] + lr_pred[0]) / 2
            
            return {
                'rf_prediction': float(rf_pred[0]),
                'lr_prediction': float(lr_pred[0]),
                'ensemble_prediction': float(final_pred)
            }
        except Exception as e:
            return {
                'error': f"Prediction error: {str(e)}",
                'technical_indicators': {
                    'rsi': float(self._calculate_rsi(df['Close']).iloc[-1]),
                    'macd': float(self._calculate_macd(df['Close']).iloc[-1])
                }
            }
