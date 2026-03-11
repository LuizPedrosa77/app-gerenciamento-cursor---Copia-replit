"""
Serviço de IA do Trade com contexto completo e streaming.
"""
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, AsyncGenerator, Dict, List

import openai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.core.config import settings
from app.models.trade import Trade
from app.models.account import TradingAccount
from app.models.note import DailyNote
from app.models.user import User, Workspace


class AIService:
    """Serviço de IA especializado em trading forex."""

    def __init__(self):
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4"

    def build_trading_context(self, workspace_id: str, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Busca e monta contexto completo do trader.
        """
        try:
            workspace_uuid = uuid.UUID(workspace_id)
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return {"error": "Invalid workspace_id or user_id"}

        context = {
            "timestamp": datetime.now().isoformat(),
            "workspace_id": workspace_id,
            "user_id": user_id,
        }

        # Resumo das contas
        context["accounts_summary"] = self._get_accounts_summary(workspace_uuid, db)
        
        # Últimos 50 trades
        context["recent_trades"] = self._get_recent_trades(workspace_uuid, db, limit=50)
        
        # Métricas detalhadas
        context["metrics"] = self._calculate_metrics(workspace_uuid, db)
        
        # Notas diárias
        context["daily_notes"] = self._get_daily_notes(workspace_uuid, db, days=30)
        
        # Metas e progresso
        context["goals"] = self._get_goals_progress(workspace_uuid, db)
        
        # Sequências atuais
        context["streaks"] = self._calculate_streaks(workspace_uuid, db)
        
        return context

    async def chat_with_ai(
        self, 
        message: str, 
        context: Dict[str, Any], 
        history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Chama OpenAI GPT-4 com streaming.
        """
        if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
            yield "data: {\"type\": \"error\", \"content\": \"OpenAI API key not configured\"}\n\n"
            return

        # Construir system prompt com contexto
        system_prompt = self._build_system_prompt(context)
        
        # Preparar mensagens para a API
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Adicionar histórico se fornecido
        if history:
            for msg in history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": message})

        try:
            # Streaming response da OpenAI
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1500
            )

            async for chunk in response:
                if chunk.choices:
                    content = chunk.choices[0].delta.get("content", "")
                    if content:
                        safe_content = content.replace('"', '\\"')
                        yield f'data: {{"type": "chunk", "content": "{safe_content}"}}\n\n'

            # Sinal de conclusão
            yield "data: {\"type\": \"done\"}\n\n"

        except Exception as e:
            yield f"data: {{\"type\": \"error\", \"content\": \"Error: {str(e)}\"}}\n\n"

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Constrói o system prompt especializado com contexto do trader.
        """
        # Formatar contexto para o prompt
        context_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        
        system_prompt = f"""Você é o Assistente IA do Gustavo Pedrosa FX, especialista em trading forex e análise de resultados. Você tem acesso completo aos dados de trading do usuário abaixo e deve analisar resultados, identificar padrões, sugerir melhorias e responder dúvidas com base nos dados reais do trader.

REGRAS IMPORTANTES:
- Sempre responda em português do Brasil
- Seja direto, objetivo e use os dados fornecidos para embasar suas respostas
- Nunca invente dados - use apenas o contexto fornecido
- Forneça análises quantitativas quando possível
- Sugira ações concretas e implementáveis
- Mantenha o foco em melhoria de performance e gestão de risco

CONTEXTO COMPLETO DO TRADER:
{context_str}

COMO USAR ESTE CONTEXTO:
1. Analise o resumo das contas para entender a situação atual
2. Use os trades recentes para identificar padrões e tendências
3. Considere as métricas (win rate, profit factor, drawdown) nas análises
4. Leve em conta as notas diárias para entender o estado emocional
5. Verifique o progresso das metas para dar feedback motivacional
6. Use as sequências para identificar padrões de comportamento

EXEMPLOS DE RESPOSTAS ESPERADAS:
- Para análises: "Com base nos seus últimos 50 trades, seu win rate é X%..."
- Para sugestões: "Recomendo reduzir o tamanho da posição em Y para Z%..."
- Para dúvidas: "Olhando seu histórico, você performa melhor em..."

