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

# --- FUNCIÓN DE TÍTULO TIPO TIKTOK (Recuadro Negro + Texto Blanco) ---
def crear_imagen_texto_pro(texto, ancho_video):
    # Tamaño de fuente grande (Título 1)
    font_size = int(ancho_video * 0.08) 
    img = PIL.Image.new('RGBA', (ancho_video, font_size + 120), (255, 255, 255, 0))
    draw = PIL.ImageDraw.Draw(img)
    
    try:
        font = PIL.ImageFont.load_default() 
    except:
        font = None

    # Coordenadas para el recuadro (Estilo tus capturas)
    text_width = len(texto) * (font_size * 0.5) # Estimación simple
    padding = 30
    
    # Dibujar el fondo negro semitransparente
    r_left = (ancho_video - text_width) // 2 - padding
    r_top = 40
    r_right = (ancho_video + text_width) // 2 + padding
    r_bottom = r_top + font_size + 40
    
    draw.rounded_rectangle([r_left, r_top, r_right, r_bottom], radius=15, fill=(0, 0, 0, 200))

    # Dibujar el texto blanco encima
    draw.text((ancho_video // 2, (r_top + r_bottom) // 2), texto, fill="white", anchor="mm")
    
    temp_path = f"TEMP/tit_{random.randint(1000,9999)}.png"
    img.save(temp_path)
    return temp_path

# --- MOTOR DE EDICIÓN (SIN POS_MAP PARA EVITAR EL ERROR) ---
def procesar_video(input_p, output_p, mode, texto=None, pos=None):
    with VideoFileClip(input_p) as clip:
        # Triturado base: Espejo y rotación sutil
        clip_final = clip.fx(vfx.mirror_x).rotate(random.choice([-2.5, 2.5]))
        
        if mode == "tit" and texto:
            img_path = crear_imagen_texto_pro(texto, clip.w)
            
            # DETERMINAR POSICIÓN DIRECTAMENTE (Resuelve el error local variable)
            if pos == "arriba":
                y_pos = 200
            elif pos == "abajo":
                y_pos = clip.h - 450
            else:
                y_pos = "center"

            txt_overlay = (ImageClip(img_path)
                           .set_duration(clip.duration)
                           .set_position(("center", y_pos)))
            
            clip_final = CompositeVideoClip([clip_final, txt_overlay])

        # Preset 'ultrafast' para evitar el Broken Pipe en Streamlit
        clip_final.write_videofile(output_p, codec="libx264", audio_codec="aac", 
                                   threads=1, preset="ultrafast", logger=None)

# --- MANEJADORES TELEGRAM ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.chat.id] = {'step': None}
    bot.send_message(message.chat.id, "✅ Bot reiniciado y listo. Envíame un video.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_data[message.chat.id] = {'file_id': message.video.file_id, 'step': 'inicio'}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Generar Títulos TikTok (3 Posiciones)", callback_data="tit_pro"))
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
    
    status = bot.send_message(chat_id, "⏳ Procesando tus 3 videos... esto puede tardar un minuto.")
    
    try:
        file_info = bot.get_file(user_data[chat_id]['file_id'])
        down = bot.download_file(file_info.file_path)
        in_p = f"VIDEO/in_{chat_id}.mp4"
        with open(in_p, 'wb') as f: f.write(down)

        # Generar las 3 versiones una por una
        for p in ["arriba", "medio", "abajo"]:
            out_p = f"US/{p}_{chat_id}.mp4"
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

st.title("🤖 OFM Triturador v4.0")
bot.infinity_polling()
