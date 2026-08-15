import os
import str
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Importando a Tesoura Mágica
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

app = FastAPI(title="Viralize.AI - Video Processing Engine")

# Permitindo que a Vercel converse com o Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Banco de dados em memória para acompanhar o status da renderização
jobs = {}

@app.get("/health")
def health():
    return {"status": "ok", "message": "Motor de edição online."}

@app.post("/upload")
async def upload_video(video: UploadFile = File(...)):
    """Recebe o arquivo bruto e guarda no servidor."""
    file_id = f"{uuid.uuid4().hex}_{video.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_id)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
        
    return {
        "status": "success",
        "file_id": file_id,
        "message": "Vídeo na base."
    }

def process_video_task(job_id: str, file_id: str, start: float, end: float, top_text: str, bottom_text: str):
    """A Linha de Montagem: Corta, redimensiona e põe legenda."""
    try:
        input_path = os.path.join(UPLOAD_DIR, file_id)
        out_filename = f"edited_{job_id}.mp4"
        out_path = os.path.join(UPLOAD_DIR, out_filename)

        # 1. Carrega o vídeo e faz o corte nos segundos exatos
        clip = VideoFileClip(input_path).subclip(start, end)
        
        # 2. Transforma em formato Vertical (9:16) para TikTok/Reels
        w, h = clip.size
        target_ratio = 9 / 16
        current_ratio = w / h
        
        if current_ratio > target_ratio:
            # Vídeo é mais largo que o ideal, cortamos as laterais
            new_w = h * target_ratio
            clip = clip.crop(x_center=w/2, y_center=h/2, width=new_w, height=h)
        else:
            # Vídeo é mais alto, cortamos cima/baixo
            new_h = w / target_ratio
            clip = clip.crop(x_center=w/2, y_center=h/2, width=w, height=new_h)
            
        # Padroniza para Full HD vertical para manter a qualidade
        clip = clip.resize(height=1920, width=1080)
        final_clip = clip

        # 3. Textos e Memes (Se a máquina aguentar a biblioteca de fontes)
        clips_to_composite = [clip]
        try:
            if top_text:
                # O parâmetro 'method=caption' faz quebra de linha automática
                txt_top = TextClip(top_text, fontsize=70, color='white', stroke_color='black', stroke_width=2, font='Arial-Bold', method='caption', size=(900, None))
                txt_top = txt_top.set_position(('center', 200)).set_duration(clip.duration)
                clips_to_composite.append(txt_top)
                
            if bottom_text:
                txt_bottom = TextClip(bottom_text, fontsize=70, color='white', stroke_color='black', stroke_width=2, font='Arial-Bold', method='caption', size=(900, None))
                txt_bottom = txt_bottom.set_position(('center', 1500)).set_duration(clip.duration)
                clips_to_composite.append(txt_bottom)
                
            if len(clips_to_composite) > 1:
                final_clip = CompositeVideoClip(clips_to_composite)
        except Exception as e:
            print(f"Alerta: Falha ao inserir texto (Falta de ImageMagick no servidor). Processando sem texto. Erro: {e}")
            # Se o ImageMagick não estiver instalado no Render, ele não crasha o sistema, apenas exporta o corte limpo.

        # 4. Renderização Final (Exportar)
        # preset="ultrafast" garante que o servidor gratuito do Render termine antes de estourar a memória
        final_clip.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=30, preset="ultrafast", logger=None)
        
        # Limpando memória cache pesada do MoviePy
        clip.close()
        final_clip.close()
        
        # 5. Avisar o Frontend que a pizza está pronta
        jobs[job_id] = {
            "status": "done",
            "video_url": f"/download/{out_filename}"
        }

    except Exception as e:
        jobs[job_id] = {
            "status": "error",
            "message": f"Erro interno na edição: {str(e)}"
        }

@app.post("/edit")
async def request_edit(
    background_tasks: BackgroundTasks,
    file_id: str = Form(...),
    start: float = Form(...),
    end: float = Form(...),
    top_text: str = Form(""),
    bottom_text: str = Form(""),
    audio_style: str = Form("") # Preparado para o futuro mix de áudio
):
    """Cria a ordem de edição e joga para segundo plano."""
    job_id = uuid.uuid4().hex
    jobs[job_id] = {"status": "processing"}
    
    # Manda a função pesada rodar sem travar a API
    background_tasks.add_task(process_video_task, job_id, file_id, start, end, top_text, bottom_text)
    
    return {"job_id": job_id, "message": "Renderização iniciada em background."}

@app.get("/edit/status/{job_id}")
def check_status(job_id: str):
    """O Frontend fica chamando essa rota de 3 em 3 segundos para ver se terminou."""
    return jobs.get(job_id, {"status": "error", "message": "Trabalho não encontrado."})

@app.get("/download/{filename}")
def download_video(filename: str):
    """Entrega o MP4 físico para o navegador do cliente."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    return {"error": "Arquivo não encontrado."}
