from typing import List
from datetime import datetime
from decimal import Decimal

from api.persistence.repositories.carteira_repository import CarteiraRepository
from api.models.carteira_models import Carteira, CarteiraCriada, SaldoItem
from api.services.key_service import gerar_chave

TAXA_SAQUE_PERCENTUAL = Decimal(os.getenv("TAXA_SAQUE_PERCENTUAL", "0.01"))
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

    def buscar_saldos(self, endereco_carteira: str) -> List[Saldo]:
        """
        Retorna todos os saldos da carteira.
        """
        rows = self.carteira_repo.buscar_saldos(endereco_carteira)
        return [
            Saldo(
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