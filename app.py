import os, telebot, random, PIL.Image, PIL.ImageDraw, PIL.ImageFont
import streamlit as st
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx, ImageClip

# --- CONFIGURACIÓN ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
user_data = {}

for folder in ['VIDEO', 'US', 'TEMP']:
    os.makedirs(folder, exist_ok=True)

# --- MOTOR DE PROCESAMIENTO ---
def procesar_final(in_path, out_path, texto, posicion):
    with VideoFileClip(in_path) as clip:
        # 1. Efecto Espejo y Rotación (Triturado)
        clip_base = clip.fx(vfx.mirror_x).rotate(random.choice([-2, 2]))
        
        # 2. Crear Imagen de Texto GIGANTE
        ancho_video = clip_base.w
        font_size = int(ancho_video * 0.18) # 18% del ancho (Masivo)
        
        # Lienzo transparente
        img = PIL.Image.new('RGBA', (ancho_video, font_size + 200), (255, 255, 255, 0))
        draw = PIL.ImageDraw.Draw(img)
        
        try:
            # Intentamos cargar una fuente Bold estándar de Linux
            font = PIL.ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = PIL.ImageFont.load_default()

        # Texto en MAYÚSCULAS
        txt_main = str(texto).upper()
        center_x, center_y = ancho_video // 2, (font_size + 200) // 2
        
        # Borde Negro Ultra Grueso (Stroke 15)
        for ox in range(-15, 16):
            for oy in range(-15, 16):
                draw.text((center_x + ox, center_y + oy), txt_main, fill="black", font=font, anchor="mm")
        
        # Texto Blanco
        draw.text((center_x, center_y), txt_main, fill="white", font=font, anchor="mm")
        
        temp_img = f"TEMP/t_{random.randint(1000,9999)}.png"
        img.save(temp_img)

        # 3. Posicionamiento ABSOLUTO (Píxeles reales)
        if posicion == "arriba":
            final_y = 50 # Literalmente pegado arriba
        elif posicion == "abajo":
            final_y = clip_base.h - 500 # Zona segura TikTok
        else:
            final_y = "center"

        txt_clip = (ImageClip(temp_img)
                    .set_duration(clip_base.duration)
                    .set_position(("center", final_y))
                    .resize(width=ancho_video * 0.95))

        # 4. Renderizado
        video_final = CompositeVideoClip([clip_base, txt_clip])
        video_final.write_videofile(out_path, codec="libx264", audio_codec="aac", threads=1, preset="ultrafast", logger=None)
        
        if os.path.exists(temp_img): os.remove(temp_img)

# --- HANDLERS TELEGRAM ---
@bot.message_handler(commands=['start'])
def reset(m):
    user_data[m.chat.id] = {'step': None}
    bot.send_message(m.chat.id, "✅ Bot Reseteado. Envía video.")

@bot.message_handler(content_types=['video'])
def get_vid(m):
    user_data[m.chat.id] = {'id': m.video.file_id, 'step': 'ready'}
    bot.send_message(m.chat.id, "🎥 Video OK. Escribe el TÍTULO ahora:")

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    cid = m.chat.id
    if m.text.startswith('/') or cid not in user_data or user_data[cid].get('id') is None:
        return

    # Evitamos que procese dos veces
    if user_data[cid].get('step') == 'proc': return
    
    texto = m.text
    user_data[cid]['step'] = 'proc'
    status = bot.send_message(cid, f"⏳ Generando 3 versiones para: {texto.upper()}")

    try:
        info = bot.get_file(user_data[cid]['id'])
        down = bot.download_file(info.file_path)
        in_p = f"VIDEO/in_{cid}.mp4"
        with open(in_p, 'wb') as f: f.write(down)

        for p in ["arriba", "medio", "abajo"]:
            out_p = f"US/{p}_{cid}.mp4"
            procesar_final(in_p, out_p, texto, p)
            with open(out_p, 'rb') as v:
                bot.send_video(cid, v, caption=f"📍 POSICIÓN: {p.upper()}")
            if os.path.exists(out_p): os.remove(out_p)
        
        os.remove(in_p)
    except Exception as e:
        bot.send_message(cid, f"❌ Error: {str(e)}")
    finally:
        user_data[cid] = {'step': None}
        bot.delete_message(cid, status.message_id)

st.title("🤖 OFM Pro v4.7")
bot.infinity_polling()
