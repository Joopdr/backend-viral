from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os

app = FastAPI()

# Isso permite que o seu site na Vercel "converse" com este servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Servidor da Agência Viral está ONLINE e pronto para cortar vídeos!"}

@app.post("/gerar-ideia")
async def gerar_ideia(tema: str):
    try:
        # Pega a chave secreta que vamos configurar no Render
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"erro": "Chave API não encontrada no servidor."}
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        prompt = f"Haja como um Diretor de Virais. O tema do vídeo é: {tema}. Me dê 3 ideias de cortes virais para o TikTok com ganchos (primeiros 3 segundos)."
        resposta = model.generate_content(prompt)
        
        return {"sucesso": True, "ideias": resposta.text}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
