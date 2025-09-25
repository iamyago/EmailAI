# Documentação Técnica da API - Classificador de Emails IA

Esta documentação fornece detalhes técnicos sobre os endpoints, modelos de dados e integração da API.

## 🔗 Base URL

```
http://localhost:8000
```

## 📋 Endpoints

### 1. Página Principal
```http
GET /
```

**Descrição**: Retorna a interface web principal da aplicação.

**Resposta**: HTML da interface do usuário

---

### 2. Status da API
```http
GET /api/health
```

**Descrição**: Verifica o status da API e conectividade com serviços externos.

**Resposta**:
```json
{
  "status": "OK",
  "message": "Email classifier service is running",
  "ai_provider": "Groq AI",
  "groq_status": "Connected",
  "supported_formats": ["txt", "pdf"],
  "max_file_size_mb": 10,
  "version": "2.0.0"
}
```

**Códigos de Status**:
- `200`: Serviço funcionando normalmente
- `503`: Serviço indisponível

---

### 3. Classificar Email
```http
POST /api/email/classify
```

**Descrição**: Classifica um email e gera resposta sugerida.

**Content-Type**: `multipart/form-data`

**Parâmetros**:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `email_content` | string | Condicional* | Conteúdo do email em texto |
| `file` | file | Condicional* | Arquivo .txt ou .pdf |

*Um dos dois parâmetros deve ser fornecido.

**Limitações**:
- Texto: máximo 50.000 caracteres
- Arquivo: máximo 10MB, formatos .txt e .pdf

**Exemplo de Requisição (texto)**:
```bash
curl -X POST "http://localhost:8000/api/email/classify" \
  -F "email_content=Olá, preciso de ajuda com o sistema."
```

**Exemplo de Requisição (arquivo)**:
```bash
curl -X POST "http://localhost:8000/api/email/classify" \
  -F "file=@email.txt"
```

**Resposta de Sucesso** (200):
```json
{
  "classification": "PRODUTIVO",
  "classification_reason": "Este email contém solicitações, dúvidas ou questões que requerem ação ou resposta específica da equipe.",
  "suggested_response": "Prezado(a),\n\nObrigado pelo seu email. Recebemos sua mensagem e nossa equipe técnica irá analisá-la com atenção.\n\nEntraremos em contato em breve com mais informações ou a solução para sua solicitação. Nosso prazo padrão de resposta é de até 24 horas para questões técnicas.\n\nCaso seja um problema urgente, por favor entre em contato através do nosso telefone de suporte.\n\nAtenciosamente,\nEquipe de Suporte Técnico",
  "analyzed_content": "Olá, preciso de ajuda com o sistema.",
  "char_count": 35,
  "classification_time": 0.15,
  "generation_time": 0.07,
  "model_used": "llama3-8b-8192"
}
```

**Códigos de Erro**:
- `400`: Dados inválidos ou ausentes
- `413`: Arquivo muito grande
- `415`: Formato de arquivo não suportado
- `422`: Erro de validação
- `500`: Erro interno do servidor

**Exemplos de Erro**:
```json
{
  "detail": "Por favor, forneça o conteúdo do email ou um arquivo."
}
```

---

### 4. Documentação Interativa
```http
GET /docs
```

**Descrição**: Interface Swagger UI para testar a API interativamente.

**Resposta**: Interface HTML do Swagger UI

---

### 5. Esquema OpenAPI
```http
GET /openapi.json
```

**Descrição**: Esquema OpenAPI 3.0 da API em formato JSON.

**Resposta**: JSON com especificação completa da API

---

## 📊 Modelos de Dados

### EmailRequest
```python
{
  "email_content": "string"  # Conteúdo do email
}
```

### EmailResponse
```python
{
  "classification": "string",        # "PRODUTIVO" ou "IMPRODUTIVO"
  "classification_reason": "string", # Justificativa da classificação
  "suggested_response": "string",    # Resposta sugerida
  "analyzed_content": "string",      # Conteúdo processado
  "char_count": "integer",          # Número de caracteres
  "classification_time": "float",    # Tempo de classificação (segundos)
  "generation_time": "float",       # Tempo de geração (segundos)
  "model_used": "string"            # Modelo de IA utilizado
}
```

