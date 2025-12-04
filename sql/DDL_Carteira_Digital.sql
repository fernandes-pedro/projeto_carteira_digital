-- =========================================================
--  Script de criação da base, usuário,
--  Projeto: Carteira Digital
--  Banco:   MySQL 8+
-- =========================================================

-- 1) Criação da base de homologação
CREATE DATABASE IF NOT EXISTS wallet_homolog
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_0900_ai_ci;

-- 2) Criação do usuário restrito para a API
--    (ajuste a senha conforme necessário)
CREATE USER IF NOT EXISTS 'wallet_api_homolog'@'%'
    IDENTIFIED BY 'api123';

-- 3) Grants: apenas DML (sem CREATE/DROP/ALTER)
GRANT SELECT, INSERT, UPDATE, DELETE
    ON wallet_homolog.*
    TO 'wallet_api_homolog'@'%';

FLUSH PRIVILEGES;

-- 4) Usar a base
USE wallet_homolog;

-- =========================================================
--  Tabelas (Aluno deve fazer o modelo)
-- =========================================================

Create Table IF NOT EXISTS MOEDA(
    id_moeda SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    codigo varchar(5) UNIQUE NOT NULL,
    nome varchar(50) NOT NULL,
    tipo varchar(50) NOT NULL
);

INSERT INTO MOEDA(codigo, nome, tipo) VALUES
('USD', 'Dólar Americano', 'FIAT'),
('SOL', 'Solana', 'CRYPTO'),
('BTC', 'Bitcoin', 'CRYPTO'),
('ETH', 'Ethereum', 'CRYPTO')
ON DUPLICATE KEY UPDATE codigo=codigo;

Create Table IF NOT EXISTS CARTEIRA(
    endereco_carteira CHAR(32) NOT NULL PRIMARY KEY,
    hash_chave_privada VARCHAR(64) NOT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_ativo varchar(10) NOT NULL DEFAULT 'ATIVO'
);

Create Table IF NOT EXISTS SALDO_CARTEIRA(
    endereco_carteira CHAR(32) NOT NULL,
    id_moeda SMALLINT NOT NULL,
    saldo DECIMAL(18,8) NOT NULL DEFAULT 0.00,
    data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY(endereco_carteira, id_moeda),
    FOREIGN KEY(endereco_carteira) REFERENCES CARTEIRA(endereco_carteira),
    FOREIGN KEY(id_moeda) REFERENCES MOEDA(id_moeda)
    
);