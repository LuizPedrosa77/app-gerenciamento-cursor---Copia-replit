/**
 * Serviço para gerenciamento de contas de trading
 */
import { api } from './api';

export interface Account {
  id: string;
  workspace_id: string;
  name: string;
  currency: string;
  platform: string;
  is_demo: boolean;
  initial_balance: number;
  current_balance: number;
  leverage?: number;
  monthly_goal_amount: number;
  biweekly_goal_amount: number;
  created_at: string;
  updated_at: string;
  closed_at?: string;
}

export interface CreateAccountData {
  name: string;
  currency?: string;
  platform?: string;
  is_demo?: boolean;
  initial_balance?: number;
  leverage?: number;
  monthly_goal_amount?: number;
  biweekly_goal_amount?: number;
}

export interface UpdateAccountData {
  name?: string;
  currency?: string;
  platform?: string;
  is_demo?: boolean;
  current_balance?: number;
  leverage?: number;
  monthly_goal_amount?: number;
  biweekly_goal_amount?: number;
  closed_at?: string;
}

export interface TotalBalance {
  total_balance: number;
  total_pnl: number;
  accounts_count: number;
  currency: string;
}

class AccountService {
  /**
   * Lista todas as contas do workspace
   */
  async listAccounts(): Promise<Account[]> {
    try {
      const response = await api.get<Account[]>('/api/v1/accounts');
      return response.data;
    } catch (error) {
      console.error('List accounts error:', error);
      throw error;
    }
  }

  /**
   * Obtém detalhes de uma conta específica
   */
  async getAccount(accountId: string): Promise<Account> {
    try {
      const response = await api.get<Account>(`/api/v1/accounts/${accountId}`);
      return response.data;
    } catch (error) {
      console.error('Get account error:', error);
      throw error;
    }
  }

  /**
   * Cria uma nova conta
   */
  async createAccount(data: CreateAccountData): Promise<Account> {
    try {
      const response = await api.post<Account>('/api/v1/accounts', data);
      return response.data;
    } catch (error) {
      console.error('Create account error:', error);
      throw error;
    }
  }

  /**
   * Atualiza uma conta existente
   */
  async updateAccount(accountId: string, data: UpdateAccountData): Promise<Account> {
    try {
      const response = await api.put<Account>(`/api/v1/accounts/${accountId}`, data);
      return response.data;
    } catch (error) {
      console.error('Update account error:', error);
      throw error;
    }
  }

  /**
   * Exclui uma conta
   */
  async deleteAccount(accountId: string): Promise<void> {
    try {
      await api.delete(`/api/v1/accounts/${accountId}`);
    } catch (error) {
      console.error('Delete account error:', error);
      throw error;
    }
  }

  /**
   * Obtém o saldo total consolidado de todas as contas
   */
  async getTotalBalance(): Promise<TotalBalance> {
    try {
      const response = await api.get<TotalBalance>('/api/v1/accounts/total-balance');
      return response.data;
    } catch (error) {
      console.error('Get total balance error:', error);
      throw error;
    }
  }

  /**
   * Sincroniza uma conta com a corretora
   */
  async syncAccount(accountId: string): Promise<void> {
    try {
      await api.post(`/api/v1/accounts/${accountId}/sync`);
    } catch (error) {
      console.error('Sync account error:', error);
      throw error;
    }
  }

  /**
   * Obtém o histórico de sincronização de uma conta
   */
  async getSyncHistory(accountId: string): Promise<any[]> {
    try {
      const response = await api.get<any[]>(`/api/v1/accounts/${accountId}/sync-history`);
      return response.data;
    } catch (error) {
      console.error('Get sync history error:', error);
      throw error;
    }
  }

  /**
   * Testa a conexão com a corretora
   */
  async testConnection(accountId: string): Promise<any> {
    try {
      const response = await api.post<any>(`/api/v1/accounts/${accountId}/test-connection`);
      return response.data;
    } catch (error) {
      console.error('Test connection error:', error);
      throw error;
    }
  }

  /**
   * Obtém métricas da conta
   */
  async getAccountMetrics(accountId: string, filters?: {
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (filters?.start_date) params.append('start_date', filters.start_date);
      if (filters?.end_date) params.append('end_date', filters.end_date);

      const response = await api.get<any>(`/api/v1/accounts/${accountId}/metrics?${params}`);
      return response.data;
    } catch (error) {
      console.error('Get account metrics error:', error);
      throw error;
    }
  }

  /**
   * Exporta dados da conta em CSV
   */
  async exportAccountData(accountId: string, format: 'csv' | 'excel' = 'csv'): Promise<Blob> {
    try {
      const response = await api.get(`/api/v1/accounts/${accountId}/export?format=${format}`, {
        responseType: 'blob'
      });
      
      return response.data;
    } catch (error) {
      console.error('Export account data error:', error);
      throw error;
    }
  }
}

// Exportar instância única do serviço
export const accountService = new AccountService();

export default accountService;
