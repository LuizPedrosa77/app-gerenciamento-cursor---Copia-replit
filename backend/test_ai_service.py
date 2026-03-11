"""
Teste do serviço de IA do Trade.
"""
import asyncio
import uuid
from datetime import datetime, timedelta

from app.core.database import AsyncSessionLocal
from app.services.ai_service import ai_service


async def test_ai_service():
    """Testa o serviço de IA com dados mock."""
    
    # Criar workspace_id e user_id de teste
    workspace_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as db:
        print("🧪 Testando AI Service...")
        print(f"Workspace ID: {workspace_id}")
        print(f"User ID: {user_id}")
        
        # Testar construção de contexto
        print("\n📊 Testando construção de contexto...")
        context = ai_service.build_trading_context(workspace_id, user_id, db)
        
        if "error" in context:
            print(f"❌ Erro no contexto: {context['error']}")
        else:
            print("✅ Contexto construído com sucesso!")
            print(f"📋 Resumo contas: {len(context.get('accounts_summary', []))}")
            print(f"📈 Trades recentes: {len(context.get('recent_trades', []))}")
            print(f"📊 Métricas: {context.get('metrics', {})}")
            print(f"📝 Notas diárias: {len(context.get('daily_notes', []))}")
            print(f"🎯 Metas: {context.get('goals', {})}")
            print(f"🔥 Sequências: {context.get('streaks', {})}")
        
        # Testar chat com IA (se API key configurada)
        print("\n🤖 Testando chat com IA...")
        test_message = "Analise minha performance e me dê 3 dicas para melhorar"
        
        try:
            response_count = 0
            async for chunk in ai_service.chat_with_ai(
                message=test_message,
                context=context,
                history=[]
            ):
                print(f"Chunk {response_count}: {chunk}")
                response_count += 1
                if response_count > 5:  # Limitar para teste
                    break
            
            print("✅ Streaming funcionando!")
        except Exception as e:
            print(f"❌ Erro no streaming: {e}")
        
        # Testar análise de sentimento
        print("\n💭 Testando análise de sentimento...")
        test_texts = [
            "Hoje foi um ótimo dia, ganhei bem!",
            "Frustrante, perdi muito hoje",
            "Dia normal, nem ganhei nem perdi"
        ]
        
        for text in test_texts:
            sentiment = ai_service._analyze_sentiment(text)
            print(f"Texto: '{text}' -> Sentimento: {sentiment}")


if __name__ == "__main__":
    asyncio.run(test_ai_service())
