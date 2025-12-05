from typing import List
from datetime import datetime
from decimal import Decimal
import os

from api.services.coinbase_service import get_cotacao
from api.persistence.repositories.carteira_repository import CarteiraRepository
from api.models.carteira_models import Carteira, CarteiraCriada, SaldoItem, ConversaoInput, MovimentoHistorico, TransferenciaInput
from api.services.key_service import gerar_chave

TAXA_SAQUE_PERCENTUAL = Decimal(os.getenv("TAXA_SAQUE_PERCENTUAL", "0.01"))
TAXA_CONVERSAO_PERCENTUAL = Decimal(os.getenv("TAXA_CONVERSAO_PERCENTUAL", "0.02"))
TAXA_TRANSFERENCIA_PERCENTUAL = Decimal(os.getenv("TAXA_TRANSFERENCIA_PERCENTUAL", "0.01"))
class CarteiraService:
    
    MOEDAS_OBRIGATORIAS = ['BTC', 'ETH', 'SOL', 'USD', 'BRL']
    
    def __init__(self, carteira_repo: CarteiraRepository):
        self.carteira_repo = carteira_repo

    def criar_carteira(self) -> CarteiraCriada:
        
        endereco, chave_privada_real, hash_chave_privada = gerar_chave()
        
        data_criacao = datetime.now()
        status_ativo = "ATIVA"
        try:
            self.carteira_repo.criar_nova_carteira(
                endereco=endereco,
                hash_chave_privada=hash_chave_privada,
                data_criacao=data_criacao,
                status=status_ativo
            )
            
            saldos_iniciais = [
                SaldoItem(codigo_moeda=moeda, saldo=Decimal("0.00"))
                for moeda in self.MOEDAS_OBRIGATORIAS
            ]
            
            self.carteira_repo.inicializar_saldos(endereco, saldos_iniciais)
            
        except Exception as e:
            print(f"Erro ao persistir a carteira: {e}")
            raise Exception("Erro ao criar a carteira no banco de dados.")

        return CarteiraCriada(
            endereco_carteira=endereco,
            data_criacao=data_criacao,
            status=status_ativo,
            chave_privada=chave_privada_real,
        )

    def buscar_por_endereco(self, endereco_carteira: str) -> Carteira:
        row = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not row:
            raise ValueError("Carteira não encontrada")

        return Carteira(
            endereco_carteira=row["endereco_carteira"],
            data_criacao=row["data_criacao"],
            status=row["status"],
        )

    def listar(self) -> List[Carteira]:
        rows = self.carteira_repo.listar()
        return [
            Carteira(
                endereco_carteira=r["endereco_carteira"],
                data_criacao=r["data_criacao"],
                status=r["status"],
            )
            for r in rows
        ]

    def bloquear(self, endereco_carteira: str) -> Carteira:
        row = self.carteira_repo.atualizar_status(endereco_carteira, "BLOQUEADA")
        if not row:
            raise ValueError("Carteira não encontrada")

        return Carteira(
            endereco_carteira=row["endereco_carteira"],
            data_criacao=row["data_criacao"],
            status=row["status"],
        )

    def buscar_saldos(self, endereco_carteira: str) -> List[SaldoItem]:
        """
        Retorna todos os saldos da carteira.
        """
        rows = self.carteira_repo.buscar_saldos(endereco_carteira)
        return [
            SaldoItem(
                id_moeda=r["id_moeda"],
                codigo_moeda=r["codigo_moeda"],
                nome_moeda=r["nome_moeda"],
                saldo=r["saldo"],
                data_atualizacao=r["data_atualizacao"],
            )
            for r in rows
        ]
        
    def depositar(self, endereco_carteira: str, codigo_moeda: str, valor: Decimal) -> MovimentoHistorico:
        if valor <= 0:
            raise ValueError("O valor do depósito deve ser positivo.")

        try:
            movimento = self.carteira_repo.registrar_deposito(endereco_carteira, codigo_moeda, valor)
            return movimento
        except Exception as e:
            raise Exception(f"Falha ao processar depósito: {e}")
        
    def sacar(self, endereco_carteira: str, codigo_moeda: str, valor_saque: Decimal, chave_privada: str) -> MovimentoHistorico:
        """
        Registra um saque, debita valor + taxa e valida a chave privada.
        """
        if valor_saque <= 0:
            raise ValueError("O valor do saque deve ser positivo.")

        is_valid = self.carteira_repo.validar_chave_privada(endereco_carteira, chave_privada)
        if not is_valid:
            raise ValueError("Chave privada inválida ou carteira não encontrada.")

        taxa = valor_saque * TAXA_SAQUE_PERCENTUAL
        valor_total_debito = valor_saque + taxa
        
        saldo_atual = self.carteira_repo.buscar_saldo_por_moeda(endereco_carteira, codigo_moeda)
        if saldo_atual is None or saldo_atual < valor_total_debito:
            raise ValueError("Saldo insuficiente para cobrir o valor e a taxa.")

        try:
            movimento = self.carteira_repo.registrar_saque(
                endereco_carteira=endereco_carteira,
                codigo_moeda=codigo_moeda,
                valor=valor_saque,
                taxa=taxa,
                valor_total_debito=valor_total_debito
            )
            return movimento
        except Exception as e:
            raise Exception(f"Falha ao processar saque: {e}")
        
    async def converter_moedas(self, endereco_carteira: str, conversao_data: ConversaoInput):
    
        if not self.carteira_repo.validar_chave_privada(endereco_carteira, conversao_data.chave_privada):
            raise ValueError("Chave privada inválida ou carteira não encontrada.")

        cotacao = await get_cotacao(conversao_data.codigo_origem, conversao_data.codigo_destino)
        
        valor_origem = conversao_data.valor_origem
        taxa_percentual = TAXA_CONVERSAO_PERCENTUAL
        
        valor_bruto_destino = valor_origem * cotacao
        
        taxa_valor = valor_bruto_destino * taxa_percentual
        
        valor_destino_liquido = valor_bruto_destino - taxa_valor
        
        saldo_origem = self.carteira_repo.buscar_saldo_por_moeda(endereco_carteira, conversao_data.codigo_origem)
        if saldo_origem is None or saldo_origem < valor_origem:
            raise ValueError("Saldo insuficiente na moeda de origem para conversão.")

        movimento = self.carteira_repo.registrar_conversao(
            endereco_carteira=endereco_carteira,
            codigo_origem=conversao_data.codigo_origem,
            codigo_destino=conversao_data.codigo_destino,
            valor_origem=valor_origem,
            valor_destino=valor_destino_liquido,
            taxa_percentual=taxa_percentual,
            taxa_valor=taxa_valor,
            cotacao_utilizada=cotacao
        )
        
        return movimento 
            
    def transferir_fundos(self, endereco_origem: str, transferencia_data: TransferenciaInput):
    
        if not self.carteira_repo.validar_chave_privada(endereco_origem, transferencia_data.chave_privada_origem):
            raise ValueError("Chave privada de origem inválida.")

        if not self.carteira_repo.buscar_por_endereco(transferencia_data.endereco_destino):
            raise ValueError("Carteira de destino não encontrada.")
        
        valor_liquido = transferencia_data.valor
        taxa_percentual = TAXA_TRANSFERENCIA_PERCENTUAL
        
        taxa_valor = valor_liquido * taxa_percentual
        
        valor_total_debito = valor_liquido + taxa_valor
        
        saldo_origem = self.carteira_repo.buscar_saldo_por_moeda(endereco_origem, transferencia_data.codigo_moeda)
        if saldo_origem is None or saldo_origem < valor_total_debito:
            raise ValueError("Saldo insuficiente na carteira de origem para cobrir o valor e a taxa.")

        movimento = self.carteira_repo.registrar_transferencia(
            endereco_origem=endereco_origem,
            endereco_destino=transferencia_data.endereco_destino,
            codigo_moeda=transferencia_data.codigo_moeda,
            valor_liquido=valor_liquido,
            valor_total_debito=valor_total_debito,
            taxa_valor=taxa_valor
        )
        
        return movimento 