# 🤖 Módulo de IA do Trade

## 📋 Visão Geral

Módulo completo de IA especializada em trading forex com contexto total dos dados do usuário, streaming em tempo real e suporte a múltiplos métodos de autenticação.

---

## 🚀 Funcionalidades

### 🎯 **Contexto Completo do Trader**
- **Resumo das contas**: Saldo, P&L total, win rate, metas
- **Trades recentes**: Últimos 50 trades com todos os campos
- **Métricas detalhadas**: Por par, por dia da semana, top/bottom trades
- **Notas diárias**: Últimos 30 dias com análise de sentimento
- **Progresso de metas**: Mensal e quinzenal com % atingido
- **Sequências**: Win/loss streaks atuais e históricas

### 💬 **Chat com IA Especializada**
- **System prompt personalizado**: Especialista em trading forex
- **Streaming SSE**: Respostas em tempo real
- **Contexto awareness**: Usa dados reais do trader
- **Português BR**: Respostas nativas em português do Brasil
- **Múltiplos modelos**: Suporte GPT-4, GPT-3.5

### 🔐 **Autenticação Flexível**
- **Bearer Token**: Para usuários autenticados
- **API Key**: Para integrações (n8n, webhooks)
- **Workspace isolamento**: Cada usuário vê apenas seus dados

### 💾 **Gerenciamento de Conversas**
- **CRUD completo**: Salvar, listar, atualizar, excluir
- **Histórico persistente**: Conversas mantidas no banco
- **Busca por workspace**: Organização por projeto

---

## 📁 Estrutura de Arquivos

```
backend/
├── app/
│   ├── services/
│   │   └── ai_service.py          # Serviço principal de IA
│   ├── api/v1/endpoints/
│   │   └── ai_trade.py            # Endpoints HTTP
│   └── models/
│       └── profile.py              # Model AIConversation
├── requirements.txt               # openai>=1.0.0
├── .env.example                 # OPENAI_API_KEY
└── test_ai_service.py           # Teste do módulo
```

---

## 🔧 Configuração

### 1. **Variáveis de Ambiente**

```bash
# .env
OPENAI_API_KEY=sk-proj-sua-chave-openai-aqui
```

### 2. **Instalar Dependências**

```bash
pip install -r requirements.txt
```

### 3. **Executar Migrations**

```bash
alembic upgrade head
```

---

## 📡 Endpoints Disponíveis

### 💬 **Chat com IA**

#### `POST /api/v1/ai/chat`
**Autenticação**: Bearer Token ou X-API-Key

```json
{
  "message": "Analise minha performance e me dê dicas",
  "conversation_history": [],
  "workspace_id": "uuid-do-workspace",
  "user_id": "uuid-do-usuario"  // Opcional para API Key
}
```

**Response**: Streaming SSE
```javascript
const eventSource = new EventSource('/api/v1/ai/chat', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer seu-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(request)
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'chunk') {
    console.log(data.content); // Texto parcial
  } else if (data.type === 'done') {
    console.log('Resposta completa!');
  } else if (data.type === 'error') {
    console.error('Erro:', data.content);
  }
};
```

### 📚 **Gerenciamento de Conversas**

#### `GET /api/v1/ai/conversations`
Lista todas as conversas do usuário.

```json
[
  {
    "id": "uuid",
    "title": "Análise de Performance",
    "workspace_id": "uuid",
    "messages": [...],
    "created_at": "2024-01-10T12:00:00",
    "updated_at": "2024-01-10T12:30:00"
  }
]
```

#### `POST /api/v1/ai/conversations`
Salva nova conversa.

```json
{
  "title": "Título da Conversa",
  "workspace_id": "uuid",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

#### `PUT /api/v1/ai/conversations/{id}`
Atualiza conversa existente.

#### `DELETE /api/v1/ai/conversations/{id}`
Remove conversa.

### 📊 **Contexto e Debug**

#### `GET /api/v1/ai/context/{workspace_id}`
Retorna o contexto completo de trading (para debugging).

```json
{
  "timestamp": "2024-01-10T12:00:00",
  "accounts_summary": [...],
  "recent_trades": [...],
  "metrics": {
    "total_trades": 150,
    "win_rate": 68.5,
    "profit_factor": 1.42,
    "by_pair": [...],
    "by_weekday": [...]
  },
  "daily_notes": [...],
  "goals": {
    "monthly": {"goal": 5000, "current": 3450, "percentage": 69},
    "biweekly": {"goal": 2500, "current": 1200, "percentage": 48}
  },
  "streaks": {
    "current_win_streak": 3,
    "current_loss_streak": 0,
    "max_win_streak": 8,
    "max_loss_streak": 4
  }
}
```

#### `GET /api/v1/ai/health`
Verifica saúde do serviço de IA.

```json
{
  "status": "healthy",
  "model": "gpt-4",
  "openai_configured": true,
  "service_version": "1.0.0"
}
```

---

## 🧪 Testes

### **Executar Teste do Serviço**

```bash
python test_ai_service.py
```

Saída esperada:
```
🧪 Testando AI Service...
Workspace ID: 123e4567-e89b-12d3-a456-426614174000
User ID: 987e6543-e21b-43d2-a456-426614174999

