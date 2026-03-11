"""
Script para popular planos padrão no banco de dados.
"""
import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.profile import Plan, PlanType


async def seed_plans():
    """Popula planos padrão."""
    async with AsyncSessionLocal() as db:
        # Verificar se planos já existem
        from sqlalchemy import select
        result = await db.execute(select(Plan))
        if result.scalars().first():
            print("Plans already exist, skipping seed.")
            return

        # Criar planos padrão
        plans = [
            Plan(
                name="Básico",
                type=PlanType.basic,
                price=Decimal("47.00"),
                max_accounts=1,
                features={
                    "max_accounts": 1,
                    "dashboard_access": True,
                    "basic_reports": True,
                    "ai_chat": False,
                    "weekly_reports": True,
                    "monthly_reports": True,
                    "export_pdf": True,
                    "screenshot_storage": "100MB",
                    "data_retention": "6 months"
                }
            ),
            Plan(
                name="Intermediário", 
                type=PlanType.intermediate,
                price=Decimal("67.00"),
                max_accounts=3,
                features={
                    "max_accounts": 3,
                    "dashboard_access": True,
                    "advanced_reports": True,
                    "ai_chat": True,
                    "ai_messages_limit": 100,
                    "weekly_reports": True,
                    "monthly_reports": True,
                    "export_pdf": True,
                    "export_excel": True,
                    "screenshot_storage": "500MB",
                    "data_retention": "12 months",
                    "risk_metrics": True,
                    "performance_comparison": True
                }
            ),
            Plan(
                name="Avançado",
                type=PlanType.advanced,
                price=Decimal("97.00"),
                max_accounts=10,
                features={
                    "max_accounts": 10,
                    "dashboard_access": True,
                    "advanced_reports": True,
                    "ai_chat": True,
                    "ai_messages_limit": -1,  # unlimited
                    "ai_advanced_models": True,
                    "weekly_reports": True,
                    "monthly_reports": True,
                    "export_pdf": True,
                    "export_excel": True,
                    "export_csv": True,
                    "screenshot_storage": "2GB",
                    "data_retention": "lifetime",
                    "risk_metrics": True,
                    "performance_comparison": True,
                    "api_access": True,
                    "custom_alerts": True,
                    "priority_support": True,
                    "beta_features": True
                }
            )
        ]

        for plan in plans:
            db.add(plan)

        await db.commit()
        print(f"Created {len(plans)} default plans.")


if __name__ == "__main__":
    asyncio.run(seed_plans())
