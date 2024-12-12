import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

class MLPredictor:
    def __init__(self):
        self.rf_model = self._build_rf_model()
        self.lr_model = self._build_lr_model()
        
    def _build_rf_model(self):
        return RandomForestRegressor(n_estimators=100, random_state=42)
    
    def _build_lr_model(self):
        return LinearRegression()
    
    def prepare_data(self, df):
        # Calculate technical indicators
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['RSI'] = self._calculate_rsi(df['Close'])
        df['MACD'] = self._calculate_macd(df['Close'])
        
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
        features = self.prepare_data(df)
        
        # Make predictions
        rf_pred = self.rf_model.predict(features.iloc[-1:])
        lr_pred = self.lr_model.predict(features.iloc[-1:])
            
        # Ensemble prediction (average of both models)
        final_pred = (rf_pred[0] + lr_pred[0]) / 2
        
        return {
            'rf_prediction': float(rf_pred[0]),
            'lr_prediction': float(lr_pred[0]),
            'ensemble_prediction': float(final_pred)
        }