
# SmartLight Solar

O  SmartLight Solar é um aplicativo de automação residencial que combina conforto, tecnologia e sustentabilidade.  
Ele permite controlar dispositivos como ar-condicionado, lâmpadas, câmeras e outros aparelhos inteligentes de forma simples e intuitiva.  
O sistema também oferece relatórios de consumo de energia e um assistente virtual inteligente para comandos e agendamentos.  

---

# Funcionalidades

- 🔑 **Cadastro e Login de Usuário** com autenticação segura (SQLite + hash de senha).  
- 🏠 **Dashboard intuitivo** com botões interativos para cada categoria de dispositivo.  
- 💡 **Controle de dispositivos por cômodo** (liga/desliga com switches).  
- 🤖 **Assistente Virtual**: interpreta comandos como:  
  - "Ligue a lâmpada da sala de estar"  
  - "Desligue o ar condicionado do quarto do Amom às 10:00"  
- 📊 **Relatório de energia**: mostra consumo total em kWh e estimativa de CO₂ evitado.  
- 👤 **Gerenciamento de Conta**: alteração de nome e senha.  
- 📬 **Suporte**: contato direto via e-mail.  

---

# Requisitos

- [Python 3.10+](https://www.python.org/)  
- [Flet](https://flet.dev/)  
- SQLite3 (já incluído no Python)  

---

# Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/smartlight-solar.git
   cd smartlight-solar
2. Crie um ambiente virtual (opcional, mas recomendado):
 
 python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

3. instale as dependências
   pip install -r requirements.txt

# Como executar:
No terminal, rode o comando:

python app.py


O aplicativo abrirá na janela do Flet.

# Estrutura do projeto

smartlight-solar/
│
├── app.py                # Ponto de entrada da aplicação
├── menu.py               # Lógica de telas e funções
├── usuarios.db           # Banco de dados SQLite
├── requirements.txt      # Dependências do projeto
│
├── docs/                 # Documentação e diagramas
│   ├── fluxograma.png
│   ├── arquitetura.png
│   └── circuito.png
│
├── scripts/              # Scripts auxiliares
│   └── init_db.sql
│
└── assets/               # Ícones, imagens, etc.


# Relatórios
O sistema calcula o consumo energético de cada dispositivo com base em médias de kWh/h.
Além disso, apresenta a estimativa de CO₂ evitada pelo uso eficiente da energia.

# Autores
Amom Ianaguivara Brito
Igor Marques Fernandes
Victor Chen
Fernando Antonio de Oliveira Ferraz

