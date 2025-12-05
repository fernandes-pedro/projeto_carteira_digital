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
                           hash_chave_privada,
                           data_criacao,
                           status_ativo AS status
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
                           hash_chave_privada,
                           data_criacao,
                           status_ativo AS status
                      FROM carteira
                     ORDER BY data_criacao DESC
                """)
            ).mappings().all()

        return [dict(r) for r in rows]


    def atualizar_status(self, endereco_carteira: str, status: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            resultado = conn.execute(
                text("""
                    UPDATE carteira
                       SET status_ativo = :status
                     WHERE endereco_carteira = :endereco
                """),
                {"status": status, "endereco": endereco_carteira},
            )

            if resultado.rowcount == 0:
                return None
            
            row = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           hash_chave_privada,
                           data_criacao,
                           status_ativo AS status
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
                    "saldo": saldo_item.saldo,
                })
            
            if dados_para_insercao:
                conn.execute(
                    text("""
                        INSERT INTO saldo_carteira (endereco_carteira, id_moeda, saldo)
                        VALUES (:endereco_carteira, :id_moeda, :saldo)
                    """),
                    dados_para_insercao,
                )
    
    def validar_chave_privada(self, endereco_carteira: str, chave_privada: str) -> bool:
        """
        Verifica se a chave privada fornecida corresponde ao hash armazenado para o endereço.
        """
        hash_fornecido = hashlib.sha256(chave_privada.encode('utf-8')).hexdigest()
        
        with get_connection() as conn:
            row = conn.execute(
                text("""
                    SELECT hash_chave_privada
                      FROM carteira
                     WHERE endereco_carteira = :endereco
                """),
                {"endereco": endereco_carteira},
            ).mappings().first()

        if not row:
            return False
            
        hash_armazenado = row["hash_chave_privada"]
        return hash_fornecido == hash_armazenado


    def registrar_deposito(self, endereco_carteira: str, codigo_moeda: str, valor: Decimal) -> Dict[str, Any]:
        with get_connection() as conn:
            moeda_row = conn.execute(
                text("SELECT id_moeda FROM moeda WHERE codigo = :codigo"),
                {"codigo": codigo_moeda}
            ).mappings().first()

            if not moeda_row:
                raise ValueError(f"Moeda com código {codigo_moeda} não encontrada.")
            
            id_moeda = moeda_row["id_moeda"]

            movimento_result = conn.execute(
                text("""
                    INSERT INTO deposito_saque (endereco_carteira, id_moeda, tipo, valor, taxa_valor)
                    VALUES (:endereco, :id_moeda, 'DEPOSITO', :valor, 0.00)
                """),
                {
                    "endereco": endereco_carteira,
                    "id_moeda": id_moeda,
                    "valor": valor
                },
            )
            
            id_movimento = movimento_result.lastrowid

            conn.execute(
                text("""
                    INSERT INTO saldo_carteira (endereco_carteira, id_moeda, saldo)
                    VALUES (:endereco, :id_moeda, :valor)
                    ON DUPLICATE KEY UPDATE saldo = saldo + :valor, data_atualizacao = CURRENT_TIMESTAMP
                """),
                {
                    "endereco": endereco_carteira,
                    "id_moeda": id_moeda,
                    "valor": valor
                },
            )

            movimento_data = conn.execute(
                text("""
                    SELECT id_movimento, data_hora
                    FROM deposito_saque
                    WHERE id_movimento = :id
                """),
                {"id": id_movimento}
            ).mappings().first()
        
        return {
            "id_movimento": id_movimento,
            "endereco_carteira": endereco_carteira,
            "codigo_moeda": codigo_moeda,
            "tipo": "DEPOSITO",
            "valor": valor,
            "taxa_valor": Decimal("0.00"),
            "data_hora": movimento_data["data_hora"]
        }
        
    def registrar_saque(self, endereco_carteira: str, codigo_moeda: str, valor: Decimal, taxa: Decimal, valor_total_debito: Decimal) -> Dict[str, Any]:
        """
        Executa o saque de forma transacional: verifica saldo, registra o movimento e debita o saldo.
        """
        with get_connection() as conn:
            moeda_row = conn.execute(
                text("SELECT id_moeda FROM moeda WHERE codigo = :codigo"),
                {"codigo": codigo_moeda}
            ).mappings().first()

            if not moeda_row:
                raise ValueError(f"Moeda com código {codigo_moeda} não encontrada.")
            
            id_moeda = moeda_row["id_moeda"]

            saldo_row = conn.execute(
                text("""
                    SELECT saldo FROM saldo_carteira
                    WHERE endereco_carteira = :endereco AND id_moeda = :id_moeda
                    FOR UPDATE
                """),
                {"endereco": endereco_carteira, "id_moeda": id_moeda}
            ).mappings().first()

            saldo_atual = saldo_row["saldo"] if saldo_row else Decimal("0.00")
            
            if saldo_atual < valor_total_debito:
                raise ValueError(f"Saldo insuficiente ({saldo_atual}) para débito total de ({valor_total_debito}).")

            movimento_result = conn.execute(
                text("""
                    INSERT INTO deposito_saque (endereco_carteira, id_moeda, tipo, valor, taxa_valor)
                    VALUES (:endereco, :id_moeda, 'SAQUE', :valor, :taxa)
                """),
                {
                    "endereco": endereco_carteira,
                    "id_moeda": id_moeda,
                    "valor": valor,
                    "taxa": taxa
                },
            )
            
            id_movimento = movimento_result.lastrowid

            conn.execute(
                text("""
                    UPDATE saldo_carteira
                    SET saldo = saldo - :total_debito, data_atualizacao = CURRENT_TIMESTAMP
                    WHERE endereco_carteira = :endereco AND id_moeda = :id_moeda
                """),
                {
                    "endereco": endereco_carteira,
                    "id_moeda": id_moeda,
                    "total_debito": valor_total_debito
                },
            )

            movimento_data = conn.execute(
                text("""
                    SELECT data_hora
                    FROM deposito_saque
                    WHERE id_movimento = :id
                """),
                {"id": id_movimento}
            ).mappings().first()
        
        return {
            "id_movimento": id_movimento,
            "endereco_carteira": endereco_carteira,
            "codigo_moeda": codigo_moeda,
            "tipo": "SAQUE",
            "valor": valor,
            "taxa_valor": taxa,
            "data_hora": movimento_data["data_hora"]
        }
    
    def registrar_conversao(self, endereco_carteira: str, codigo_origem: str, codigo_destino: str, 
                            valor_origem: Decimal, valor_destino: Decimal, taxa_percentual: Decimal, 
                            taxa_valor: Decimal, cotacao_utilizada: Decimal) -> Dict[str, Any]:
        """
        Executa a conversão de forma transacional: registra a operação, debita a origem e credita o destino.
        """
        with get_connection() as conn:
            moedas_map = conn.execute(
                text("""
                    SELECT id_moeda, codigo
                    FROM moeda
                    WHERE codigo IN (:origem, :destino)
                """),
                {"origem": codigo_origem, "destino": codigo_destino}
            ).mappings().all()

            if len(moedas_map) < 2:
                raise ValueError("Moeda de origem ou destino não encontrada no cadastro.")
            
            id_moeda_origem = next(m["id_moeda"] for m in moedas_map if m["codigo"] == codigo_origem)
            id_moeda_destino = next(m["id_moeda"] for m in moedas_map if m["codigo"] == codigo_destino)

            saldo_origem_row = conn.execute(
                text("""
                    SELECT saldo FROM saldo_carteira
                    WHERE endereco_carteira = :endereco AND id_moeda = :id_origem
                    FOR UPDATE
                """),
                {"endereco": endereco_carteira, "id_origem": id_moeda_origem}
            ).mappings().first()

            saldo_atual = saldo_origem_row["saldo"] if saldo_origem_row else Decimal("0.00")
            
            if saldo_atual < valor_origem:
                raise ValueError(f"Saldo insuficiente ({saldo_atual}) na moeda {codigo_origem} para conversão.")

            conn.execute(
                text("""
                    UPDATE saldo_carteira
                       SET saldo = saldo - :valor_origem, data_atualizacao = CURRENT_TIMESTAMP
                     WHERE endereco_carteira = :endereco AND id_moeda = :id_origem
                """),
                {
                    "endereco": endereco_carteira,
                    "id_origem": id_moeda_origem,
                    "valor_origem": valor_origem
                },
            )
            
            conn.execute(
                text("""
                    INSERT INTO saldo_carteira (endereco_carteira, id_moeda, saldo)
                    VALUES (:endereco, :id_destino, :valor_destino)
                    ON DUPLICATE KEY UPDATE saldo = saldo + :valor_destino, data_atualizacao = CURRENT_TIMESTAMP
                """),
                {
                    "endereco": endereco_carteira,
                    "id_destino": id_moeda_destino,
                    "valor_destino": valor_destino
                },
            )
            
            movimento_result = conn.execute(
                text("""
                    INSERT INTO conversao (endereco_carteira, id_moeda_origem, id_moeda_destino, valor_origem, 
                                           valor_destino, taxa_percentual, taxa_valor, cotacao_utilizada)
                    VALUES (:endereco, :id_origem, :id_destino, :v_origem, :v_destino, :t_perc, :t_valor, :cotacao)
                """),
                {
                    "endereco": endereco_carteira,
                    "id_origem": id_moeda_origem,
                    "id_destino": id_moeda_destino,
                    "v_origem": valor_origem,
                    "v_destino": valor_destino,
                    "t_perc": taxa_percentual,
                    "t_valor": taxa_valor,
                    "cotacao": cotacao_utilizada
                },
            )
            
            id_conversao = movimento_result.lastrowid
            
            movimento_data = conn.execute(
                text("""
                    SELECT data_hora FROM conversao WHERE id_conversao = :id
                """),
                {"id": id_conversao}
            ).mappings().first()
                
        return {
            "id_conversao": id_conversao,
            "endereco_carteira": endereco_carteira,
            "codigo_origem": codigo_origem,
            "codigo_destino": codigo_destino,
            "valor_origem": valor_origem,
            "valor_destino": valor_destino,
            "taxa_valor": taxa_valor,
            "cotacao_utilizada": cotacao_utilizada,
            "data_hora": movimento_data["data_hora"]
        }
        
    def registrar_transferencia(self, endereco_origem: str, endereco_destino: str, codigo_moeda: str, 
                                valor_liquido: Decimal, valor_total_debito: Decimal, taxa_valor: Decimal) -> Dict[str, Any]:
        """
        Executa a transferência de forma transacional: debita a origem, credita o destino e registra o movimento.
        """
        with get_connection() as conn:
            moeda_row = conn.execute(
                text("SELECT id_moeda FROM moeda WHERE codigo = :codigo"),
                {"codigo": codigo_moeda}
            ).mappings().first()

            if not moeda_row:
                raise ValueError(f"Moeda com código {codigo_moeda} não encontrada.")
            
            id_moeda = moeda_row["id_moeda"]

            saldo_origem_row = conn.execute(
                text("""
                    SELECT saldo FROM saldo_carteira
                    WHERE endereco_carteira = :endereco_origem AND id_moeda = :id_moeda
                    FOR UPDATE
                """),
                {"endereco_origem": endereco_origem, "id_moeda": id_moeda}
            ).mappings().first()

            saldo_atual = saldo_origem_row["saldo"] if saldo_origem_row else Decimal("0.00")
            
            if saldo_atual < valor_total_debito:
                raise ValueError(f"Saldo insuficiente ({saldo_atual}) na origem para débito total de ({valor_total_debito}).")

            conn.execute(
                text("""
                    UPDATE saldo_carteira
                       SET saldo = saldo - :total_debito, data_atualizacao = CURRENT_TIMESTAMP
                     WHERE endereco_carteira = :endereco_origem AND id_moeda = :id_moeda
                """),
                {
                    "endereco_origem": endereco_origem,
                    "id_moeda": id_moeda,
                    "total_debito": valor_total_debito
                },
            )
            
            conn.execute(
                text("""
                    INSERT INTO saldo_carteira (endereco_carteira, id_moeda, saldo)
                    VALUES (:endereco_destino, :id_moeda, :valor_liquido)
                    ON DUPLICATE KEY UPDATE saldo = saldo + :valor_liquido, data_atualizacao = CURRENT_TIMESTAMP
                """),
                {
                    "endereco_destino": endereco_destino,
                    "id_moeda": id_moeda,
                    "valor_liquido": valor_liquido
                },
            )
            
            movimento_result = conn.execute(
                text("""
                    INSERT INTO transferencia (endereco_origem, endereco_destino, id_moeda, valor, taxa_valor)
                    VALUES (:origem, :destino, :id_moeda, :valor_liquido, :taxa_valor)
                """),
                {
                    "origem": endereco_origem,
                    "destino": endereco_destino,
                    "id_moeda": id_moeda,
                    "valor_liquido": valor_liquido,
                    "taxa_valor": taxa_valor
                },
            )
            
            id_transferencia = movimento_result.lastrowid
            
            movimento_data = conn.execute(
                text("""
                    SELECT data_hora FROM transferencia WHERE id_transferencia = :id
                """),
                {"id": id_transferencia}
            ).mappings().first()
                
        return {
            "id_transferencia": id_transferencia,
            "endereco_origem": endereco_origem,
            "endereco_destino": endereco_destino,
            "codigo_moeda": codigo_moeda,
            "valor": valor_liquido,
            "taxa_valor": taxa_valor,
            "data_hora": movimento_data["data_hora"]
        }