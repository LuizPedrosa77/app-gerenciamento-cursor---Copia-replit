/**
 * Serviço para gerenciamento de trades
 */
import { api } from './api';

export interface Trade {
  id: string;
  workspace_id: string;
  account_id: string;
  symbol: string;
  pair: string;
  side: string;
  dir: string;
  volume: number;
  lots: number;
  open_time: string;
  close_time: string;
  open_price: number;
  close_price: number;
  stop_loss?: number;
  take_profit?: number;
  commission: number;
  swap: number;
  taxes: number;
  gross_profit: number;
  net_profit: number;
  pnl: number;
  profit_currency: string;
  status: string;
  result: string;
  magic_number?: number;
  strategy_name?: string;
  comment?: string;
  screenshot_url?: string;
  screenshot_caption?: string;
  has_vm: boolean;
  vm_lots: number;
  vm_result: string;
  vm_net_profit: number;
  date?: string;
  year?: number;
  month?: number;
  created_at: string;
  updated_at: string;
  tags: any[];
}

export interface CreateTradeData {
  account_id: string;
  symbol: string;
  pair: string;
  side: string;
  dir: string;
  volume: number;
  lots: number;
  open_time: string;
  close_time?: string;
  open_price: number;
  close_price?: number;
  stop_loss?: number;
  take_profit?: number;
  commission?: number;
  swap?: number;
  taxes?: number;
  gross_profit?: number;
  net_profit?: number;
  pnl?: number;
  profit_currency?: string;
  status?: string;
  result?: string;
  magic_number?: number;
  strategy_name?: string;
  comment?: string;
  screenshot_url?: string;
  screenshot_caption?: string;
  has_vm?: boolean;
  vm_lots?: number;
  vm_result?: string;
  vm_net_profit?: number;
  date?: string;
  year?: number;
  month?: number;
  tag_ids?: string[];
}

export interface UpdateTradeData {
  symbol?: string;
  pair?: string;
  side?: string;
  dir?: string;
  volume?: number;
  lots?: number;
  close_time?: string;
  close_price?: number;
  stop_loss?: number;
  take_profit?: number;
  commission?: number;
  swap?: number;
  taxes?: number;
  gross_profit?: number;
  net_profit?: number;
  pnl?: number;
  status?: string;
  result?: string;
  strategy_name?: string;
  comment?: string;
  screenshot_url?: string;
  screenshot_caption?: string;
  has_vm?: boolean;
  vm_lots?: number;
  vm_result?: string;
  vm_net_profit?: number;
  tag_ids?: string[];
}

export interface TradeFilters {
  account_id?: string;
  symbol?: string;
  side?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  min_pnl?: number;
  max_pnl?: number;
  has_screenshot?: boolean;
  tag_ids?: string[];
  page?: number;
  limit?: number;
}