Agora, analise a solicitação do usuário com base neste contexto completo."""
        
        return system_prompt

    def _get_accounts_summary(self, workspace_id: uuid.UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """Busca resumo das contas do workspace."""
        result = db.execute(
            select(TradingAccount).where(
                TradingAccount.workspace_id == workspace_id,
                TradingAccount.closed_at.is_(None)
            )
        )
        accounts = result.scalars().all()
        
        summary = []
        for account in accounts:
            # Calcular P&L total da conta
            trades_result = db.execute(
                select(func.sum(Trade.net_profit)).where(
                    Trade.account_id == account.id
                )
            )
            total_pnl = trades_result.scalar() or Decimal("0")
            
            # Calcular win rate
            trades_count_result = db.execute(
                select(func.count(Trade.id)).where(
                    Trade.account_id == account.id
                )
            )
            trades_count = trades_count_result.scalar() or 0
            
            wins_result = db.execute(
                select(func.count(Trade.id)).where(
                    and_(
                        Trade.account_id == account.id,
                        Trade.net_profit >= 0
                    )
                )
            )
            wins = wins_result.scalar() or 0
            win_rate = (wins / trades_count * 100) if trades_count > 0 else 0
            
            summary.append({
                "id": str(account.id),
                "name": account.name,
                "balance": float(account.current_balance),
                "initial_balance": float(account.initial_balance),
                "total_pnl": float(total_pnl),
                "current_balance_with_pnl": float(account.current_balance + total_pnl),
                "trades_count": trades_count,
                "win_rate": round(win_rate, 2),
                "monthly_goal": float(account.monthly_goal_amount),
                "biweekly_goal": float(account.biweekly_goal_amount),
                "currency": account.currency,
                "platform": account.platform,
                "is_demo": account.is_demo
            })
        
        return summary

    def _get_recent_trades(self, workspace_id: uuid.UUID, db: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
        """Busca trades recentes com todos os campos."""
        result = db.execute(
            select(Trade)
            .where(Trade.workspace_id == workspace_id)
            .order_by(desc(Trade.open_time))
            .limit(limit)
        )
        trades = result.scalars().all()
        
        recent_trades = []
        for trade in trades:
            recent_trades.append({
                "id": str(trade.id),
                "date": trade.open_time.strftime("%Y-%m-%d") if trade.open_time else None,
                "pair": trade.pair or trade.symbol,
                "dir": trade.dir or trade.side.upper(),
                "lots": float(trade.lots or trade.volume),
                "result": "WIN" if trade.net_profit >= 0 else "LOSS",
                "pnl": float(trade.pnl or trade.net_profit),
                "open_price": float(trade.open_price),
                "close_price": float(trade.close_price) if trade.close_price else None,
                "stop_loss": float(trade.stop_loss) if trade.stop_loss else None,
                "take_profit": float(trade.take_profit) if trade.take_profit else None,
                "comment": trade.comment,
                "strategy_name": trade.strategy_name,
                "has_vm": trade.has_vm,
                "vm_lots": float(trade.vm_lots),
                "vm_result": trade.vm_result,
                "vm_pnl": float(trade.vm_net_profit),
                "total_pnl": float(trade.net_profit + trade.vm_net_profit),
                "screenshot_url": trade.screenshot_url,
                "screenshot_caption": trade.screenshot_caption
            })
        
        return recent_trades

    def _calculate_metrics(self, workspace_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
        """Calcula métricas detalhadas do workspace."""
        
        # Métricas básicas
        trades_result = db.execute(
            select(
                func.count(Trade.id).label('total_trades'),
                func.sum(Trade.net_profit).label('total_pnl'),
                func.sum(func.case((Trade.net_profit >= 0, 1), else_=0)).label('wins'),
                func.sum(func.case((Trade.net_profit < 0, 1), else_=0)).label('losses'),
                func.max(Trade.net_profit).label('best_trade'),
                func.min(Trade.net_profit).label('worst_trade')
            ).where(Trade.workspace_id == workspace_id)
        )
        metrics = trades_result.first()
        
        total_trades = metrics.total_trades or 0
        total_pnl = float(metrics.total_pnl or 0)
        wins = metrics.wins or 0
        losses = metrics.losses or 0
        best_trade = float(metrics.best_trade or 0)
        worst_trade = float(metrics.worst_trade or 0)
        
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        profit_factor = (total_pnl + abs(worst_trade)) / abs(worst_trade) if worst_trade != 0 else 0
        
        # P&L por par
        pair_result = db.execute(
            select(
                Trade.pair,
                func.sum(Trade.net_profit).label('pnl'),
                func.count(Trade.id).label('count'),
                func.sum(func.case((Trade.net_profit >= 0, 1), else_=0)).label('wins')
            )
            .where(Trade.workspace_id == workspace_id)
            .group_by(Trade.pair)
            .order_by(desc('pnl'))
        )
        by_pair = []
        for row in pair_result:
            by_pair.append({
                "pair": row.pair,
                "pnl": float(row.pnl or 0),
                "count": row.count,
                "win_rate": (row.wins / row.count * 100) if row.count > 0 else 0
            })
        
        # P&L por dia da semana
        dow_result = db.execute(
            select(
                func.extract('dow', Trade.open_time).label('dow'),
                func.sum(Trade.net_profit).label('pnl'),
                func.count(Trade.id).label('count')
            )
            .where(Trade.workspace_id == workspace_id)
            .group_by(func.extract('dow', Trade.open_time))
            .order_by('dow')
        )
        by_weekday = []
        weekday_names = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        for row in dow_result:
            dow = int(row.dow)
            by_weekday.append({
                "day": weekday_names[dow],
                "pnl": float(row.pnl or 0),
                "count": row.count
            })
        
        # Top trades
        top_trades_result = db.execute(
            select(Trade)
            .where(Trade.workspace_id == workspace_id)
            .order_by(desc(Trade.net_profit))
            .limit(5)
        )
        top_trades = []
        for trade in top_trades_result.scalars():
            top_trades.append({
                "id": str(trade.id),
                "pair": trade.pair or trade.symbol,
                "dir": trade.dir or trade.side.upper(),
                "pnl": float(trade.net_profit),
                "date": trade.open_time.strftime("%Y-%m-%d") if trade.open_time else None
            })
        
        # Worst trades
        worst_trades_result = db.execute(
            select(Trade)
            .where(Trade.workspace_id == workspace_id)
            .order_by(Trade.net_profit)
            .limit(5)
        )
        worst_trades = []
        for trade in worst_trades_result.scalars():
            worst_trades.append({
                "id": str(trade.id),
                "pair": trade.pair or trade.symbol,
                "dir": trade.dir or trade.side.upper(),
                "pnl": float(trade.net_profit),
                "date": trade.open_time.strftime("%Y-%m-%d") if trade.open_time else None
            })
        
        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "by_pair": by_pair,
            "by_weekday": by_weekday,
            "top_trades": top_trades,
            "worst_trades": worst_trades
        }

    def _get_daily_notes(self, workspace_id: uuid.UUID, db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
        """Busca notas diárias dos últimos N dias."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = db.execute(
            select(DailyNote)
            .where(
                and_(
                    DailyNote.workspace_id == workspace_id,
                    DailyNote.date >= cutoff_date
                )
            )
            .order_by(desc(DailyNote.date))
        )
        notes = result.scalars().all()
        
        daily_notes = []
        for note in notes:
            daily_notes.append({
                "id": str(note.id),
                "date": note.date.strftime("%Y-%m-%d"),
                "content": note.content,
                "sentiment": self._analyze_sentiment(note.content),
                "created_at": note.created_at.isoformat() if note.created_at else None
            })
        
        return daily_notes

    def _get_goals_progress(self, workspace_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
        """Calcula progresso das metas mensais e quinzenais."""
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Meta mensal
        monthly_goal_result = db.execute(
            select(func.sum(TradingAccount.monthly_goal_amount))
            .where(TradingAccount.workspace_id == workspace_id)
        )
        monthly_goal = monthly_goal_result.scalar() or Decimal("0")
        
        # P&L do mês atual
        monthly_pnl_result = db.execute(
            select(func.sum(Trade.net_profit))
            .where(
                and_(
                    Trade.workspace_id == workspace_id,
                    Trade.open_time >= current_month_start
                )
            )
        )
        monthly_pnl = monthly_pnl_result.scalar() or Decimal("0")
        
        # Meta quinzenal (calculada como metade da mensal)
        biweekly_goal = monthly_goal / Decimal("2")
        
        # P&L dos últimos 15 dias
        biweekly_start = now - timedelta(days=15)
        biweekly_pnl_result = db.execute(
            select(func.sum(Trade.net_profit))
            .where(
                and_(
                    Trade.workspace_id == workspace_id,
                    Trade.open_time >= biweekly_start
                )
            )
        )
        biweekly_pnl = biweekly_pnl_result.scalar() or Decimal("0")
        
        return {
            "monthly": {
                "goal": float(monthly_goal),
                "current": float(monthly_pnl),
                "percentage": (float(monthly_pnl / monthly_goal) * 100) if monthly_goal > 0 else 0,
                "remaining": float(monthly_goal - monthly_pnl),
                "achieved": monthly_pnl >= monthly_goal
            },
            "biweekly": {
                "goal": float(biweekly_goal),
                "current": float(biweekly_pnl),
                "percentage": (float(biweekly_pnl / biweekly_goal) * 100) if biweekly_goal > 0 else 0,
                "remaining": float(biweekly_goal - biweekly_pnl),
                "achieved": biweekly_pnl >= biweekly_goal
            }
        }

    def _calculate_streaks(self, workspace_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
        """Calcula sequências atuais de wins/losses."""
        result = db.execute(
            select(Trade)
            .where(Trade.workspace_id == workspace_id)
            .order_by(desc(Trade.open_time))
        )
        trades = result.scalars().all()
        
        current_win_streak = 0
        current_loss_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        
        for trade in trades:
            if trade.net_profit >= 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        return {
            "current_win_streak": current_win_streak,
            "current_loss_streak": current_loss_streak,
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak
        }

    def _analyze_sentiment(self, text: str) -> str:
        """Análise simples de sentimento da nota."""
        positive_words = ['bom', 'ótimo', 'excelente', 'feliz', 'confiante', 'ganhei', 'vitória', 'sucesso']
        negative_words = ['ruim', 'péssimo', 'triste', 'frustrado', 'perdi', 'prejuízo', 'erro', 'falha']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positivo"
        elif negative_count > positive_count:
            return "negativo"
        else:
            return "neutro"


# Instância global do serviço
ai_service = AIService()
