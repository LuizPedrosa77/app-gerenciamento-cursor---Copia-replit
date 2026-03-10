import React, { useState, useEffect } from 'react';
import ReplayPanel from '../components/ReplayPanel';
import { useReplayChart } from '../hooks/useReplayChart';

export default function ReplayPage() {
  const [replayStatus, setReplayStatus] = useState<'idle' | 'playing' | 'paused' | 'completed'>('idle');
  const [currentSymbol, setCurrentSymbol] = useState('EUR/USD');
  
  const {
    chartData,
    isConnected,
    replayTime,
    clearData,
    setSymbol,
    exportData
  } = useReplayChart({
    symbol: currentSymbol,
    onCandle: (candle) => {
      console.log('Novo candle:', candle);
    },
    onTick: (tick) => {
      console.log('Novo tick:', tick);
    }
  });

  useEffect(() => {
    // Carregar script do TradingView se não estiver carregado
    if (!window.TradingView) {
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = () => {
        console.log('TradingView carregado');
      };
      document.head.appendChild(script);
    }
  }, []);

  const handleReplayData = (data: any) => {
    console.log('Dados do replay:', data);
    // Aqui você pode processar os dados do replay
    // e atualizar outros componentes se necessário
  };

  const handleStatusChange = (status: 'idle' | 'playing' | 'paused' | 'completed') => {
    setReplayStatus(status);
    console.log('Status do replay:', status);
  };

  const handleSymbolChange = (symbol: string) => {
    setCurrentSymbol(symbol);
    setSymbol(symbol);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-gray-900">
              Replay de Mercado
            </h1>
            
            <div className="flex items-center gap-4">
              {/* Seletor de Símbolo */}
              <select
                value={currentSymbol}
                onChange={(e) => handleSymbolChange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="EUR/USD">EUR/USD</option>
                <option value="GBP/USD">GBP/USD</option>
                <option value="USD/JPY">USD/JPY</option>
                <option value="AUD/USD">AUD/USD</option>
                <option value="USD/CAD">USD/CAD</option>
              </select>

              {/* Status */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  replayStatus === 'playing' ? 'bg-green-500 animate-pulse' :
                  replayStatus === 'paused' ? 'bg-yellow-500' :
                  replayStatus === 'completed' ? 'bg-blue-500' :
                  'bg-gray-400'
                }`} />
                <span className="text-sm font-medium text-gray-700">
                  {replayStatus === 'playing' ? 'Reproduzindo' :
                   replayStatus === 'paused' ? 'Pausado' :
                   replayStatus === 'completed' ? 'Concluído' :
                   'Inativo'}
                </span>
              </div>

              {/* Botões de Ação */}
              <button
                onClick={clearData}
                className="px-3 py-2 bg-gray-500 text-white text-sm rounded-md hover:bg-gray-600 transition-colors"
              >
                Limpar Dados
              </button>
              
              <button
                onClick={() => {
                  const data = exportData();
                  console.log('Dados exportados:', data);
                  // Aqui você pode implementar download do JSON
                  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `replay-data-${currentSymbol}-${new Date().toISOString().split('T')[0]}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="px-3 py-2 bg-blue-500 text-white text-sm rounded-md hover:bg-blue-600 transition-colors"
              >
                Exportar Dados
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Conteúdo Principal */}
      <div className="relative">
        {/* Container do TradingView */}
        <div className="h-screen">
          <div 
            id="tradingview_chart" 
            style={{ height: 'calc(100vh - 200px)' }}
            className="bg-white"
          />
        </div>

        {/* Painel de Replay */}
        <ReplayPanel
          onReplayData={handleReplayData}
          onStatusChange={handleStatusChange}
        />

        {/* Overlay de Informações */}
        {replayTime && (
          <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-10">
            <div className="text-sm font-medium text-gray-700 mb-2">
              Tempo Atual do Replay
            </div>
            <div className="text-lg font-bold text-blue-600">
              {new Date(replayTime).toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}
            </div>
          </div>
        )}

        {/* Estatísticas em Tempo Real */}
        {chartData && (
          <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-10">
            <div className="text-sm font-medium text-gray-700 mb-3">
              Estatísticas do Replay
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Candles:</span>
                <span className="font-medium">{chartData.candles.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Ticks:</span>
                <span className="font-medium">{chartData.ticks.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Preço Atual:</span>
                <span className="font-medium">
                  {chartData.currentPrice ? chartData.currentPrice.toFixed(5) : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Volume:</span>
                <span className="font-medium">{chartData.volume.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="text-center text-sm text-gray-500">
            Sistema de Replay de Mercado - Gustavo Pedrosa FX
          </div>
        </div>
      </div>
    </div>
  );
}