class TradeService {
  /**
   * Lista trades com filtros opcionais
   */
  async listTrades(filters?: TradeFilters): Promise<{
    trades: Trade[];
    total: number;
    page: number;
    limit: number;
  }> {
    try {
      const params = new URLSearchParams();
      
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
              value.forEach(v => params.append(key, v.toString()));
            } else {
              params.append(key, value.toString());
            }
          }
        });
      }

      const response = await api.get(`/api/v1/accounts/trades?${params}`);
      return response.data;
    } catch (error) {
      console.error('List trades error:', error);
      throw error;
    }
  }

  /**
   * Obtém detalhes de um trade específico
   */
  async getTrade(tradeId: string): Promise<Trade> {
    try {
      const response = await api.get<Trade>(`/api/v1/accounts/trades/${tradeId}`);
      return response.data;
    } catch (error) {
      console.error('Get trade error:', error);
      throw error;
    }
  }

  /**
   * Cria um novo trade
   */
  async createTrade(data: CreateTradeData): Promise<Trade> {
    try {
      const response = await api.post<Trade>('/api/v1/accounts/trades', data);
      return response.data;
    } catch (error) {
      console.error('Create trade error:', error);
      throw error;
    }
  }

  /**
   * Atualiza um trade existente
   */
  async updateTrade(tradeId: string, data: UpdateTradeData): Promise<Trade> {
    try {
      const response = await api.put<Trade>(`/api/v1/accounts/trades/${tradeId}`, data);
      return response.data;
    } catch (error) {
      console.error('Update trade error:', error);
      throw error;
    }
  }

  /**
   * Exclui um trade
   */
  async deleteTrade(tradeId: string): Promise<void> {
    try {
      await api.delete(`/api/v1/accounts/trades/${tradeId}`);
    } catch (error) {
      console.error('Delete trade error:', error);
      throw error;
    }
  }

  /**
   * Exclui múltiplos trades
   */
  async deleteMultipleTrades(tradeIds: string[]): Promise<void> {
    try {
      await api.post('/api/v1/accounts/trades/delete-multiple', { trade_ids: tradeIds });
    } catch (error) {
      console.error('Delete multiple trades error:', error);
      throw error;
    }
  }

  /**
   * Faz upload de screenshot para um trade
   */
  async uploadScreenshot(tradeId: string, file: File): Promise<string> {
    try {
      const response = await api.upload(`/api/v1/accounts/trades/${tradeId}/screenshot`, file);
      return response.data.screenshot_url;
    } catch (error) {
      console.error('Upload screenshot error:', error);
      throw error;
    }
  }

  /**
   * Exporta trades em CSV
   */
  async exportCSV(accountId: string, month?: number, year?: number): Promise<Blob> {
    try {
      const params = new URLSearchParams();
      if (month) params.append('month', month.toString());
      if (year) params.append('year', year.toString());

      const response = await api.get(`/api/v1/accounts/trades/export?${params}`, {
        responseType: 'blob'
      });
      
      return response.data;
    } catch (error) {
      console.error('Export CSV error:', error);
      throw error;
    }
  }

  /**
   * Obtém estatísticas dos trades
   */
  async getTradeStats(accountId: string, filters?: {
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (filters?.start_date) params.append('start_date', filters.start_date);
      if (filters?.end_date) params.append('end_date', filters.end_date);

      const response = await api.get<any>(`/api/v1/accounts/trades/stats?${params}`);
      return response.data;
    } catch (error) {
      console.error('Get trade stats error:', error);
      throw error;
    }
  }

  /**
   * Obtém trades por par
   */
  async getTradesByPair(accountId: string): Promise<any[]> {
    try {
      const response = await api.get<any[]>(`/api/v1/accounts/trades/by-pair?account_id=${accountId}`);
      return response.data;
    } catch (error) {
      console.error('Get trades by pair error:', error);
      throw error;
    }
  }

  /**
   * Obtém trades por dia da semana
   */
  async getTradesByWeekday(accountId: string): Promise<any[]> {
    try {
      const response = await api.get<any[]>(`/api/v1/accounts/trades/by-weekday?account_id=${accountId}`);
      return response.data;
    } catch (error) {
      console.error('Get trades by weekday error:', error);
      throw error;
    }
  }

  /**
   * Obtém trades por direção (buy/sell)
   */
  async getTradesByDirection(accountId: string): Promise<any[]> {
    try {
      const response = await api.get<any[]>(`/api/v1/accounts/trades/by-direction?account_id=${accountId}`);
      return response.data;
    } catch (error) {
      console.error('Get trades by direction error:', error);
      throw error;
    }
  }

  /**
   * Obtém os melhores trades
   */
  async getTopTrades(accountId: string, limit: number = 10): Promise<Trade[]> {
    try {
      const response = await api.get<Trade[]>(`/api/v1/accounts/trades/top?account_id=${accountId}&limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Get top trades error:', error);
      throw error;
    }
  }

  /**
   * Obtém os piores trades
   */
  async getWorstTrades(accountId: string, limit: number = 10): Promise<Trade[]> {
    try {
      const response = await api.get<Trade[]>(`/api/v1/accounts/trades/worst?account_id=${accountId}&limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Get worst trades error:', error);
      throw error;
    }
  }

  /**
   * Duplica um trade
   */
  async duplicateTrade(tradeId: string): Promise<Trade> {
    try {
      const response = await api.post<Trade>(`/api/v1/accounts/trades/${tradeId}/duplicate`);
      return response.data;
    } catch (error) {
      console.error('Duplicate trade error:', error);
      throw error;
    }
  }

  /**
   * Importa trades de um arquivo CSV
   */
  async importCSV(accountId: string, file: File): Promise<{
    imported: number;
    errors: string[];
  }> {
    try {
      const response = await api.upload(`/api/v1/accounts/trades/import?account_id=${accountId}`, file);
      return response.data;
    } catch (error) {
      console.error('Import CSV error:', error);
      throw error;
    }
  }
}

// Exportar instância única do serviço
export const tradeService = new TradeService();

export default tradeService;
