from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import os
import re
import time
import io
from typing import Optional
import PyPDF2
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv() # Carrega as variáveis do arquivo .env

# Agora o os.getenv vai encontrar a variável que foi carregada
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI(
    title="Email Classifier AI",
    description="AI-powered email classification and response generation using Groq AI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# PASSAR A KEY É OPCIONAL (EU NÃO RECOMENDO)
# GROQ_API_KEY = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and GROQ_API_KEY.startswith('gsk_') else None

ALLOWED_EXTENSIONS = {'txt', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class EmailRequest(BaseModel):
    email_content: str

class FileRequest(BaseModel):
    file_content: str
    file_type: str

class EmailResponse(BaseModel):
    classification: str
    classification_reason: str
    suggested_response: str
    analyzed_content: str
    char_count: int
    classification_time: float
    generation_time: float
    model_used: str

def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text += f"\n--- Página {page_num + 1} ---\n{page_text}\n"
            except Exception as e:
                text += f"\n--- Erro na página {page_num + 1}: {str(e)} ---\n"
        
        return text.strip() if text.strip() else "Não foi possível extrair texto do PDF."
        
    except Exception as e:
        return f"Erro ao processar PDF: {str(e)}"

def preprocess_text(text: str) -> str:
    
    if not text or not isinstance(text, str):
        return ""

    text = re.sub(r'\s+', ' ', text.strip())
    
   
    text = re.sub(r'^(From|To|Subject|Date|Cc|Bcc|Reply-To|Message-ID):.*?\n', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'\n--+\n.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'\nEnviado do meu.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\nSent from my.*$', '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def classify_email_with_groq(email_content: str) -> str:
    if not groq_client:
        return classify_email_fallback(email_content)
    
    try:
        system_prompt = """Você é um especialista em classificação de emails corporativos para uma empresa do setor financeiro.

Sua tarefa é classificar emails em duas categorias:

PRODUTIVO: Emails que requerem ação ou resposta específica, incluindo:
- Solicitações de suporte técnico
- Dúvidas sobre sistemas ou processos
- Relatórios de problemas ou erros
- Pedidos de informação ou documentos
- Atualizações de status de projetos
- Questões relacionadas ao trabalho
- Reuniões e agendamentos
- Problemas urgentes

IMPRODUTIVO: Emails que não necessitam ação imediata, incluindo:
- Mensagens de felicitações (aniversários, feriados)
- Agradecimentos simples
- Mensagens pessoais não relacionadas ao trabalho
- Spam ou mensagens promocionais
- Cumprimentos sociais
- Mensagens de "bom dia/boa tarde" sem conteúdo adicional

Analise o contexto, intenção e urgência da mensagem. Responda APENAS com "PRODUTIVO" ou "IMPRODUTIVO"."""

        user_prompt = f"""Classifique o seguinte email:

{email_content}

Classificação:"""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=10,
            temperature=0.1,
            top_p=0.9,
            stream=False
        )
        
        classification = completion.choices[0].message.content.strip().upper()
        
        # Valdação da resposta
        if classification in ["PRODUTIVO", "IMPRODUTIVO"]:
            return classification
        elif "PRODUTIVO" in classification:
            return "PRODUTIVO"
        elif "IMPRODUTIVO" in classification:
            return "IMPRODUTIVO"
        else:
            return "PRODUTIVO"  # Padrão para evitar perda de emails importantes
            
    except Exception as e:
        print(f"Erro na classificação com Groq: {str(e)}")
        return classify_email_fallback(email_content)

def classify_email_fallback(email_content: str) -> str:

    content_lower = email_content.lower()
    
    
    productive_keywords = [
        'problema', 'erro', 'bug', 'falha', 'suporte', 'ajuda', 'urgente', 'crítico',
        'solicitação', 'pedido', 'dúvida', 'questão', 'informação', 'documento',
        'status', 'atualização', 'relatório', 'reunião', 'projeto', 'prazo',
        'entrega', 'sistema', 'aplicação', 'login', 'acesso', 'senha',
        'manutenção', 'correção', 'instalação', 'configuração', 'backup',
        'segurança', 'vírus', 'lento', 'travando', 'não funciona', 'indisponível'
    ]
    
    
    unproductive_keywords = [
        'feliz', 'parabéns', 'aniversário', 'natal', 'ano novo', 'feriado',
        'obrigado', 'obrigada', 'agradecimento', 'agradecimentos', 'gratidão',
        'cumprimento', 'cumprimentos', 'saudação', 'saudações',
        'bom dia', 'boa tarde', 'boa noite', 'bom final de semana',
        'feliz páscoa', 'feliz natal', 'próspero ano novo'
    ]
    
  
    productive_score = 0
    unproductive_score = 0
    
    for keyword in productive_keywords:
        if keyword in content_lower:
            weight = 2 if keyword in ['problema', 'erro', 'urgente', 'crítico', 'suporte'] else 1
            productive_score += weight
    
    for keyword in unproductive_keywords:
        if keyword in content_lower:
            unproductive_score += 1
    
  
    if any(word in content_lower for word in ['?', 'como', 'quando', 'onde', 'por que', 'preciso']):
        productive_score += 1
    
    if len(email_content.split()) < 10 and unproductive_score > 0:
        unproductive_score += 1
    
   
    if productive_score > unproductive_score:
        return "PRODUTIVO"
    elif unproductive_score > productive_score:
        return "IMPRODUTIVO"
    else:
        if '?' in email_content or any(word in content_lower for word in ['preciso', 'gostaria', 'poderia']):
            return "PRODUTIVO"
        return "PRODUTIVO"

def generate_classification_reason(email_content: str, classification: str) -> str:
  
    if classification == "PRODUTIVO":
        return "Este email contém solicitações, dúvidas ou questões que requerem ação ou resposta específica da equipe."
    else:
        return "Este email contém mensagens de cortesia, agradecimentos ou cumprimentos que não necessitam ação imediata."

def generate_response_with_groq(email_content: str, classification: str) -> str:
    
    if not groq_client:
        return generate_response_fallback(email_content, classification)
    
    try:
        if classification == "PRODUTIVO":
            system_prompt = """Você é um assistente de atendimento ao cliente de uma empresa do setor financeiro. 
Gere uma resposta automática profissional, cordial e útil para emails produtivos.

A resposta deve:
- Ser cordial e profissional
- Confirmar o recebimento da mensagem
- Indicar que a solicitação será analisada
- Fornecer expectativa de prazo quando apropriado
- Ser concisa (máximo 4 parágrafos)
- Usar linguagem formal mas acessível
- Incluir uma assinatura profissional

Não mencione detalhes específicos que não foram fornecidos no email original."""

            user_prompt = f"""Gere uma resposta automática para este email produtivo:

{email_content}

Resposta:"""

        else:  # IMPRODUTIVO
            system_prompt = """Você é um assistente de atendimento ao cliente de uma empresa do setor financeiro.
Gere uma resposta automática cordial e amigável para emails improdutivos.

A resposta deve:
- Ser educada e calorosa
- Agradecer pela mensagem
- Retribuir o sentimento quando apropriado
- Ser breve (máximo 2 parágrafos)
- Manter tom profissional mas amigável
- Incluir uma assinatura profissional"""

            user_prompt = f"""Gere uma resposta automática para este email improdutivo:

{email_content}

Resposta:"""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
            stream=False
        )
        
        response = completion.choices[0].message.content.strip()
        
        if not response:
            return generate_response_fallback(email_content, classification)
            
        return response
        
    except Exception as e:
        print(f"Erro na geração de resposta com Groq: {str(e)}")
        return generate_response_fallback(email_content, classification)

def generate_response_fallback(email_content: str, classification: str) -> str:

    if classification == "PRODUTIVO":
        return """Prezado(a),

Obrigado pelo seu email. Recebemos sua mensagem e nossa equipe técnica irá analisá-la com atenção.

Entraremos em contato em breve com mais informações ou a solução para sua solicitação. Nosso prazo padrão de resposta é de até 24 horas para questões técnicas.

Caso seja um problema urgente, por favor entre em contato através do nosso telefone de suporte.

Atenciosamente,
Equipe de Suporte Técnico"""
    else:
        return """Prezado(a),

Muito obrigado pela sua mensagem! Ficamos felizes em receber seu contato.

Desejamos um excelente dia e agradecemos por fazer parte da nossa comunidade.

Atenciosamente,
Equipe de Atendimento"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
  
    return FileResponse("static/index.html")

@app.post("/api/email/classify")
async def classify_email(
    email_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    
    start_time = time.time()
    
    try:
        content = ""
        
    
        if file:
            if file.size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            file_content = await file.read()
            
            if file.filename.lower().endswith('.pdf'):
                content = extract_text_from_pdf(file_content)
            else:
                try:
                    content = file_content.decode('utf-8', errors='ignore')
                except Exception:
                    content = file_content.decode('latin-1', errors='ignore')
        
        
        elif email_content:
            content = email_content
        
        if not content or not content.strip():
            raise HTTPException(
                status_code=400,
                detail="Nenhum conteúdo de email fornecido. Por favor, envie um arquivo ou digite o texto do email."
            )
        
        
        if len(content) > 50000:
            raise HTTPException(
                status_code=400,
                detail="Conteúdo muito longo. Limite máximo: 50.000 caracteres."
            )
        
      
        processed_content = preprocess_text(content)
        
        if not processed_content:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível processar o conteúdo do email."
            )
        
    
        classification_start = time.time()
        classification = classify_email_with_groq(processed_content)
        classification_time = time.time() - classification_start
        
      
        classification_reason = generate_classification_reason(processed_content, classification)
        
       
        response_start = time.time()
        suggested_response = generate_response_with_groq(processed_content, classification)
        generation_time = time.time() - response_start
        
        # Prepare response data
        return {
            "classification": classification,
            "classification_reason": classification_reason,
            "suggested_response": suggested_response,
            "analyzed_content": processed_content[:300] + "..." if len(processed_content) > 300 else processed_content,
            "char_count": len(content),
            "classification_time": round(classification_time, 2),
            "generation_time": round(generation_time, 2),
            "model_used": "llama3-8b-8192" if groq_client else "Rule-based fallback"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro interno no endpoint de classificação: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    
    try:
        groq_status = "Connected" if groq_client else "Not configured"
        
        return {
            "status": "OK",
            "message": "Email classifier service is running",
            "ai_provider": "Groq AI",
            "groq_status": groq_status,
            "supported_formats": ["txt", "pdf"],
            "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
            "version": "2.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Service error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