📊 Testando construção de contexto...
✅ Contexto construído com sucesso!
📋 Resumo contas: 2
📈 Trades recentes: 50
📊 Métricas: {...}
📝 Notas diárias: 15
🎯 Metas: {...}
🔥 Sequências: {...}

🤖 Testando chat com IA...
✅ Streaming funcionando!

💭 Testando análise de sentimento...
Texto: 'Hoje foi um ótimo dia, ganhei bem!' -> Sentimento: positivo
Texto: 'Frustrante, perdi muito hoje' -> Sentimento: negativo
Texto: 'Dia normal, nem ganhei nem perdi' -> Sentimento: neutro
```

---

## 🎯 Casos de Uso

### 1. **Análise de Performance**
```
Usuário: "Analise minha performance deste mês"
IA: "Com base nos seus 42 trades deste mês, seu win rate é 72%...
```

### 2. **Sugestões de Melhoria**
```
Usuário: "Como posso melhorar meu drawdown?"
IA: "Analisando seu histórico, seu maior drawdown foi de 15%...
```

### 3. **Identificação de Padrões**
```
Usuário: "Tenho algum padrão nos meus trades?"
IA: "Sim! Identifiquei que você performa 23% melhor...
```

### 4. **Gestão de Risco**
```
Usuário: "Qual o tamanho ideal de posição para mim?"
IA: "Com base no seu capital atual e histórico...
```

---

## 🔒 Segurança

### **API Key Validation**
- Chaves fortes e únicas por cliente
- Rate limiting por API Key
- Logs de acesso completos

### **Isolamento de Dados**
- Cada usuário acessa apenas seus workspaces
- Sanitização completa de inputs
- Validação de UUIDs

### **OpenAI Security**
- API keys armazenadas como variáveis de ambiente
- Rate limiting automático da OpenAI
- Tokens limitados por requisição

---

## 📈 Performance

### **Otimizações Implementadas**
- **Context caching**: Dados cacheados por 5 minutos
- **Streaming**: Respostas em tempo real sem buffering
- **Batch queries**: Consultas otimizadas ao banco
- **Lazy loading**: Carrega apenas dados necessários

### **Métricas Esperadas**
- **Resposta inicial**: < 500ms
- **Streaming**: Primeiro chunk em < 1s
- **Contexto completo**: < 2s
- **Concurrent users**: 100+ suportados

---

## 🚀 Deploy

### **Produção**
```bash
# 1. Setar variáveis de ambiente
export OPENAI_API_KEY=sk-proj-sua-chave

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Rodar migrations
alembic upgrade head

# 4. Iniciar serviço
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **Docker**
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    # ... outras configurações
```

---

## 🐛 Troubleshooting

### **Erro Comum: "OpenAI API key not configured"**
```bash
# Verificar variável de ambiente
echo $OPENAI_API_KEY

# Ou verificar .env
cat .env | grep OPENAI_API_KEY
```

### **Erro Comum: "Invalid workspace_id"**
- Verifique se o UUID está correto
- Confirme se o usuário tem acesso ao workspace

### **Erro Comum: "Streaming error"**
- Verifique conexão com OpenAI
- Confirme se a API key tem créditos
- Verifique rate limits

---

## 📚 Documentação Adicional

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [FastAPI Streaming Responses](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

## 🎉 Pronto para Uso!

O módulo de IA está completamente implementado e pronto para produção. 

**Próximos passos:**
1. Configure sua API Key da OpenAI
2. Execute as migrations
3. Teste com o script fornecido
4. Integre com o frontend

**Suporte total para trading forex especializado!** 🚀
