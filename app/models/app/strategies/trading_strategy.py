from datetime import datetime

class TradingStrategy:
    def __init__(self, initial_balance=1000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = {}
        self.trades = []
        
        # Risk management parameters
        self.max_position_size = 0.2  # Max 20% of portfolio in single position
        self.stop_loss_pct = 0.02     # 2% stop loss
        self.take_profit_pct = 0.04   # 4% take profit
        self.max_daily_loss = 0.05    # 5% max daily loss

    def get_total_value(self):
        """Calculate total portfolio value including positions"""
        total = self.balance
        for symbol, position in self.positions.items():
            total += position['quantity'] * position['current_price']
        return total
        
    def should_buy(self, predictions, technical_indicators):
        """Determine if we should buy based on predictions and technicals"""
        # Calculate prediction confidence
        pred_change = (predictions['ensemble_prediction'] - technical_indicators['current_price']) / technical_indicators['current_price']
        
        # Calculate technical signals
        tech_signals = 0
        if technical_indicators['current_price'] > technical_indicators['sma20']:
            tech_signals += 1
        if 30 < technical_indicators['rsi'] < 70:
            tech_signals += 1
        if technical_indicators['macd'] > 0:
            tech_signals += 1
            
        confidence = (tech_signals / 3 + max(0, pred_change)) / 2
        
        return {
            'should_buy': pred_change > 0.01 and confidence > 0.6,
            'confidence': confidence
        }
    
    def execute_trade(self, symbol, action, quantity, price):
        """Execute a trade with risk management"""
        if action == "buy":
            cost = price * quantity
            if cost <= self.balance and cost <= self.balance * self.max_position_size:
                self.balance -= cost
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'current_price': price,
                    'timestamp': datetime.now()
                }
                self.trades.append({
                    'symbol': symbol,
                    'action': 'buy',
                    'quantity': quantity,
                    'price': price,
                    'timestamp': datetime.now()
                })
                return True
                
        elif action == "sell" and symbol in self.positions:
            position = self.positions[symbol]
            revenue = price * quantity
            self.balance += revenue
            
            # Calculate profit/loss
            profit = (price - position['entry_price']) * quantity
            
            # Update position or remove if fully sold
            if quantity >= position['quantity']:
                del self.positions[symbol]
            else:
                position['quantity'] -= quantity
            
            self.trades.append({
                'symbol': symbol,
                'action': 'sell',
                'quantity': quantity,
                'price': price,
                'profit': profit,
                'timestamp': datetime.now()
            })
            return True
            
        return False

    def update_positions(self, symbol, current_price):
        """Update position with current price and check stop loss/take profit"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position['current_price'] = current_price
            
            price_change = (current_price - position['entry_price']) / position['entry_price']
            
            # Check stop loss and take profit
            if price_change <= -self.stop_loss_pct or price_change >= self.take_profit_pct:
                return self.execute_trade(symbol, "sell", position['quantity'], current_price)
        
        return False

