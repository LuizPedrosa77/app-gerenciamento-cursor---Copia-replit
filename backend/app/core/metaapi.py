import requests
import time
from typing import Optional

METAAPI_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJhYjkwOGQ4Mzk2ZmM2NTRlY2ZhMjUxZTFiYzE3MDY0MCIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiYWI5MDhkODM5NmZjNjU0ZWNmYTI1MWUxYmMxNzA2NDAiLCJpYXQiOjE3NzM0MjA5NDUsImV4cCI6MTc3NjAxMjk0NX0.oHHM77Piu67Sy6NjZNBlBxYTfSgsvWJ0IbsKS3a8pBcOJjZWus6gdY_caJ22ZA-Nynk9VLTfMN0iILSxS1Z_Tp-57p5b-wSr1xTKNeSPXZP5hbEARFpa4bgP4ZS4Y6lvucsGIbrGCLP5wGkbyJ2L5URMTVEDwo205Hri1298GGfr6PKrJ-UIqFNeM-CpClDZStVP4-we-Ijbh4CDaQkpCVZg7C1gelJu7opBkwsrnMq4QEsjf4-5J3F8IJHCptv34uAegCbwYVtRhuDfkHqoHZi4pt3f8pw902bgCQT8ZiXafI2NjMakA6xTCtjPghWRBRaNogcyFirmj6g7U28fQJYozeJhmiXIyq0BJe576Llt5TSE4QB1AbHLNkDbAjGET6oDwkocv75SZiu0Ixm7biF0UrPu0UEzDNQuSJ0WOKL_PSHESmXvc0QhHXwkXQTuoYIHj9wPDbxCrvFVXOOZzIroxfvgYnyq-nIm4t7alCmgS6TjGcqdH8HisO2J0DdhwOiHuqiNcR5RA_oDUFU2axnRJoe6D58aX080XRaqktQUMl0Kl2xpfzZf1Ox3y-04a7x3s2FHJva7K8UMYRiYDDhin80nJQ28JmezPw4E85csm8EFFCpbdJevh4qE5WOZ8JCvUbmoE6iphADYbRB-7lsQO8phbCc3YZkFu-ubE8Q"
METAAPI_BASE = "https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai"
METAAPI_ACCOUNT_BASE = "https://mt-client-api-v1.new-york.agiliumtrade.ai"

def get_headers():
    return {
        "auth-token": METAAPI_TOKEN,
        "Content-Type": "application/json"
    }

def create_mt_account(login: str, password: str, server: str, platform: str = "mt5") -> dict:
    """Cria conta MT4/MT5 no MetaApi"""
    url = f"{METAAPI_BASE}/users/current/accounts"
    payload = {
        "login": login,
        "password": password,
        "server": server,
        "platform": platform,
        "name": f"GPFX-{login}",
        "magic": 0,
        "application": "MetaApi",
        "type": "cloud"
    }
    response = requests.post(url, json=payload, headers=get_headers())
    response.raise_for_status()
    return response.json()

def get_mt_account(account_id: str) -> dict:
    """Busca conta MT no MetaApi"""
    url = f"{METAAPI_BASE}/users/current/accounts/{account_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()

def wait_account_deployed(account_id: str, timeout: int = 120) -> bool:
    """Aguarda conta ser deployada (max 2 minutos)"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            account = get_mt_account(account_id)
            state = account.get("state", "")
            if state == "DEPLOYED":
                return True
            if state in ["DEPLOY_FAILED", "ERROR"]:
                return False
        except:
            pass
        time.sleep(5)
    return False

def get_trade_history(account_id: str, start_time: str = "2020-01-01T00:00:00.000Z") -> list:
    """Puxa histórico de trades da conta"""
    url = f"{METAAPI_ACCOUNT_BASE}/users/current/accounts/{account_id}/history-deals/time/{start_time}/9999-01-01T00:00:00.000Z"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()

def delete_mt_account(account_id: str) -> bool:
    """Remove conta do MetaApi"""
    url = f"{METAAPI_BASE}/users/current/accounts/{account_id}"
    response = requests.delete(url, headers=get_headers())
    return response.status_code in [200, 204]

def parse_deal_to_trade(deal: dict, account_id: str) -> Optional[dict]:
    """Converte deal do MetaApi para formato do sistema"""
    entry_type = deal.get("entryType", "")
    if entry_type not in ["DEAL_ENTRY_OUT", "DEAL_ENTRY_IN_OUT"]:
        return None
    deal_type = deal.get("type", "")
    if deal_type not in ["DEAL_TYPE_BUY", "DEAL_TYPE_SELL"]:
        return None
    time_str = deal.get("time", "")
    if not time_str:
        return None
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        trade_date = dt.date()
        year = dt.year
        month = dt.month
    except:
        return None
    pnl = float(deal.get("profit", 0))
    direction = "BUY" if deal_type == "DEAL_TYPE_BUY" else "SELL"
    result = "WIN" if pnl > 0 else "LOSS"
    return {
        "account_id": account_id,
        "date": trade_date,
        "year": year,
        "month": month,
        "pair": deal.get("symbol", ""),
        "direction": direction,
        "lots": float(deal.get("volume", 0)),
        "pnl": pnl,
        "result": result,
        "notes": f"Importado via MetaApi | Deal ID: {deal.get('id', '')}"
    }
