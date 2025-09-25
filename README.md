# Classificador de Emails IA com FastAPI

Este é um projeto feito para o processo seletivo da AutoU, considerei TODOS os tópicos do desafio. é uma aplicação web para classificação automática de emails e geração de respostas sugeridas, utilizando FastAPI para o backend e Groq AI para inteligência artificial. O frontend é construído com HTML, CSS e JavaScript puros, oferecendo uma interface responsiva.
  

## Funcionalidades
-   **Backend FastAPI**: API robusta e de alta performance.
-   **Groq AI Integration**: Classificação de emails (Produtivo/Improdutivo) e geração de respostas inteligentes.
-   **Frontend Interativo**: Interface de usuário intuitiva.
-   **Múltiplas Entradas**: Suporte para upload de arquivos (.txt, .pdf) e entrada de texto direto.
-   **Modo Claro/Escuro**: Alternância de tema para melhor experiência visual.
-   **Estatísticas de Performance**: Visualização de tempos de processamento da IA.

## Pré-requisitos
Certifique-se de ter instalado:

-   [Python 3.11+](https://www.python.org/downloads/)
-   `pip` (gerenciador de pacotes do Python)

## Instalação
1.  **Clone o repositório** (ou extraia o arquivo ZIP do projeto):

    ```bash
    git clone https://github.com/iamyago/EmailAI
    cd email-classifier-fastapi
    ```

2.  **Instale as dependências** do Python:

    ```bash
    pip install -r requirements.txt
    ```
    
3.  **Configure sua chave Groq API** (opcional, uma chave de teste já está embutida):

    Defina a variável de ambiente `GROQ_API_KEY` com sua chave. Exemplo:

    ```bash
    # Linux/macOS
    export GROQ_API_KEY="sua_chave_aqui"

    # Windows (CMD)
    set GROQ_API_KEY=sua_chave_aqui
    ```

## Como Usar

### 1. Iniciar a Aplicação

Execute o servidor FastAPI:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Acessar a Interface

Abra seu navegador e acesse:

-   **Interface Principal**: [http://localhost:8000](http://localhost:8000)
-   **Documentação da API (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
-   **Status da API**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 3. Classificar Emails

Na interface, você pode:

-   **Upload de Arquivo**: Clique na aba "📁 Upload de Arquivo", selecione um `.txt` ou `.pdf` (até 10MB) e clique em "🔍 Analisar Email".
-   **Texto Direto**: Clique na aba "✏️ Texto Direto", digite ou cole o conteúdo do email e clique em "🔍 Analisar Email".

Os resultados mostrarão a classificação (Produtivo/Improdutivo), uma justificativa, uma resposta sugerida e estatísticas de processamento.

## 📂 Estrutura do Projeto

```
email-classifier-fastapi/
├── main.py                 # Aplicação FastAPI principal
├── requirements.txt        # Dependências Python
├── static/                 # Arquivos estáticos do frontend
│   ├── index.html         # Interface principal
│   ├── style.css          # Estilos CSS
│   └── script.js          # Lógica JavaScript
├── test_email.txt         # Exemplo de arquivo para teste
├── README.md              # Este arquivo
├── WINDOWS_SETUP.md       # Guia de instalação para Windows
└── API_DOCUMENTATION.md   # Documentação técnica da API
```

## Troubleshooting

-   **`Address already in use`**: A porta 8000 já está sendo usada. Tente iniciar em outra porta (`--port 8001`) ou encerre o processo que está usando a porta.
-   **`ModuleNotFoundError`**: Certifique-se de que todas as dependências foram instaladas (`pip install -r requirements.txt`).
-   **Problemas com Groq AI**: Verifique sua conexão com a internet e se a `GROQ_API_KEY` está correta. O sistema possui um fallback para classificação baseada em regras.

---

