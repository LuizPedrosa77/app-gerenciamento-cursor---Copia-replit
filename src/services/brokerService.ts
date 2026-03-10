/**
 * Serviço para gerenciamento de conexões com corretoras
 */
import { api } from './api';

export interface BrokerConnection {
  id: string;
  workspace_id: string;
  name: string;
  broker: string;
  server: string;
  login: string;
  password?: string; // Encriptado
  api_key?: string; // Encriptado
  is_active: boolean;
  is_connected: boolean;
  last_sync_at?: string;
  sync_status: 'idle' | 'syncing' | 'success' | 'error';
  sync_error?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateConnectionData {
  name: string;
  broker: string;
  server: string;
  login: string;
  password: string;
  api_key?: string;
  is_active?: boolean;
}

export interface UpdateConnectionData {
  name?: string;
  server?: string;
  login?: string;
  password?: string;
  api_key?: string;
  is_active?: boolean;
}

export interface SyncResult {
  success: boolean;
  message: string;
  synced_trades?: number;
  synced_accounts?: number;
  errors?: string[];
  duration?: number;
}

export interface ConnectionTest {
  success: boolean;
  message: string;
  latency?: number;
  server_time?: string;
  account_info?: {
    balance: number;
    equity: number;
    margin: number;
    free_margin: number;
    currency: string;
  };
}

class BrokerService {
  /**
   * Lista todas as conexões com corretoras
   */
  async listConnections(): Promise<BrokerConnection[]> {
    try {
      const response = await api.get<BrokerConnection[]>('/api/v1/brokers/connections');
      return response.data;
    } catch (error) {
      console.error('List connections error:', error);
      throw error;
    }
  }

  /**
   * Obtém detalhes de uma conexão específica
   */
  async getConnection(connectionId: string): Promise<BrokerConnection> {
    try {
      const response = await api.get<BrokerConnection>(`/api/v1/brokers/connections/${connectionId}`);
      return response.data;
    } catch (error) {
      console.error('Get connection error:', error);
      throw error;
    }
  }

  /**
   * Cria uma nova conexão com corretora
   */
  async createConnection(data: CreateConnectionData): Promise<BrokerConnection> {
    try {
      const response = await api.post<BrokerConnection>('/api/v1/brokers/connections', data);
      return response.data;
    } catch (error) {
      console.error('Create connection error:', error);
      throw error;
    }
  }

  /**
   * Atualiza uma conexão existente
   */
  async updateConnection(connectionId: string, data: UpdateConnectionData): Promise<BrokerConnection> {
    try {
      const response = await api.put<BrokerConnection>(`/api/v1/brokers/connections/${connectionId}`, data);
      return response.data;
    } catch (error) {
      console.error('Update connection error:', error);
      throw error;
    }
  }

  /**
   * Exclui uma conexão
   */
  async deleteConnection(connectionId: string): Promise<void> {
    try {
      await api.delete(`/api/v1/brokers/connections/${connectionId}`);
    } catch (error) {
      console.error('Delete connection error:', error);
      throw error;
    }
  }

  /**
   * Testa uma conexão com a corretora
   */
  async testConnection(connectionId: string): Promise<ConnectionTest> {
    try {
      const response = await api.post<ConnectionTest>(`/api/v1/brokers/connections/${connectionId}/test`);
      return response.data;
    } catch (error) {
      console.error('Test connection error:', error);
      throw error;
    }
  }

