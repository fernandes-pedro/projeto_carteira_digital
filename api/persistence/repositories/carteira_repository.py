import os
import secrets
import hashlib
from typing import Dict, Any, Optional, List

from api.models.carteira_models import SaldoItem
from sqlalchemy import text
from datetime import datetime
from api.persistence.db import get_connection
from decimal import Decimal

class CarteiraRepository:
    """
    Acesso a dados da carteira usando SQLAlchemy Core + SQL puro.
    """

    def criar_nova_carteira(self, endereco: str, hash_chave_privada: str, data_criacao: datetime, status: str) -> Dict[str, Any]:
        """
        Gera chave pública, chave privada, salva no banco (apenas hash da privada)
        e retorna os dados da carteira + chave privada em claro.
        """

        with get_connection() as conn:
            # 1) INSERT
            conn.execute(
                text("""
                    INSERT INTO carteira (endereco_carteira, hash_chave_privada, data_criacao, status_ativo)
                    VALUES (:endereco, :hash_privada, :data_criacao, :status)
                """),
                {
                    "endereco": endereco,
                    "hash_privada": hash_chave_privada,
                    "data_criacao": data_criacao,
                    "status": status,
                },
            )

            # 2) SELECT para retornar a carteira criada
            row = conn.execute(
                text("""
                    SELECT endereco_carteira, data_criacao, status_ativo
                    FROM carteira
                    WHERE endereco_carteira = :endereco
                """),
                {"endereco": endereco},
            ).mappings().first()

        return dict(row) if row else {}

    def buscar_por_endereco(self, endereco_carteira: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            row = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           data_criacao,
                           status,
                           hash_chave_privada
                      FROM carteira
                     WHERE endereco_carteira = :endereco
                """),
                {"endereco": endereco_carteira},
            ).mappings().first()

        return dict(row) if row else None

    def listar(self) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           data_criacao,
                           status,
                           hash_chave_privada
                      FROM carteira
                """)
            ).mappings().all()

        return [dict(r) for r in rows]

    def atualizar_status(self, endereco_carteira: str, status: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            conn.execute(
                text("""
                    UPDATE carteira
                       SET status = :status
                     WHERE endereco_carteira = :endereco
                """),
                {"status": status, "endereco": endereco_carteira},
            )

            row = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           data_criacao,
                           status,
                           hash_chave_privada
                      FROM carteira
                     WHERE endereco_carteira = :endereco
                """),
                {"endereco": endereco_carteira},
            ).mappings().first()

        return dict(row) if row else None

    def buscar_saldos(self, endereco_carteira: str) -> List[Dict[str, Any]]:
        """
        Retorna todos os saldos de uma carteira com informações das moedas.
        """
        with get_connection() as conn:
            rows = conn.execute(
                text("""
                    SELECT sc.id_moeda,
                           m.codigo AS codigo_moeda,
                           m.nome AS nome_moeda,
                           sc.saldo,
                           sc.data_atualizacao
                      FROM saldo_carteira sc
                      JOIN moeda m ON sc.id_moeda = m.id_moeda
                     WHERE sc.endereco_carteira = :endereco
                     ORDER BY m.codigo
                """),
                {"endereco": endereco_carteira},
            ).mappings().all()

        return [dict(r) for r in rows]
    
    def inicializar_saldos(self, endereco_carteira: str, saldos_iniciais: List[SaldoItem]):
        codigos = [s.codigo_moeda for s in saldos_iniciais]
        
        with get_connection() as conn:
            moedas_map = conn.execute(
                text(f"""
                    SELECT id_moeda, codigo
                    FROM moeda
                    WHERE codigo IN ({', '.join(f"'{c}'" for c in codigos)})
                """)
            ).mappings().all()
        
        moeda_id_map = {m["codigo"]: m["id_moeda"] for m in moedas_map}
        
        dados_para_insercao = []
        for saldo_item in saldos_iniciais:
            id_moeda = moeda_id_map.get(saldo_item.codigo_moeda)
            
            if id_moeda is None:
                print(f"Aviso: Moeda {saldo_item.codigo_moeda} não encontrada no DB. Ignorando inicialização.")
                continue
            
            dados_para_insercao.append({
                "endereco_carteira": endereco_carteira,
                "id_moeda": id_moeda,
                "saldo": saldo_item.saldo, # Deve ser 0.00
            })
            
            if dados_para_insercao:
                conn.execute(
                    text("""
                        INSERT INTO saldo_carteira (endereco_carteira, id_moeda, saldo)
                        VALUES (:endereco_carteira, :id_moeda, :saldo)
                    """),
                    dados_para_insercao,
                )