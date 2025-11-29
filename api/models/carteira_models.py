from typing import Literal
from datetime import  datetime
from pydantic import BaseModel
from decimal import Decimal


class Carteira(BaseModel):
    endereco_carteira: str
    data_criacao: datetime
    status: Literal["ATIVA","BLOQUEADA"]

class CarteiraCriada(Carteira):
    chave_privada: str

class Saldo(BaseModel):
    id_moeda: int
    codigo_moeda: str
    nome_moeda: str
    saldo: Decimal
    data_atualizacao: datetime