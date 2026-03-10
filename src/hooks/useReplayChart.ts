/**
 * Hook personalizado para integração do Replay com TradingView
 */
import { useEffect, useRef, useState } from 'react';
import replayService, { ReplayCandle, ReplayTick } from '../services/replayService';

interface UseReplayChartOptions {
  symbol?: string;
  onCandle?: (candle: ReplayCandle) => void;
  onTick?: (tick: ReplayTick) => void;
}

interface ChartData {
  candles: ReplayCandle[];
  ticks: ReplayTick[];
  currentPrice: number | null;
  volume: number;
}

export function useReplayChart(options: UseReplayChartOptions = {}) {
  const [chartData, setChartData] = useState<ChartData>({
    candles: [],
    ticks: [],
    currentPrice: null,
    volume: 0,
  });

  const [isConnected, setIsConnected] = useState(false);
  const [replayTime, setReplayTime] = useState<string | null>(null);
  const chartWidgetRef = useRef<any>(null);
  const verticalLineRef = useRef<any>(null);
  const labelRef = useRef<any>(null);

  // Inicializar TradingView Widget
  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).TradingView) {
      initTradingViewWidget();
    }
  }, []);

  // Configurar callbacks do replay
  useEffect(() => {
    replayService.onCandle((candle: ReplayCandle) => {
      setChartData(prev => ({
        ...prev,
        candles: [...prev.candles, candle],
        currentPrice: candle.close,
        volume: candle.volume,
      }));

      updateChartWithCandle(candle);
      options.onCandle?.(candle);
    });

    replayService.onTick((tick: ReplayTick) => {
      setChartData(prev => ({
        ...prev,
        ticks: [...prev.ticks, tick],
        currentPrice: (tick.bid + tick.ask) / 2,
        volume: tick.volume,
      }));

      updateChartWithTick(tick);
      options.onTick?.(tick);
    });

    replayService.onStatus((status) => {
      if (status.current_time) {
        setReplayTime(status.current_time);
        updateReplayLine(status.current_time);
      }
    });

    return () => {
      cleanup();
    };
  }, [options]);

  const initTradingViewWidget = () => {
    const widget = new (window as any).TradingView.widget({
      container_id: 'tradingview_chart',
      symbol: options.symbol || 'EUR/USD',
      interval: '1H',
      theme: 'light',
      style: '1',
      locale: 'pt_BR',
      toolbar_bg: '#f1f3f6',
      enable_publishing: false,
      allow_symbol_change: true,
      datafeed: createCustomDatafeed(),
      library_path: 'https://s3.tradingview.com/tv.js/',
      studies_overrides: {},
      overrides: {
        'paneProperties.background': '#ffffff',
        'paneProperties.vertGridProperties.color': '#f1f3f6',
        'paneProperties.horzGridProperties.color': '#f1f3f6',
        'symbolWatermarkProperties.transparency': 90,
        'scalesProperties.textColor': '#666',
        'mainSeriesProperties.candleStyle.wickUpColor': '#26a69a',
        'mainSeriesProperties.candleStyle.wickDownColor': '#ef5350',
      },
    });

    chartWidgetRef.current = widget;
    widget.onChartReady(() => {
      createReplayLine();
    });
  };

  const createCustomDatafeed = () => {
    return {
      onReady: (callback: any) => {
        setTimeout(() => {
          callback({
            supported_resolutions: ['1', '5', '15', '30', '60', '240', '1D'],
            supports_marks: false,
            supports_time: true,
          });
        }, 0);
      },
      resolveSymbol: (symbolName: string, onSymbolResolvedCallback: any, onResolveErrorCallback: any) => {
        setTimeout(() => {
          onSymbolResolvedCallback({
            name: symbolName,
            description: symbolName,
            type: 'forex',
            session: '24x7',
            timezone: 'America/Sao_Paulo',
            ticker: symbolName,
            exchange: 'FX',
            minmov: 1,
            pricescale: 100000,
            has_intraday: true,
            has_no_volume: false,
            supported_resolutions: ['1', '5', '15', '30', '60', '240', '1D'],
          });
        }, 0);
      },
      getBars: (
        symbolInfo: any,
        resolution: string,
        from: number,
        to: number,
        onHistoryCallback: any,
        onErrorCallback: any,
        firstDataRequest: boolean
      ) => {
        // Usar dados do replay se disponíveis
        if (chartData.candles.length > 0) {
          const bars = chartData.candles.map(candle => ({
            time: new Date(candle.timestamp).getTime() / 1000,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
            volume: candle.volume,
          }));
          onHistoryCallback(bars, { noData: false });
        } else {
          onHistoryCallback([], { noData: true });
        }
      },
      subscribeBars: () => {},
      unsubscribeBars: () => {},
    };
  };

  const createReplayLine = () => {
    if (!chartWidgetRef.current) return;

    const chart = chartWidgetRef.current.chart();
    
    // Criar linha vertical para tempo atual do replay
    verticalLineRef.current = chart.createLine({
      color: '#2196F3',
      width: 2,
      style: 2, // dashed
      title: 'Replay Time',
    });

    // Criar label flutuante
    labelRef.current = chart.createShape({
      shape: 'text',
      text: '',
      color: '#2196F3',
      backgroundColor: '#ffffff',
      borderColor: '#2196F3',
      borderWidth: 1,
      fontsize: 12,
      bold: true,
    });
  };

  const updateChartWithCandle = (candle: ReplayCandle) => {
    if (!chartWidgetRef.current) return;

    const chart = chartWidgetRef.current.chart();
    const barData = {
      time: new Date(candle.timestamp).getTime() / 1000,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
      volume: candle.volume,
    };

    // Atualizar gráfico com novo candle
    chart.dataHandler().updateData(barData);
  };

  const updateChartWithTick = (tick: ReplayTick) => {
    if (!chartWidgetRef.current) return;

    const chart = chartWidgetRef.current.chart();
    const currentPrice = (tick.bid + tick.ask) / 2;

    // Criar ou atualizar linha de preço atual
    if (chart.currentPriceLine) {
      chart.currentPriceLine.remove();
    }

    chart.currentPriceLine = chart.createLine({
      color: '#FF6B6B',
      width: 2,
      price: currentPrice,
      title: `Current: ${currentPrice.toFixed(5)}`,
    });
  };

  const updateReplayLine = (timestamp: string) => {
    if (!chartWidgetRef.current || !verticalLineRef.current || !labelRef.current) return;

    const chart = chartWidgetRef.current.chart();
    const time = new Date(timestamp).getTime() / 1000;

    // Atualizar posição da linha vertical
    verticalLineRef.current.setEnd({ time, price: null });
    verticalLineRef.current.setStart({ time, price: null });

    // Atualizar label
    const formattedTime = new Date(timestamp).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

    labelRef.current.set({
      time,
      price: chart.getVisibleRange().from + (chart.getVisibleRange().to - chart.getVisibleRange().from) * 0.8,
      text: formattedTime,
    });
  };

  const cleanup = () => {
    if (chartWidgetRef.current) {
      chartWidgetRef.current.remove();
      chartWidgetRef.current = null;
    }
    verticalLineRef.current = null;
    labelRef.current = null;
  };

  // Métodos públicos
  const clearData = () => {
    setChartData({
      candles: [],
      ticks: [],
      currentPrice: null,
      volume: 0,
    });

    if (chartWidgetRef.current) {
      chartWidgetRef.current.chart().dataHandler().clearData();
    }
  };

  const setSymbol = (newSymbol: string) => {
    if (chartWidgetRef.current) {
      chartWidgetRef.current.setSymbol(newSymbol);
    }
  };

  const setTimeframe = (timeframe: string) => {
    if (chartWidgetRef.current) {
      chartWidgetRef.current.setTimeframe(timeframe);
    }
  };

  const exportData = () => {
    return {
      candles: chartData.candles,
      ticks: chartData.ticks,
      summary: {
        totalCandles: chartData.candles.length,
        totalTicks: chartData.ticks.length,
        currentPrice: chartData.currentPrice,
        totalVolume: chartData.volume,
        timeRange: {
          start: chartData.candles[0]?.timestamp,
          end: chartData.candles[chartData.candles.length - 1]?.timestamp,
        },
      },
    };
  };

  return {
    // Estado
    chartData,
    isConnected,
    replayTime,
    
    // Métodos
    clearData,
    setSymbol,
    setTimeframe,
    exportData,
    
    // Refs
    chartWidgetRef,
    verticalLineRef,
    labelRef,
  };
}
