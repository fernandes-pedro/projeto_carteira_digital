import secrets, hashlib, os

def gera_chave():
    """
    Gera a Chave Privada, calcula seu HASH e gera o Endereço (Chave Pública).
    
    Returns:
        tuple: (endereco_carteira, chave_privada_real, hash_chave_privada)
    """
    chave_privada_bytes = secrets.token_bytes(32)
    chave_privada_real = chave_privada_bytes.hex()
    
    endereco_carteira = secrets.token_hex(16)
    
    hash_chave_privada = hashlib.sha256(chave_privada_real.encode('utf-8')).hexdigest()
    
    return endereco_carteira, chave_privada_real, hash_chave_privada
    