### HealthResponse
```python
{
  "status": "string",              # Status do serviço
  "message": "string",             # Mensagem descritiva
  "ai_provider": "string",         # Provedor de IA
  "groq_status": "string",         # Status da conexão Groq
  "supported_formats": ["string"], # Formatos suportados
  "max_file_size_mb": "integer",   # Tamanho máximo do arquivo
  "version": "string"              # Versão da API
}
```

## 🤖 Integração com IA

### Groq AI
- **Modelo**: `llama3-8b-8192`
- **Provedor**: Groq AI
- **Fallback**: Classificação baseada em regras

### Prompts do Sistema

#### Classificação:
```
Você é um especialista em classificação de emails corporativos para uma empresa do setor financeiro.

Sua tarefa é classificar emails em duas categorias:

PRODUTIVO: Emails que requerem ação ou resposta específica
IMPRODUTIVO: Emails que não necessitam ação imediata

Analise o contexto, intenção e urgência da mensagem. Responda APENAS com "PRODUTIVO" ou "IMPRODUTIVO".
```

#### Geração de Resposta:
```
Você é um assistente de atendimento ao cliente de uma empresa do setor financeiro. 
Gere uma resposta automática profissional, cordial e útil para emails produtivos.

A resposta deve:
- Ser cordial e profissional
- Confirmar o recebimento da mensagem
- Indicar que a solicitação será analisada
- Fornecer expectativa de prazo quando apropriado
- Ser concisa (máximo 4 parágrafos)
- Usar linguagem formal mas acessível
- Incluir uma assinatura profissional
```

## 🔧 Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `GROQ_API_KEY` | Chave da API Groq | Chave de teste incluída |
| `HOST` | Host do servidor | `0.0.0.0` |
| `PORT` | Porta do servidor | `8000` |

### Configurações Internas

```python
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_LENGTH = 50000           # 50k caracteres
```

## 🚀 Performance

### Métricas Típicas
- **Classificação**: 0.1-0.2 segundos
- **Geração de Resposta**: 0.05-0.1 segundos
- **Processamento Total**: 0.15-0.3 segundos
- **Throughput**: ~10-20 requisições/segundo

### Otimizações
- Cache de modelos em memória
- Processamento assíncrono
- Validação rápida de entrada
- Fallback para classificação local

## 🔒 Segurança

### Validações
- Tipo de arquivo (whitelist)
- Tamanho de arquivo (10MB máximo)
- Comprimento de texto (50k caracteres)
- Sanitização de entrada

### Headers de Segurança
- CORS configurado para desenvolvimento
- Validação de Content-Type
- Rate limiting (pode ser implementado)

## 🧪 Testes

### Teste Manual via cURL

**Classificação de texto**:
```bash
curl -X POST "http://localhost:8000/api/email/classify" \
  -F "email_content=Preciso de ajuda urgente com o sistema"
```

**Upload de arquivo**:
```bash
curl -X POST "http://localhost:8000/api/email/classify" \
  -F "file=@test_email.txt"
```

**Status da API**:
```bash
curl -X GET "http://localhost:8000/api/health"
```

### Teste via Python

```python
import requests

# Teste de classificação
response = requests.post(
    "http://localhost:8000/api/email/classify",
    data={"email_content": "Olá, preciso de suporte técnico"}
)
print(response.json())

# Teste de status
health = requests.get("http://localhost:8000/api/health")
print(health.json())
```

### Teste via JavaScript

```javascript
// Teste de classificação
const formData = new FormData();
formData.append('email_content', 'Preciso de ajuda com o sistema');

fetch('/api/email/classify', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 📈 Monitoramento

### Logs
- Requests HTTP
- Tempos de resposta
- Erros de classificação
- Status da conexão Groq

### Métricas Disponíveis
- Tempo de classificação
- Tempo de geração
- Contagem de caracteres
- Modelo utilizado

## 🔄 Versionamento

### Versão Atual: 2.0.0

**Changelog**:
- Migração completa para FastAPI
- Nova interface de usuário
- Melhor integração com Groq AI
- Documentação automática
- Tratamento de erros aprimorado

---


