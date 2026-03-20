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

for folder in ['VIDEO', 'US', 'TEMP']:
    os.makedirs(folder, exist_ok=True)

# --- FUNCIÓN DE TÍTULO ESTILO TIKTOK PREMIUM ---
def crear_imagen_texto_pro(texto, ancho_video):
    font_size = int(ancho_video * 0.10) 
    # Lienzo con espacio para el fondo del texto
    img = PIL.Image.new('RGBA', (ancho_video, font_size + 160), (255, 255, 255, 0))
    draw = PIL.ImageDraw.Draw(img)
    
    # Intentar cargar fuente
    try:
        font = PIL.ImageFont.load_default() 
    except:
        font = None

    # 1. Dibujar el RECUADRO NEGRO (Fondo semitransparente como tus ejemplos)
    padding = 40
    text_width = ancho_video * 0.8 # Estimación
    left = (ancho_video - text_width) // 2
    top = 50
    right = left + text_width
    bottom = top + font_size + 60
    
    # Dibujamos el fondo redondeado o rectangular negro
    draw.rectangle([left - padding, top, right + padding, bottom], fill=(0, 0, 0, 180))

    # 2. Dibujar el TEXTO BLANCO
    draw.text((ancho_video // 2, (top + bottom) // 2), texto, fill="white", anchor="mm")
    
    temp_path = f"TEMP/tit_{random.randint(1000,9999)}.png"
    img.save(temp_path)
    return temp_path

# --- MOTOR DE EDICIÓN ---
def procesar_video(input_p, output_p, mode, texto=None, pos=None):
    with VideoFileClip(input_p) as clip:
        clip_final = clip.fx(vfx.mirror_x).rotate(random.choice([-2.5, 2.5]))
        
        if mode == "tit" and texto:
            img_path = crear_imagen_texto_pro(texto, clip.w)
            # Posiciones seguras según tus capturas
            y_map = {"arriba": 250, "medio": "center", "abajo": clip.h - 500}
            y_final = y_map.get(pos, "center")

            txt_overlay = (ImageClip(img_path)
                           .set_duration(clip.duration)
                           .set_position(("center", y_final)))
            
            clip_final = CompositeVideoClip([clip_final, txt_overlay])

        clip_final.write_videofile(output_p, codec="libx264", audio_codec="aac", 
                                   threads=1, preset="ultrafast", logger=None)

# --- MANEJADORES TELEGRAM (PRIORIDAD AL START) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # LIMPIEZA TOTAL: Esto hace que el bot vuelva a funcionar siempre
    user_data[message.chat.id] = {'step': None}
    bot.send_
