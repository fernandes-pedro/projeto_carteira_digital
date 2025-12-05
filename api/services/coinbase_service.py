import httpx
from decimal import Decimal

BASE_URL = "https://api.coinbase.com/v2/prices"

async def get_cotacao(moeda_origem: str, moeda_destino: str) -> Decimal:
    """
    Busca a cotação spot na API da Coinbase.
    Retorna a cotação (unidades de DESTINO por 1 unidade de ORIGEM).
    """
    pair = f"{moeda_origem}-{moeda_destino}"
    url = f"{BASE_URL}/{pair}/spot"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        cotacao = Decimal(data["data"]["amount"])
        return cotacao
