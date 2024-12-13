'use client'

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Alert, AlertDescription } from "../components/ui/alert";
import { AlertCircle, Play, Square, TrendingUp, Plus, Trash2 } from "lucide-react";

interface Position {
  quantity: number;
  entry_price: number;
  current_price: number;
}

interface Metrics {
  current_total?: number;
  return_pct?: number;
  cash_balance?: number;
}

interface Positions {
  [key: string]: Position;
}

export default function TradingDashboard() {
  const [positions, setPositions] = useState<Positions>({});
  const [metrics, setMetrics] = useState<Metrics>({});
  const [symbols, setSymbols] = useState<string[]>([]);
  const [newSymbol, setNewSymbol] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_URL = '/api'; // This will be proxied to your backend

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [portfolioRes, stocksRes] = await Promise.all([
        fetch(`${API_URL}/portfolio`),
        fetch(`${API_URL}/stocks`)
      ]);
      
      const portfolio = await portfolioRes.json();
      const stocks = await stocksRes.json();
      
      setPositions(portfolio.positions);
      setMetrics(portfolio.performance);
      setSymbols(stocks.map((s: any) => s.symbol));
      setError(null);
    } catch (err) {
      setError('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleTrade = async (symbol: string, action: string) => {
    try {
      const res = await fetch(`${API_URL}/trade/${symbol}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, quantity: 1 })
      });
      if (!res.ok) throw new Error('Trade failed');
      fetchData();
    } catch (err) {
      setError('Trade execution failed');
    }
  };

  const handleAddSymbol = async () => {
    try {
      const res = await fetch(`${API_URL}/add_symbol/${newSymbol}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Failed to add symbol');
      setNewSymbol('');
      fetchData();
    } catch (err) {
      setError('Failed to add symbol');
    }
  };

  const handleRemoveSymbol = async (symbol: string) => {
    try {
      const res = await fetch(`${API_URL}/remove_symbol/${symbol}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to remove symbol');
      fetchData();
    } catch (err) {
      setError('Failed to remove symbol');
    }
  };

  if (loading) return <div className="flex justify-center p-8">Loading...</div>;

  return (
    <div className="p-4 max-w-7xl mx-auto space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-gray-100">
              <p className="text-sm text-gray-500">Total Value</p>
              <p className="text-2xl font-bold">${metrics.current_total?.toFixed(2) || 0}</p>
            </div>
            <div className="p-4 rounded-lg bg-gray-100">
              <p className="text-sm text-gray-500">Return</p>
              <p className="text-2xl font-bold">{metrics.return_pct?.toFixed(2) || 0}%</p>
            </div>
            <div className="p-4 rounded-lg bg-gray-100">
              <p className="text-sm text-gray-500">Cash Balance</p>
              <p className="text-2xl font-bold">${metrics.cash_balance?.toFixed(2) || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Positions */}
      <Card>
        <CardHeader>
          <CardTitle>Current Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(positions).map(([symbol, data]) => (
              <div key={symbol} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">{symbol}</p>
                  <p className="text-sm text-gray-500">
                    Quantity: {data.quantity} | Entry: ${data.entry_price}
                  </p>
                </div>
                <Button 
                  variant="destructive"
                  onClick={() => handleTrade(symbol, 'sell')}
                >
                  Close Position
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Monitored Symbols */}
      <Card>
        <CardHeader>
          <CardTitle>Monitored Symbols</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              placeholder="Enter symbol (e.g., AAPL)"
              className="border p-2 rounded"
            />
            <Button onClick={handleAddSymbol}>
              <Plus className="w-4 h-4 mr-2" />
              Add Symbol
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {symbols.map(symbol => (
              <div key={symbol} className="flex items-center justify-between p-4 border rounded-lg">
                <span>{symbol}</span>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleTrade(symbol, 'buy')}
                  >
                    <Play className="w-4 h-4" />
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleRemoveSymbol(symbol)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
