import os
import telebot
import random
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

# --- CONFIGURACIÓN ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
user_data = {} # Aquí guardaremos el video y el estado del usuario

# Crear carpetas
for folder in ['VIDEO', 'US']:
    os.makedirs(folder, exist_ok=True)

# --- FUNCIÓN PARA CREAR VIDEOS CON TÍTULOS ---
def crear_video_con_texto(input_p, texto, posicion):
    with VideoFileClip(input_p) as clip:
        # Ajustamos el tamaño del texto según el ancho del video
        fontsize = int(clip.w * 0.08)
        
        # Creamos el clip de texto
        # 'method=caption' hace que el texto se ajuste al ancho
        txt_clip = TextClip(texto, fontsize=fontsize, color='white', 
                            font='Arial-Bold', method='caption', width=clip.w * 0.8)
        
        # Definimos la posición
        pos_map = {
            "arriba": ("center", 50),
            "medio": ("center", "center"),
            "abajo": ("center", clip.h - 150)
        }
        
        txt_clip = txt_clip.set_start(0).set_duration(clip.duration).set_position(pos_map[posicion])
        
        # Combinamos
        result = CompositeVideoClip([clip, txt_clip])
        output_p = f"US/{posicion}_{os.path.basename(input_p)}"
        result.write_videofile(output_p, codec="libx264", audio_codec="aac", logger=None)
        return output_p

# --- MANEJADORES TELEGRAM ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "manda un video para comenzar")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_data[message.chat.id] = {'file_id': message.video.file_id, 'step': 'menu'}
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚙️ Triturar (Normal/TK)", callback_data="triturar"),
        types.InlineKeyboardButton("📝 Añadir Títulos", callback_data="pedir_titulo")
    )
    bot.send_message(message.chat.id, "video recibido. elige el modo:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "pedir_titulo":
        user_data[chat_id]['step'] = 'esperando_texto'
        bot.send_message(chat_id, "✍️ Escribe el título que quieres ponerle al video:")
        bot.answer_callback_query(call.id)
    
    elif call.data == "triturar":
        # Aquí puedes mantener tu lógica anterior de triturado
        bot.send_message(chat_id, "Usa el menú anterior para elegir Normal o TK (proceso en desarrollo)")
        bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'esperando_texto')
def procesar_titulo(message):
    chat_id = message.chat.id
    texto = message.text
    file_id = user_data[chat_id]['file_id']
    
    status = bot.send_message(chat_id, f"⏳ Generando tus 3 videos con el título: '{texto}'...")
    
    try:
        # Descargar video
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        input_path = f"VIDEO/temp_{chat_id}.mp4"
        
        with open(input_path, 'wb') as f:
            f.write(downloaded)
        
        # Generar las 3 versiones
        posiciones = ["arriba", "medio", "abajo"]
        for pos in posiciones:
            path_editado = crear_video_con_texto(input_path, texto, pos)
            with open(path_editado, 'rb') as v:
                bot.send_video(chat_id, v, caption=f"✅ Título {pos}")
            os.remove(path_editado)
            
        os.remove(input_path)
        bot.delete_message(chat_id, status.message_id)
        bot.send_message(chat_id, "✨ ¡Listo! Aquí tienes tus 3 versiones.")
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error al crear títulos: {str(e)}\n(Asegúrate de tener ImageMagick instalado o configurado)")

# --- INTERFAZ ---
st.title("🤖 OFM Processor - Modo Títulos")
bot.infinity_polling()
