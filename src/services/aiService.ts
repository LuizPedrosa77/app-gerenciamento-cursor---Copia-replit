/**
 * Serviço para IA do Trade com streaming SSE
 */
import { api } from './api';

export interface AIConversation {
  id: string;
  title: string;
  workspace_id: string;
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface AIModelsResponse {
  models: Array<{
    id: string;
    name: string;
    description: string;
    max_tokens: number;
    cost_per_token: number;
  }>;
}

class AIService {
  private eventSource: EventSource | null = null;
  private onChunkCallback: ((text: string) => void) | null = null;
  private onDoneCallback: (() => void) | null = null;
  private onErrorCallback: ((error: string) => void) | null = null;

  /**
   * Inicia chat com streaming SSE
   */
  async chatStream(
    message: string,
    history: ChatMessage[] = [],
    options: {
      workspace_id?: string;
      model?: string;
      temperature?: number;
      max_tokens?: number;
    } = {}
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Limpar callback anterior
        this.cleanup();

        // Preparar dados da requisição
        const requestData = {
          message,
          conversation_history: history,
          workspace_id: options.workspace_id,
          model: options.model || 'gpt-4',
          temperature: options.temperature || 0.7,
          max_tokens: options.max_tokens || 1000,
        };

        // Construir URL com parâmetros
        const params = new URLSearchParams();
        Object.entries(requestData).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, value.toString());
          }
        });

        // Criar EventSource para SSE
        this.eventSource = new EventSource(
          `${import.meta.env.VITE_API_URL}/api/v1/ai/chat?${params.toString()}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json',
            }
          }
        );

        // Configurar handlers
        this.eventSource.onopen = () => {
          console.log('AI Chat SSE connection opened');
        };

        this.eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            switch (data.type) {
              case 'chunk':
                if (this.onChunkCallback) {
                  this.onChunkCallback(data.content);
                }
                break;

              case 'done':
                if (this.onDoneCallback) {
                  this.onDoneCallback();
                }
                resolve();
                break;

              case 'error':
                const errorMsg = data.content || 'Erro desconhecido';
                if (this.onErrorCallback) {
                  this.onErrorCallback(errorMsg);
                }
                reject(new Error(errorMsg));
                break;

              default:
                console.warn('Unknown SSE message type:', data.type);
            }
          } catch (parseError) {
            console.error('Error parsing SSE message:', parseError);
            if (this.onErrorCallback) {
              this.onErrorCallback('Erro ao processar resposta');
            }
            reject(new Error('Parse error'));
          }
        };

        this.eventSource.onerror = (event) => {
          console.error('SSE error:', event);
          const errorMsg = 'Erro na conexão com IA';
          if (this.onErrorCallback) {
            this.onErrorCallback(errorMsg);
          }
          reject(new Error(errorMsg));
        };

        this.eventSource.onclose = () => {
          console.log('SSE connection closed');
          this.cleanup();
        };

      } catch (error) {
        console.error('Chat stream error:', error);
        reject(error);
      }
    });
  }

  /**
   * Configura callbacks para o streaming
   */
  onChunk(callback: (text: string) => void): void {
    this.onChunkCallback = callback;
  }

  onDone(callback: () => void): void {
    this.onDoneCallback = callback;
  }

  onError(callback: (error: string) => void): void {
    this.onErrorCallback = callback;
  }

  /**
   * Para o streaming e limpa recursos
   */
  cleanup(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    this.onChunkCallback = null;
    this.onDoneCallback = null;
    this.onErrorCallback = null;
  }

  /**
   * Obtém conversas do usuário
   */
  async getConversations(): Promise<AIConversation[]> {
    try {
      const response = await api.get<AIConversation[]>('/api/v1/ai/conversations');
      return response.data;
    } catch (error) {
      console.error('Get conversations error:', error);
      throw error;
    }
  }

  /**
   * Salva uma conversa
   */
  async saveConversation(conversation: {
    title: string;
    workspace_id: string;
    messages: ChatMessage[];
  }): Promise<AIConversation> {
    try {
      const response = await api.post<AIConversation>('/api/v1/ai/conversations', conversation);
      return response.data;
    } catch (error) {
      console.error('Save conversation error:', error);
      throw error;
    }
  }

  /**
   * Obtém detalhes de uma conversa
   */
  async getConversation(conversationId: string): Promise<AIConversation> {
    try {
      const response = await api.get<AIConversation>(`/api/v1/ai/conversations/${conversationId}`);
      return response.data;
    } catch (error) {
      console.error('Get conversation error:', error);
      throw error;
    }
  }

  /**
   * Atualiza uma conversa existente
   */
  async updateConversation(conversationId: string, data: {
    title?: string;
    messages?: ChatMessage[];
  }): Promise<AIConversation> {
    try {
      const response = await api.put<AIConversation>(`/api/v1/ai/conversations/${conversationId}`, data);
      return response.data;
    } catch (error) {
      console.error('Update conversation error:', error);
      throw error;
    }
  }

  /**
   * Exclui uma conversa
   */
  async deleteConversation(conversationId: string): Promise<void> {
    try {
      await api.delete(`/api/v1/ai/conversations/${conversationId}`);
    } catch (error) {
      console.error('Delete conversation error:', error);
      throw error;
    }
  }

  /**
   * Obtém modelos de IA disponíveis
   */
  async getAvailableModels(): Promise<AIModelsResponse> {
    try {
      const response = await api.get<AIModelsResponse>('/api/v1/ai/models');
      return response.data;
    } catch (error) {
      console.error('Get available models error:', error);
      throw error;
    }
  }

  /**
   * Verifica saúde do serviço de IA
   */
  async healthCheck(): Promise<{
    status: string;
    model: string;
    openai_configured: boolean;
    service_version: string;
  }> {
    try {
      const response = await api.get<any>('/api/v1/ai/health');
      return response.data;
    } catch (error) {
      console.error('AI health check error:', error);
      throw error;
    }
  }

  /**
   * Obtém contexto completo para debugging
   */
  async getTradingContext(workspaceId: string): Promise<any> {
    try {
      const response = await api.get<any>(`/api/v1/ai/context/${workspaceId}`);
      return response.data;
    } catch (error) {
      console.error('Get trading context error:', error);
      throw error;
    }
  }

  /**
   * Gera sugestões baseadas no contexto atual
   */
  async generateSuggestions(context: {
    recent_trades: number;
    current_pnl: number;
    win_rate: number;
    active_pairs: string[];
  }): Promise<string[]> {
    try {
      const response = await api.post<string[]>('/api/v1/ai/suggestions', context);
      return response.data;
    } catch (error) {
      console.error('Generate suggestions error:', error);
      throw error;
    }
  }

  /**
   * Analisa sentimento de mensagens
   */
  async analyzeSentiment(text: string): Promise<{
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number;
    emotions: string[];
  }> {
    try {
      const response = await api.post<any>('/api/v1/ai/analyze-sentiment', { text });
      return response.data;
    } catch (error) {
      console.error('Analyze sentiment error:', error);
      throw error;
    }
  }

  /**
   * Obtém estatísticas de uso da IA
   */
  async getUsageStats(period?: {
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

      const response = await api.get<any>(`/api/v1/ai/usage-stats?${params}`);
      return response.data;
    } catch (error) {
      console.error('Get usage stats error:', error);
      throw error;
    }
  }

  /**
   * Limpa conversas antigas
   */
  async clearOldConversations(daysOld: number = 90): Promise<{
    deleted: number;
  }> {
    try {
      const response = await api.delete<any>(`/api/v1/ai/conversations/clear?days_old=${daysOld}`);
      return response.data;
    } catch (error) {
      console.error('Clear old conversations error:', error);
      throw error;
    }
  }

  /**
   * Exporta conversas em formato específico
   */
  async exportConversations(format: 'json' | 'csv' | 'txt' = 'json'): Promise<Blob> {
    try {
      const response = await api.get(`/api/v1/ai/conversations/export?format=${format}`, {
        responseType: 'blob'
      });
      
      return response.data;
    } catch (error) {
      console.error('Export conversations error:', error);
      throw error;
    }
  }
}

// Exportar instância única do serviço
export const aiService = new AIService();

export default aiService;
