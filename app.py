import os
import telebot
import random
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, vfx, ImageClip
import PIL.Image, PIL.ImageDraw, PIL.ImageFont

# --- CONFIGURACIÓN ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
user_data = {}

# Carpetas de trabajo
for folder in ['VIDEO', 'US', 'TEMP']:
    os.makedirs(folder, exist_ok=True)

# --- FUNCIÓN DE TÍTULO TIPO TIKTOK (Recuadro Negro + Texto Blanco GIGANTE) ---
def crear_imagen_texto_pro(texto, ancho_video):
    # Definimos un tamaño de fuente masivo (Título 1 real)
    font_size = int(ancho_video * 0.12) # 12% del ancho del video
    
    # Creamos un lienzo transparente alto para dar espacio
    img = PIL.Image.new('RGBA', (ancho_video, font_size + 200), (255, 255, 255, 0))
    draw = PIL.ImageDraw.Draw(img)
    
    try:
        font = PIL.ImageFont.load_default() # Para que funcione sin subir .ttf
    except:
        font = None

    # EFECTO TIKTOK: Contorno negro grueso (Stroke)
    pos_x = ancho_video // 2
    pos_y = (font_size + 200) // 2
    stroke = 6 # Grosor del contorno
    
    # Dibujar contorno negro
    for ox in range(-stroke, stroke + 1):
        for oy in range(-stroke, stroke + 1):
            draw.text((pos_x + ox, pos_y + oy), texto, fill="black", anchor="mm")

    # Texto principal en blanco encima (Grosor extra)
    draw.text((pos_x, pos_y), texto, fill="white", anchor="mm")
    
    temp_path = f"TEMP/tit_{random.randint(1000,9999)}.png"
    img.save(temp_path)
    return temp_path

# --- MOTOR DE EDICIÓN ---
def procesar_video(input_p, output_p, mode, texto=None, pos=None):
    with VideoFileClip(input_p) as clip:
        # 1. Triturado base: Espejo y rotación sutil
        clip_base = clip.fx(vfx.mirror_x).rotate(random.choice([-2.5, 2.5]))
        
        # 2. Lógica de Títulos (Ahora se aplica ANTES del fondo TikTok)
        if mode == "tit" and texto:
            img_path = crear_imagen_texto_pro(texto, clip_base.w)
            
            # Recalibración de posiciones seguras para video original (no 9:16)
            y_pos_map = {
                "arriba": 150, 
                "abajo": clip_base.h - 300,
                "medio": "center"
            }
            
            # Buscamos la posición, si no existe, usamos medio por seguridad
            y_final = y_pos_map.get(pos, "center")

            txt_overlay = (ImageClip(img_path)
                           .set_duration(clip_base.duration)
                           .set_position(("center", y_final))
                           .resize(width=clip_base.w * 0.9)) # Aseguramos que el título sea imponente

            clip_final = CompositeVideoClip([clip_base, txt_overlay])
        else:
            clip_final = clip_base

        # Renderizado (threads=1 para no saturar Streamlit)
        clip_final.write_videofile(output_p, codec="libx264", audio_codec="aac", threads=1, preset="ultrafast", logger=None)

# --- MANEJADORES TELEGRAM (Igual que v4.0) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.chat.id] = {'step': None}
    bot.send_message(message.chat.id, "✅ Bot reiniciado y listo. Envíame un video.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_data[message.chat.id] = {'file_id': message.video.file_id, 'step': 'inicio'}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Generar Títulos Título 1 (3 Posiciones)", callback_data="tit_pro"))
    bot.send_message(message.chat.id, "✅ Video recibido. Elige modo:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "tit_pro")
def ask_text(call):
    user_data[call.message.chat.id]['step'] = 'wait_txt'
    bot.send_message(call.message.chat.id, "✍️ Escribe el título que llevará el video:")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'wait_txt')
def start_proc(message):
    if message.text.startswith('/'): return
    
    chat_id = message.chat.id
    texto = message.text
    user_data[chat_id]['step'] = 'proc'
    
    status = bot.send_message(chat_id, "⏳ Generando tus 3 videos... esto puede tardar un minuto.")
    
    try:
        file_info = bot.get_file(user_data[chat_id]['file_id'])
        down = bot.download_file(file_info.file_path)
        in_p = f"VIDEO/in_{chat_id}.mp4"
        with open(in_p, 'wb') as f: f.write(down)

        # Generar las 3 versiones una por una
        for p in ["arriba", "medio", "abajo"]:
            out_p = f"US/{p}_{chat_id}.mp4"
            # Modo 'tit' para que aplique la lógica de títulos
            procesar_video(in_p, out_p, "tit", texto, p)
            with open(out_p, 'rb') as v:
                bot.send_video(chat_id, v, caption=f"✅ Posición: {p}")
            if os.path.exists(out_p): os.remove(out_p)

        os.remove(in_p)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")
    finally:
        user_data[chat_id]['step'] = None
        bot.delete_message(chat_id, status.message_id)

st.title("🤖 OFM Processor v4.1")
bot.infinity_polling()
