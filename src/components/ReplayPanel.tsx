import React, { useState, useEffect, useRef } from 'react';
import { Calendar, Play, Pause, Square, SkipForward, SkipBack, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';
import replayService, { ReplayConfig, ReplaySession, ReplayProgress, ReplayStatus } from '../services/replayService';

interface ReplayPanelProps {
  onReplayData?: (data: any) => void;
  onStatusChange?: (status: 'idle' | 'playing' | 'paused' | 'completed') => void;
}

type ReplayState = 'idle' | 'playing' | 'paused' | 'completed';

const TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'];
const SPEEDS = [0.5, 1, 2, 5, 10];
const SYMBOLS = [
  { value: 'EUR/USD', label: 'EUR/USD' },
  { value: 'GBP/USD', label: 'GBP/USD' },
  { value: 'USD/JPY', label: 'USD/JPY' },
  { value: 'AUD/USD', label: 'AUD/USD' },
  { value: 'USD/CAD', label: 'USD/CAD' },
];

export default function ReplayPanel({ onReplayData, onStatusChange }: ReplayPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [replayState, setReplayState] = useState<ReplayState>('idle');
  const [currentSession, setCurrentSession] = useState<ReplaySession | null>(null);
  const [progress, setProgress] = useState<ReplayProgress | null>(null);
  
  // Configuração
  const [symbol, setSymbol] = useState('EUR/USD');
  const [timeframe, setTimeframe] = useState('H1');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [speed, setSpeed] = useState(1);
  const [mode, setMode] = useState<'candle' | 'tick'>('candle');

  const progressBarRef = useRef<HTMLDivElement>(null);

  // Inicializar datas padrão
  useEffect(() => {
    const now = new Date();
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
    
    setStartDate(lastMonth.toISOString().split('T')[0]);
    setEndDate(now.toISOString().split('T')[0]);
  }, []);

  // Configurar callbacks do serviço
  useEffect(() => {
    replayService.onStatus((status: ReplayStatus) => {
      switch (status.status) {
        case 'running':
          setReplayState('playing');
          onStatusChange?.('playing');
          break;
        case 'paused':
          setReplayState('paused');
          onStatusChange?.('paused');
          break;
        case 'completed':
          setReplayState('completed');
          onStatusChange?.('completed');
          break;
        default:
          setReplayState('idle');
          onStatusChange?.('idle');
      }
    });

    replayService.onProgress((progressData: ReplayProgress) => {
      setProgress(progressData);
    });

    replayService.onCandle((data) => {
      onReplayData?.(data);
    });

    replayService.onTick((data) => {
      onReplayData?.(data);
    });

    replayService.onFinished(() => {
      setReplayState('completed');
      onStatusChange?.('completed');
    });

    return () => {
      replayService.destroy();
    };
  }, [onReplayData, onStatusChange]);

  // Criar sessão de replay
  const createReplaySession = async () => {
    try {
      const config: ReplayConfig = {
        account_id: 'default', // Temporário
        symbol,
        timeframe,
        start_date: startDate,
        end_date: endDate,
        speed,
        mode,
      };

      const sessionId = await replayService.createSession(config);
      replayService.connect(sessionId);
      setIsExpanded(true);
    } catch (error) {
      console.error('Error creating replay session:', error);
      // TODO: Mostrar toast de erro
    }
  };

  // Iniciar replay
  const handlePlay = () => {
    replayService.play();
  };

  // Pausar replay
  const handlePause = () => {
    replayService.pause();
  };

  // Parar replay
  const handleStop = () => {
    replayService.stop();
    setReplayState('idle');
    setProgress(null);
  };

  // Seek para posição específica
  const handleSeek = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!progress || !progressBarRef.current) return;

    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = (clickX / rect.width) * 100;
    
    // Calcular timestamp baseado na porcentagem
    const totalDuration = new Date(progress.current_time).getTime() - new Date(startDate).getTime();
    const targetTime = new Date(new Date(startDate).getTime() + (totalDuration * percentage / 100));
    
    replayService.seek(targetTime.toISOString());
  };

  // Ajustar velocidade
  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed);
    replayService.setSpeed(newSpeed);
  };

  // Formatar data para exibição
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Renderizar status badge
  const renderStatusBadge = () => {
    switch (replayState) {
      case 'playing':
        return (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-green-600 font-medium">● Reproduzindo</span>
          </div>
        );
      case 'paused':
        return (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-yellow-500 rounded-full" />
            <span className="text-yellow-600 font-medium">● Pausado</span>
          </div>
        );
      case 'completed':
        return (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-green-600 font-medium">✓ Replay Concluído</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-gray-400 rounded-full" />
            <span className="text-gray-600 font-medium">● Inativo</span>
          </div>
        );
    }
  };

  // Renderizar header (sempre visível)
  const renderHeader = () => (
    <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-t-lg">
      <div className="flex items-center gap-3">
        <Play className="w-4 h-4 text-gray-600" />
        <span className="font-medium text-gray-800">Replay de Mercado</span>
        {renderStatusBadge()}
      </div>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-1 hover:bg-gray-100 rounded transition-colors"
      >
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-600" />
        )}
      </button>
    </div>
  );

  // Renderizar painel de configuração
  const renderConfigPanel = () => (
    <div className="p-4 bg-gray-50 border border-gray-200 space-y-3">
      {/* Linha 1: Par e Timeframe */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 flex-1">
          <label className="text-sm font-medium text-gray-700">Par:</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {SYMBOLS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Timeframe:</label>
          <div className="flex gap-1">
            {TIMEFRAMES.map(tf => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  timeframe === tf
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Linha 2: Datas */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 flex-1">
          <Calendar className="w-4 h-4 text-gray-500" />
          <label className="text-sm font-medium text-gray-700">Data início:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div className="flex items-center gap-2 flex-1">
          <Calendar className="w-4 h-4 text-gray-500" />
          <label className="text-sm font-medium text-gray-700">Data fim:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Linha 3: Velocidade */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Velocidade:</label>
        <div className="flex gap-1">
          {SPEEDS.map(s => (
            <button
              key={s}
              onClick={() => handleSpeedChange(s)}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                speed === s
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Linha 4: Modo */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Modo:</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              value="candle"
              checked={mode === 'candle'}
              onChange={(e) => setMode(e.target.value as 'candle' | 'tick')}
              className="text-blue-500 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Candle a candle</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              value="tick"
              checked={mode === 'tick'}
              onChange={(e) => setMode(e.target.value as 'candle' | 'tick')}
              className="text-blue-500 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Tick a tick</span>
          </label>
        </div>
      </div>

      {/* Botão Iniciar */}
      <button
        onClick={createReplaySession}
        className="w-full py-2 bg-green-500 text-white font-medium rounded-md hover:bg-green-600 transition-colors"
      >
        ▶ Iniciar Replay
      </button>
    </div>
  );

  // Renderizar painel de reprodução
  const renderPlaybackPanel = () => {
    if (!progress) return null;

    return (
      <div className="p-4 bg-gray-50 border border-gray-200 space-y-4">
        {/* Info */}
        <div className="text-sm text-gray-600 text-center">
          {symbol} · {timeframe} · {new Date(startDate).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })} · 
          {mode === 'candle' ? 'Candle' : 'Tick'} {progress.processed_ticks}/{progress.total_ticks}
        </div>

        {/* Barra de Progresso */}
        <div className="space-y-2">
          <div
            ref={progressBarRef}
            onClick={handleSeek}
            className="w-full h-2 bg-gray-200 rounded-full cursor-pointer relative"
          >
            <div
              className="h-full bg-blue-500 rounded-full transition-all"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
          <div className="text-xs text-gray-600 text-center">
            {progress.progress.toFixed(1)}% · {formatDate(progress.current_time)}
          </div>
        </div>

        {/* Controles */}
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => replayService.seek(startDate)}
            className="p-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
            title="Início"
          >
            <SkipBack className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => replayService.seek(new Date(progress.current_time).getTime() - 10000)}
            className="p-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
            title="-10s"
          >
            <SkipBack className="w-3 h-3" />
          </button>

          <button
            onClick={replayState === 'playing' ? handlePause : handlePlay}
            className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
            style={{ width: '48px', height: '48px' }}
          >
            {replayState === 'playing' ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5" />
            )}
          </button>

          <button
            onClick={() => replayService.seek(new Date(progress.current_time).getTime() + 10000)}
            className="p-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
            title="+10s"
          >
            <SkipForward className="w-3 h-3" />
          </button>

          <button
            onClick={handleStop}
            className="p-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            title="Parar"
          >
            <Square className="w-4 h-4" />
          </button>
        </div>

        {/* Velocidade em tempo real */}
        <div className="flex items-center justify-center gap-2">
          <span className="text-sm text-gray-600">Velocidade:</span>
          <div className="flex gap-1">
            {SPEEDS.map(s => (
              <button
                key={s}
                onClick={() => handleSpeedChange(s)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  speed === s
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Renderizar painel concluído
  const renderCompletedPanel = () => (
    <div className="p-4 bg-gray-50 border border-gray-200 space-y-3">
      <div className="text-center text-green-600 font-medium">
        ✓ Replay concluído com sucesso!
      </div>
      <div className="flex gap-2">
        <button
          onClick={createReplaySession}
          className="flex-1 py-2 bg-blue-500 text-white font-medium rounded-md hover:bg-blue-600 transition-colors"
        >
          Novo Replay
        </button>
        <button
          onClick={() => {
            handleStop();
            setIsExpanded(false);
          }}
          className="flex-1 py-2 bg-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-400 transition-colors"
        >
          Fechar
        </button>
      </div>
    </div>
  );

  return (
    <div className="absolute bottom-4 left-4 right-4 z-10 max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        {renderHeader()}
        
        {isExpanded && (
          <>
            {replayState === 'idle' && renderConfigPanel()}
            {(replayState === 'playing' || replayState === 'paused') && renderPlaybackPanel()}
            {replayState === 'completed' && renderCompletedPanel()}
          </>
        )}
      </div>
    </div>
  );
}
