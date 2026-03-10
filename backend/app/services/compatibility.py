"""
Serviço de compatibilidade entre frontend e backend.
Normaliza dados e garante compatibilidade total.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from app.models.trade import Trade
from app.models.account import TradingAccount


class CompatibilityService:
    """Serviço para normalizar dados entre frontend e backend."""

    @staticmethod
    def normalize_trade_from_frontend(trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados do frontend para formato do backend.
        Frontend usa: pnl, pair, dir, lots, result, date
        Backend usa: net_profit, symbol, side, volume, status, open_time
        """
        normalized = trade_data.copy()
        
        # Mapear campos do frontend para backend
        if "pnl" in normalized:
            normalized["net_profit"] = Decimal(str(normalized["pnl"]))
        
        if "pair" in normalized:
            normalized["symbol"] = normalized["pair"]
        
        if "dir" in normalized:
            # Converter BUY/SELL para buy/sell
            dir_value = normalized["dir"].upper()
            normalized["side"] = dir_value.lower()
            normalized["dir"] = dir_value  # Manter para compatibilidade
        
        if "lots" in normalized:
            normalized["volume"] = Decimal(str(normalized["lots"]))
            normalized["lots"] = Decimal(str(normalized["lots"]))  # Manter para compatibilidade
        
        if "result" in normalized:
            result_value = normalized["result"].upper()
            normalized["status"] = "closed"  # Sempre closed por enquanto
            normalized["result"] = result_value  # Manter para compatibilidade
        
        # Converter data string para datetime se necessário
        if "date" in normalized and normalized["date"]:
            try:
                date_obj = datetime.fromisoformat(normalized["date"].replace("Z", "+00:00"))
                normalized["open_time"] = date_obj
                
                # Extrair ano e mês para compatibilidade
                normalized["year"] = date_obj.year
                normalized["month"] = date_obj.month
            except (ValueError, AttributeError):
                pass  # Manter valores originais se falhar
        
        # Garantir campos VM
        if "hasVM" in normalized:
            normalized["has_vm"] = normalized["hasVM"]
        
        if "vmLots" in normalized:
            normalized["vm_lots"] = Decimal(str(normalized["vmLots"]))
        
        if "vmResult" in normalized:
            normalized["vm_result"] = normalized["vmResult"].upper()
        
        if "vmPnl" in normalized:
            normalized["vm_net_profit"] = Decimal(str(normalized["vmPnl"]))
        
        return normalized
    
    @staticmethod
    def normalize_trade_to_backend(trade: Trade) -> Dict[str, Any]:
        """
        Converte model do backend para formato compatível com frontend.
        """
        # Garantir campos de compatibilidade
        if not hasattr(trade, 'pnl') or trade.pnl is None:
            trade.pnl = trade.net_profit
        
        if not hasattr(trade, 'pair') or not trade.pair:
            trade.pair = trade.symbol
        
        if not hasattr(trade, 'dir') or not trade.dir:
            trade.dir = trade.side.upper()
        
        if not hasattr(trade, 'lots') or trade.lots is None:
            trade.lots = trade.volume
        
        if not hasattr(trade, 'result') or not trade.result:
            trade.result = "WIN" if trade.net_profit >= 0 else "LOSS"
        
        if not hasattr(trade, 'date') or not trade.date:
            if trade.open_time:
                trade.date = trade.open_time.strftime("%Y-%m-%d")
                trade.year = trade.open_time.year
                trade.month = trade.open_time.month
        
        return {
            "id": str(trade.id),
            "workspace_id": str(trade.workspace_id),
            "account_id": str(trade.account_id),
            "symbol": trade.symbol,
            "pair": trade.pair,
            "side": trade.side,
            "dir": trade.dir,
            "volume": trade.volume,
            "lots": trade.lots,
            "open_time": trade.open_time,
            "close_time": trade.close_time,
            "open_price": trade.open_price,
            "close_price": trade.close_price,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "commission": trade.commission,
            "swap": trade.swap,
            "taxes": trade.taxes,
            "gross_profit": trade.gross_profit,
            "net_profit": trade.net_profit,
            "pnl": trade.pnl,
            "profit_currency": trade.profit_currency,
            "status": trade.status,
            "result": trade.result,
            "magic_number": trade.magic_number,
            "strategy_name": trade.strategy_name,
            "comment": trade.comment,
            "screenshot_url": trade.screenshot_url,
            "screenshot_caption": trade.screenshot_caption,
            # VM fields
            "has_vm": trade.has_vm,
            "vm_lots": trade.vm_lots,
            "vm_result": trade.vm_result,
            "vm_net_profit": trade.vm_net_profit,
            # Date fields
            "date": trade.date,
            "year": trade.year,
            "month": trade.month,
            "created_at": trade.created_at,
            "updated_at": trade.updated_at,
            "tags": [
                {
                    "id": str(tag.id),
                    "name": tag.name,
                    "color": tag.color
                }
                for tag in trade.tag_links
            ] if hasattr(trade, 'tag_links') else []
        }
    
    @staticmethod
    def normalize_account_to_backend(account: TradingAccount) -> Dict[str, Any]:
        """
        Converte model do backend para formato compatível com frontend.
        """
        return {
            "id": str(account.id),
            "workspace_id": str(account.workspace_id),
            "name": account.name,
            "balance": float(account.current_balance),
            "initial_balance": float(account.initial_balance),
            "currency": account.currency,
            "platform": account.platform,
            "is_demo": account.is_demo,
            "leverage": account.leverage,
            "monthly_goal": float(account.monthly_goal_amount),
            "monthly_goal_amount": float(account.monthly_goal_amount),
            "biweekly_goal_amount": float(account.biweekly_goal_amount),
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            "closed_at": account.closed_at,
            # Campos adicionais que o frontend pode esperar
            "notes": "",
            "trades": [],  # Populado se necessário
            "withdrawals": {}  # Populado se necessário
        }
    
    @staticmethod
    def create_gpfx_state_from_backend(accounts: list[TradingAccount]) -> Dict[str, Any]:
        """
        Cria estado GPFX compatível com frontend a partir dos dados do backend.
        """
        from datetime import datetime
        
        # Converter contas para formato frontend
        frontend_accounts = []
        for account in accounts:
            account_data = CompatibilityService.normalize_account_to_backend(account)
            frontend_accounts.append(account_data)
        
        # Estado padrão GPFX
        now = datetime.now()
        return {
            "accounts": frontend_accounts,
            "activeAccount": 0,
            "activeYear": now.getFullYear() if hasattr(now, 'getFullYear') else now.year,
            "activeMonth": now.getMonth() if hasattr(now, 'getMonth') else now.month - 1
        }
    
    @staticmethod
    def validate_trade_data(trade_data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Valida dados de trade do frontend.
        Retorna (is_valid, error_messages)
        """
        errors = []
        
        # Campos obrigatórios
        required_fields = ["pair", "dir", "result", "pnl"]
        for field in required_fields:
            if field not in trade_data or trade_data[field] is None:
                errors.append(f"Campo '{field}' é obrigatório")
        
        # Validações específicas
        if "pair" in trade_data:
            if not trade_data["pair"] or len(trade_data["pair"]) < 1:
                errors.append("Pair/Ativo é inválido")
        
        if "dir" in trade_data:
            if trade_data["dir"] not in ["BUY", "SELL"]:
                errors.append("Direção deve ser BUY ou SELL")
        
        if "result" in trade_data:
            if trade_data["result"] not in ["WIN", "LOSS"]:
                errors.append("Resultado deve ser WIN ou LOSS")
        
        if "pnl" in trade_data:
            try:
                pnl = Decimal(str(trade_data["pnl"]))
                if pnl == Decimal("0"):
                    errors.append("P&L não pode ser zero")
            except (ValueError, TypeError):
                errors.append("P&L deve ser um número válido")
        
        if "lots" in trade_data and trade_data["lots"] is not None:
            try:
                lots = Decimal(str(trade_data["lots"]))
                if lots <= 0:
                    errors.append("Lots deve ser maior que zero")
            except (ValueError, TypeError):
                errors.append("Lots deve ser um número válido")
        
        # Validação de campos VM
        if trade_data.get("has_vm", False):
            if "vmLots" in trade_data and trade_data["vmLots"] is not None:
                try:
                    vm_lots = Decimal(str(trade_data["vmLots"]))
                    if vm_lots <= 0:
                        errors.append("VM Lots deve ser maior que zero")
                except (ValueError, TypeError):
                    errors.append("VM Lots deve ser um número válido")
            
            if "vmResult" in trade_data:
                if trade_data["vmResult"] not in ["WIN", "LOSS"]:
                    errors.append("VM Result deve ser WIN ou LOSS")
        
        return len(errors) == 0, errors


# Instância global do serviço
compatibility_service = CompatibilityService()