  /**
   * Inicia sincronização do histórico
   */
  async syncHistory(connectionId: string, options?: {
    start_date?: string;
    end_date?: string;
    symbols?: string[];
    accounts?: string[];
  }): Promise<SyncResult> {
    try {
      const params = new URLSearchParams();
      
      if (options) {
        Object.entries(options).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
              value.forEach(v => params.append(key, v.toString()));
            } else {
              params.append(key, value.toString());
            }
          }
        });
      }

      const response = await api.post<SyncResult>(`/api/v1/brokers/connections/${connectionId}/sync?${params}`);
      return response.data;
    } catch (error) {
      console.error('Sync history error:', error);
      throw error;
    }
  }

  /**
   * Para sincronização em andamento
   */
  async stopSync(connectionId: string): Promise<void> {
    try {
      await api.post(`/api/v1/brokers/connections/${connectionId}/stop-sync`);
    } catch (error) {
      console.error('Stop sync error:', error);
      throw error;
    }
  }

  /**
   * Obtém status da sincronização
   */
  async getSyncStatus(connectionId: string): Promise<any> {
    try {
      const response = await api.get<any>(`/api/v1/brokers/connections/${connectionId}/sync-status`);
      return response.data;
    } catch (error) {
      console.error('Get sync status error:', error);
      throw error;
    }
  }

  /**
   * Obtém histórico de sincronizações
   */
  async getSyncHistory(connectionId: string): Promise<any[]> {
    try {
      const response = await api.get<any[]>(`/api/v1/brokers/connections/${connectionId}/sync-history`);
      return response.data;
    } catch (error) {
      console.error('Get sync history error:', error);
      throw error;
    }
  }

  /**
   * Obtém símbolos disponíveis na corretora
   */
  async getSymbols(connectionId: string): Promise<any[]> {
    try {
      const response = await api.get<any[]>(`/api/v1/brokers/connections/${connectionId}/symbols`);
      return response.data;
    } catch (error) {
      console.error('Get symbols error:', error);
      throw error;
    }
  }

  /**
   * Obtém contas da corretora
   */
  async getAccounts(connectionId: string): Promise<any[]> {
    try {
      const response = await api.get<any[]>(`/api/v1/brokers/connections/${connectionId}/accounts`);
      return response.data;
    } catch (error) {
      console.error('Get accounts error:', error);
      throw error;
    }
  }

  /**
   * Obtém corretoras disponíveis
   */
  async getAvailableBrokers(): Promise<any[]> {
    try {
      const response = await api.get<any[]>('/api/v1/brokers/available');
      return response.data;
    } catch (error) {
      console.error('Get available brokers error:', error);
      throw error;
    }
  }

  /**
   * Valida credenciais da corretora
   */
  async validateCredentials(data: {
    broker: string;
    server: string;
    login: string;
    password: string;
    api_key?: string;
  }): Promise<ConnectionTest> {
    try {
      const response = await api.post<ConnectionTest>('/api/v1/brokers/validate-credentials', data);
      return response.data;
    } catch (error) {
      console.error('Validate credentials error:', error);
      throw error;
    }
  }

  /**
   * Importa contas da corretora
   */
  async importAccounts(connectionId: string): Promise<{
    imported: number;
    errors: string[];
  }> {
    try {
      const response = await api.post<any>(`/api/v1/brokers/connections/${connectionId}/import-accounts`);
      return response.data;
    } catch (error) {
      console.error('Import accounts error:', error);
      throw error;
    }
  }

  /**
   * Ativa/desativa uma conexão
   */
  async toggleConnection(connectionId: string, isActive: boolean): Promise<BrokerConnection> {
    try {
      const response = await api.patch<BrokerConnection>(`/api/v1/brokers/connections/${connectionId}`, {
        is_active: isActive
      });
      return response.data;
    } catch (error) {
      console.error('Toggle connection error:', error);
      throw error;
    }
  }

  /**
   * Obtém métricas da conexão
   */
  async getConnectionMetrics(connectionId: string, period?: {
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    try {
      const params = new URLSearchParams();
      
      if (period) {
        Object.entries(period).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, value.toString());
          }
        });
      }

      const response = await api.get<any>(`/api/v1/brokers/connections/${connectionId}/metrics?${params}`);
      return response.data;
    } catch (error) {
      console.error('Get connection metrics error:', error);
      throw error;
    }
  }
}

// Exportar instância única do serviço
export const brokerService = new BrokerService();

export default brokerService;
