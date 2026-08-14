from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

# Inicialização da aplicação Backend
app = FastAPI(title="Viralize.AI - Video Processing Engine")

# ==========================================
# CONFIGURAÇÃO DE SEGURANÇA E CORS
# Isso permite que o seu site na Vercel envie arquivos pesados sem ser bloqueado.
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção final, trocar "*" pelo link da sua Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretório temporário para salvar os vídeos do usuário
UPLOAD_DIR = "temp_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# ROTAS DO SERVIDOR
# ==========================================

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "system": "Viralize.AI Render Backend",
        "message": "O motor de processamento está ativo e aguardando arquivos."
    }

@app.post("/upload")
async def upload_video(video: UploadFile = File(...)):
    """
    Recebe o arquivo .mp4 do Frontend (Vercel) e salva no servidor Render.
    Aqui é onde o FFmpeg entrará em ação na próxima fase de desenvolvimento.
    """
    try:
        # Caminho onde o arquivo será salvo no servidor
        file_path = os.path.join(UPLOAD_DIR, video.filename)
        
        # Salvando o arquivo físico recebido do usuário
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
            
        # O retorno que fará a barra de 90% pular para 100% de Sucesso no seu painel
        return {
            "status": "success",
            "filename": video.filename,
            "message": "Upload concluído! O vídeo foi recebido pelo motor de processamento.",
            "file_size_bytes": os.path.getsize(file_path)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro interno ao processar o vídeo: {str(e)}"
        }
