# 💼 Sistema de Gerenciamento de Carteiras Digitais

Sistema acadêmico desenvolvido para demonstrar um ambiente completo de **carteiras digitais**, incluindo criação de carteiras, depósitos, saques, conversões de moedas, transferências e consulta de saldos e histórico.  

O projeto apresenta **arquitetura limpa**, boas práticas de desenvolvimento, segurança baseada em hash SHA-256 e camadas bem definidas entre serviço, modelos e banco de dados.

---

## 🧭 Sumário
- [Objetivos Acadêmicos](#-objetivos-acadêmicos)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Segurança](#-segurança)
- [Moedas Suportadas](#-moedas-suportadas)
- [Funcionalidades](#-funcionalidades)
- [Regras de Negócio](#-regras-de-negócio)
- [Fluxo de Uso](#-fluxo-completo-de-uso)
- [Tecnologias Utilizadas](#-tecnologias-e-bibliotecas-utilizadas)
- [Conclusão](#-conclusão)

---

# 🎓 Objetivos Acadêmicos

Este sistema demonstra:

- Construção de API REST com **camadas bem separadas**  
- Uso de **regras financeiras reais**  
- Persistência com SQL  
- Hash seguro de chaves privadas  
- Manipulação de moedas, taxas e operações sensíveis  
- Comunicação com serviços externos (cotação de moedas)  
- Estruturação profissional para trabalhos acadêmicos  

---

# 🏛 Arquitetura do Sistema

O projeto segue uma arquitetura modular:

/api
├── /models → Modelos Pydantic
├── /services → Regras de negócio (CarteiraService)
├── /persistence
│ └── /repositories → Acesso ao banco (CarteiraRepository)
├── /routes → Endpoints REST
└── main.py → Inicialização da API


### ✔ Benefícios:
- Fácil manutenção  
- Testabilidade  
- Baixo acoplamento  
- Reutilização organizada  

---

# 🔐 Segurança

### 🔑 Geração e armazenamento de chaves privadas

Cada carteira criada gera:

- **Endereço público**
- **Chave privada real (retornada apenas 1x)**
- **Hash SHA-256 da chave privada (salvo no banco)**

A chave privada **nunca é armazenada**, somente seu hash.

### Processo:

1. Gera chave privada real  
2. Calcula o hash com SHA-256  
3. Armazena **apenas o hash**  
4. Operações sensíveis comparam:

sha256(chave informada) == hash armazenado


### Operações que exigem chave privada:
- Saque  
- Conversão  
- Transferência  

---

# 💰 Moedas Suportadas

Toda carteira criada inicia com saldo zero nas moedas:

- **BTC**
- **ETH**
- **SOL**
- **USD**
- **BRL**

Essas moedas são obrigatórias e geradas automaticamente.

---

# ⚙️ Funcionalidades

A seguir estão todas as operações implementadas:

---

## 🆕 Criar Carteira
- Gera endereço único  
- Cria chave privada e hash  
- Salva apenas o hash  
- Inicializa as moedas obrigatórias  
- Retorna a chave privada **somente no momento da criação**  

---

## 🔎 Buscar Carteira
Retorna endereço, data de criação e status.

---

## 📜 Listar Carteiras
Lista todas as carteiras cadastradas.

---

## 🔒 Bloquear Carteira
Atualiza o status para **BLOQUEADA**.  
Carteiras bloqueadas não podem realizar operações sensíveis.

---

## 💵 Buscar Saldos
Retorna:

- Código da moeda  
- Nome  
- Saldo atual  
- Data de atualização  

---

## ➕ Depósito
Permite depositar valor positivo em qualquer moeda.

---

## 🏧 Saque (com chave privada)
Regras:
- Valor positivo  
- Chave privada válida  
- Saldo suficiente  
- Taxa aplicada:

TAXA_SAQUE_PERCENTUAL = 1% (0.01)

---

## 🔁 Conversão de Moedas (cotação real)
Processo:

1. Valida chave privada  
2. Busca cotação externa
3. Calcula valor bruto  
4. Aplica taxa de conversão (2%):
5. Registra operação no banco 

TAXA_CONVERSAO_PERCENTUAL = 0.02

---

## 📤 Transferência entre Carteiras
Regras:

- Exige chave privada da origem  
- Carteira destino deve existir  
- Verifica saldo  
- Aplica taxa:

TAXA_TRANSFERENCIA_PERCENTUAL = 0.0

---

# 📚 Regras de Negócio

✔ Chave privada real nunca é salva  
✔ Carteiras bloqueadas não operam  
✔ Todas operações são registradas em histórico  
✔ Taxas configuradas via variáveis de ambiente:

TAXA_SAQUE_PERCENTUAL=0.01
TAXA_CONVERSAO_PERCENTUAL=0.02
TAXA_TRANSFERENCIA_PERCENTUAL=0.01

✔ Moedas obrigatórias instaladas automaticamente  

---

# 🔄 Fluxo Completo de Uso

1. Criar carteira  
2. Guardar a chave privada (não é possível recuperar depois)  
3. Depositar valores  
4. Converter ou transferir  
5. Consultar saldos  
6. Bloquear quando necessário  

---

# 🛠 Tecnologias e Bibliotecas Utilizadas

- **Python 3.11+**  
- **FastAPI**  
- **Pydantic**  
- **PostgreSQL / SQLite**  
- **hashlib (SHA-256)**  
- **Decimal (precisão financeira)**  
- **async/await para cotações externas**  

---

# 📌 Conclusão

Este projeto apresenta um sistema completo de gestão de carteiras digitais, construído com:

- Arquitetura organizada;  
- Regras de negócio realistas;  
- Segurança com hash SHA-256;  
- Persistência sólida;  
- Divisão clara entre camadas.  

Ideal para fins acadêmicos e estudos avançados de APIs, sistemas financeiros e boas práticas de software.

---

Se quiser, posso adicionar:

📊 **Fluxograma das operações**  
📘 **Versão em inglês**  
🛠 **Badges do GitHub**  
📄 **Diagrama UML**  
📦 **Seção de instalação e execução**  