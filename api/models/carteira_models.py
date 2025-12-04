from typing import Literal
from datetime import  datetime
from pydantic import BaseModel
from decimal import Decimal


class CarteiraCriada(BaseModel):
    endereco_carteira: str
    chave_privada: str
    data_criacao: datetime
    status: Literal["ATIVA","BLOQUEADA"]
    
class CarteiraBase(BaseModel):
    endereco_carteira: str
    data_criacao: datetime
    status_ativo: str
class SaldoItem(BaseModel):
    codigo_moeda: str
    saldo: Decimal

class CarteiraSaldoResponse(BaseModel):
    endereco_carteira: str
    saldos: list[SaldoItem]