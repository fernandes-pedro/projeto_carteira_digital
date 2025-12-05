from typing import Literal, Optional
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
    
class MovimentoInput(BaseModel):
    codigo_moeda: str 
    valor: Decimal
    chave_privada: Optional[str] = None
    
class MovimentoHistorico(BaseModel):
    id_movimento: int
    endereco_carteira: str
    codigo_moeda: str
    tipo: Literal["DEPOSITO", "SAQUE"]
    valor: Decimal
    taxa_valor: Decimal
    data_hora: datetime

class ConversaoInput(BaseModel):
    """Modelo para a requisição de conversão."""
    codigo_origem: str
    codigo_destino: str
    valor_origem: Decimal 
    chave_privada: str
    
class TransferenciaInput(BaseModel):
    """Modelo para a requisição de transferência."""
    endereco_destino: str
    codigo_moeda: str
    valor: Decimal
    chave_privada_origem: str