from fastapi import APIRouter, HTTPException, Depends, status
from models.carteira_models import CarteiraCriada, MovimentoInput, MovimentoHistorico, ConversaoInput
from services.carteira_service import CarteiraService
from typing import List, Dict, Any

from models.carteira_models import TransferenciaInput
from api.services.carteira_service import CarteiraService
from api.persistence.repositories.carteira_repository import CarteiraRepository
from api.models.carteira_models import CarteiraCriada


router = APIRouter(prefix="/carteiras", tags=["carteiras"])


def get_carteira_service() -> CarteiraService:
    repo = CarteiraRepository()
    return CarteiraService(repo)


@router.post("/carteiras", response_model=CarteiraCriada, status_code=201)
def criar_carteira(
    service: CarteiraService = Depends(get_carteira_service),
)->CarteiraCriada:
    """
    Cria uma nova carteira. O body é opcional .
    Retorna endereço e chave privada (apenas nesta resposta).
    """
    try:
        return service.criar_carteira()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Carteira])
def listar_carteiras(service: CarteiraService = Depends(get_carteira_service)):
    return service.listar()


@router.get("/{endereco_carteira}", response_model=Carteira)
def buscar_carteira(
    endereco_carteira: str,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        return service.buscar_por_endereco(endereco_carteira)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{endereco_carteira}", response_model=Carteira)
def bloquear_carteira(
    endereco_carteira: str,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        return service.bloquear(endereco_carteira)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{endereco_carteira}/saldos", response_model=List[Saldo])
def buscar_saldos_carteira(
    endereco_carteira: str,
    service: CarteiraService = Depends(get_carteira_service),
):
    """
    Retorna todos os saldos de uma carteira específica.
    """
    try:
        return service.buscar_saldos(endereco_carteira)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{endereco_carteira}/depositos", 
             response_model=MovimentoHistorico, 
             status_code=status.HTTP_201_CREATED)
def realizar_deposito(
    endereco_carteira: str,
    movimento: MovimentoInput,
    service: CarteiraService = Depends(get_carteira_service),
) -> MovimentoHistorico:
    """
    Registra um depósito na carteira (entrada de fundos sem taxa).
    """
    if movimento.chave_privada is not None:
         pass 
         
    try:
        return service.depositar(
            endereco_carteira=endereco_carteira,
            codigo_moeda=movimento.codigo_moeda,
            valor=movimento.valor
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/{endereco_carteira}/saques", 
            response_model=MovimentoHistorico, 
            status_code=status.HTTP_201_CREATED)
def realizar_saque(
    endereco_carteira: str,
    movimento: MovimentoInput,
    service: CarteiraService = Depends(get_carteira_service),
) -> MovimentoHistorico:
    """
    Registra um saque na carteira (saída de fundos com taxa).
    Exige chave privada e validação de saldo.
    """
    if not movimento.chave_privada:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave privada é obrigatória para saques.")
        
    try:
        return service.sacar(
            endereco_carteira=endereco_carteira,
            codigo_moeda=movimento.codigo_moeda,
            valor_saque=movimento.valor,
            chave_privada=movimento.chave_privada
        )
    except ValueError as e:
        if "Chave privada inválida" in str(e):
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        else:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/{endereco_carteira}/conversoes",
             response_model=dict, 
             status_code=status.HTTP_201_CREATED)
async def realizar_conversao(
    endereco_carteira: str,
    conversao: ConversaoInput,
    service: CarteiraService = Depends(get_carteira_service),
):
    """
    Converte saldo de uma moeda para outra, aplicando taxa e usando cotação externa (Coinbase).
    Exige chave privada e validação de saldo.
    """
    if not conversao.chave_privada:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave privada é obrigatória para conversão.")
        
    try:
        return await service.converter_moedas(
            endereco_carteira=endereco_carteira,
            conversao_data=conversao
        )
    except ValueError as e:
        if "Chave privada inválida" in str(e):
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        elif "Saldo insuficiente" in str(e):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        else:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro no processamento da conversão: {e}")
    
@router.post("/{endereco_origem}/transferencias", 
            response_model=Dict[str, Any], 
            status_code=status.HTTP_201_CREATED)
def realizar_transferencia(
    endereco_origem: str,
    transferencia: TransferenciaInput,
    service: CarteiraService = Depends(get_carteira_service),
) -> Dict[str, Any]:
    """
    Transfere valor da carteira de origem para a carteira de destino. 
    A origem paga taxa, o destino recebe o valor líquido.
    """
    if not transferencia.chave_privada_origem:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave privada de origem é obrigatória para transferências.")
        
    try:
        return service.transferir_fundos(
            endereco_origem=endereco_origem,
            transferencia_data=transferencia
        )
    except ValueError as e:
        if "Chave privada de origem inválida" in str(e):
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        elif "Saldo insuficiente" in str(e):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        else:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro no processamento da transferência: {e}")