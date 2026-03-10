/**
 * Type definitions for Replay System
 */

declare global {
  interface Window {
    TradingView: any;
  }
}

export interface ReplayTick {
  timestamp: string;
  bid: number;
  ask: number;
  volume: number;
  symbol_id: string;
}

export interface ReplayCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  symbol_id: string;
}

export interface ReplayProgress {
  progress: number;
  processed_ticks: number;
  total_ticks: number;
  current_time: string;
}

export interface ReplayStatus {
  status: string;
  current_time?: string;
  speed?: number;
  progress?: number;
  action?: string;
}
