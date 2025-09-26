from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from textwrap import dedent
import PyPDF2
import spacy
from spacy.cli import download
import re
import os
import io
import time
from groq import Groq


# ==============================
# Configurações
# ==============================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

ALLOWED_EXTENSIONS = {"txt", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MODEL_NAME = "llama-3.1-8b-instant"

# NLP (carregar ou baixar modelo)
try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    download("pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")

# Cliente Groq
groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_")
    else None
)


app = FastAPI(
    title="Email Classifier AI",
    description="AI-powered email classification and response generation using Groq AI",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==============================
# Modelos Pydantic
# ==============================
class EmailRequest(BaseModel):
    email_content: str


class EmailResponse(BaseModel):
    classification: str
    classification_reason: str
    suggested_response: str
    analyzed_content: str
    char_count: int
    classification_time: float
    generation_time: float
    model_used: str


# ==============================
# Utilitários
# ==============================
def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = "\n".join(
            f"--- Página {i+1} ---\n{page.extract_text() or ''}"
            for i, page in enumerate(reader.pages)
        )
        return text.strip() or "Não foi possível extrair texto do PDF."
    except Exception as e:
        return f"Erro ao processar PDF: {e}"


def preprocess_text(text: str) -> str:
    if not text:
        return ""
    # Limpeza com regex
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(
        r"^(From|To|Subject|Date|Cc|Bcc|Reply-To|Message-ID):.*?\n",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(r"\n--+\n.*$", "", text, flags=re.DOTALL)
    text = re.sub(r"\n(Enviado do meu|Sent from my).*?$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # NLP (stopwords + lematização)
    doc = nlp(text.lower())
    tokens = [t.lemma_ for t in doc if not t.is_stop and t.is_alpha]
    return " ".join(tokens).strip()


# ==============================
# Classificação
# ==============================
def classify_email_with_groq(email_content: str) -> str:
    if not groq_client:
        return classify_email_fallback(email_content)

    system_prompt = dedent("""
        Você é um especialista em classificação de emails corporativos para uma empresa do setor financeiro e também um assistente versátil.

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

Além disso, considere as seguintes categorias adicionais:
1. SUPORTE TÉCNICO → ...
2. FINANCEIRO → ...
3. REUNIÃO/AGENDA → ...
4. INFORMATIVO → ...
5. SOCIAL/PESSOAL → ...
6. SPAM/IRRELEVANTE → ...

Se for um EMAIL, responda apenas com a categoria.
        Se não for um email, responda de forma natural e criativa como uma IA conversacional.
        Exemplo: "bolo de chocolate" → "Que delicioso!

Exemplos:
Email: "Obrigado pela ajuda"
Classificação: IMPRODUTIVO

Email: "Preciso da fatura de agosto"
Classificação: FINANCEIRO
    """)

    user_prompt = f"Classifique o seguinte email:\n\n{email_content}\n\nClassificação:"

    try:
        completion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=10,
            temperature=0.1,
            top_p=0.9,
        )
        classification = completion.choices[0].message.content.strip().upper()
        if "PRODUTIVO" in classification:
            return "PRODUTIVO"
        if "IMPRODUTIVO" in classification:
            return "IMPRODUTIVO"
        return "PRODUTIVO"
    except Exception as e:
        print(f"Erro na classificação com Groq: {e}")
        return classify_email_fallback(email_content)


def classify_email_fallback(email_content: str) -> str:
    text = email_content.lower()

    productive = {
        "problema",
        "erro",
        "urgente",
        "suporte",
        "pedido",
        "dúvida",
        "informação",
        "reunião",
        "projeto",
        "senha",
    }
    unproductive = {
        "feliz",
        "parabéns",
        "aniversário",
        "feriado",
        "obrigado",
        "cumprimento",
        "bom dia",
        "boa tarde",
        "boa noite",
    }

    prod_score = sum(2 if k in text else 0 for k in {"problema", "erro", "urgente", "suporte"}) + \
                 sum(1 for k in productive if k in text)
    unprod_score = sum(1 for k in unproductive if k in text)

    if prod_score >= unprod_score:
        return "PRODUTIVO"
    return "IMPRODUTIVO"


# ==============================
# Respostas automáticas
# ==============================
def generate_classification_reason(classification: str) -> str:
    return (
        "Este email contém solicitações ou questões que requerem ação."
        if classification == "PRODUTIVO"
        else "Este email contém mensagens sociais ou cortesia sem necessidade de ação imediata."
    )


def generate_response_with_groq(email_content: str, classification: str) -> str:
    if not groq_client:
        return generate_response_fallback(classification)

    system_prompt = dedent("""
        Você é um assistente de atendimento ao cliente de uma empresa do setor financeiro.
    """)
    if classification == "PRODUTIVO":
        system_prompt += dedent("""
            Gere uma resposta profissional:
            - Confirme recebimento
            - Indique análise
            - Informe prazo quando adequado
            - Use linguagem cordial e formal
            - Até 4 parágrafos
        """)
    else:
        system_prompt += dedent("""
            Gere uma resposta cordial e breve:
            - Agradeça pela mensagem
            - Retribua sentimento
            - Até 2 parágrafos
        """)

    user_prompt = f"Email:\n{email_content}\n\nResposta:"

    try:
        completion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro na resposta com Groq: {e}")
        return generate_response_fallback(classification)


def generate_response_fallback(classification: str) -> str:
    if classification == "PRODUTIVO":
        return dedent("""
            Prezado(a),

            Obrigado pelo seu email. Nossa equipe técnica irá analisá-lo e retornaremos em até 24h.

            Atenciosamente,
            Equipe de Suporte Técnico
        """).strip()
    return dedent("""
        Prezado(a),

        Muito obrigado pela sua mensagem! Desejamos um excelente dia.

        Atenciosamente,
        Equipe de Atendimento
    """).strip()


# ==============================
# Rotas
# ==============================
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")


@app.post("/api/email/classify")
async def classify_email(
    email_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    start_time = time.time()

    # Entrada
    content = ""
    if file:
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(400, f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB")
        file_bytes = await file.read()
        content = (
            extract_text_from_pdf(file_bytes)
            if file.filename.lower().endswith(".pdf")
            else file_bytes.decode("utf-8", errors="ignore")
        )
    elif email_content:
        content = email_content

    if not content.strip():
        raise HTTPException(400, "Nenhum conteúdo de email fornecido.")

    if len(content) > 50000:
        raise HTTPException(400, "Conteúdo muito longo. Limite: 50.000 caracteres.")

    # Processamento
    processed = preprocess_text(content)
    if not processed:
        raise HTTPException(400, "Não foi possível processar o conteúdo.")

    # Classificação
    t0 = time.time()
    classification = classify_email_with_groq(processed)
    classification_time = time.time() - t0

    # Resposta
    t1 = time.time()
    suggested_response = generate_response_with_groq(processed, classification)
    generation_time = time.time() - t1

    return {
        "classification": classification,
        "classification_reason": generate_classification_reason(classification),
        "suggested_response": suggested_response,
        "analyzed_content": processed[:300] + "..." if len(processed) > 300 else processed,
        "char_count": len(content),
        "classification_time": round(classification_time, 2),
        "generation_time": round(generation_time, 2),
        "model_used": MODEL_NAME if groq_client else "Rule-based fallback",
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "OK",
        "message": "Email classifier service is running",
        "ai_provider": "Groq AI",
        "groq_status": "Connected" if groq_client else "Not configured",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
