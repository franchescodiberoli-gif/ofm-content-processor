import os
import telebot
import random
import time
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, vfx

# --- SEGURIDAD ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)

# --- CREAR CARPETAS (FUNDAMENTAL) ---
# Esto asegura que el servidor tenga donde guardar los videos
for folder in ['VIDEO', 'US', 'TEMP']:
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

# --- FUNCIÓN DE EDICIÓN ---
def triturar_pro(input_p, output_p, mode="norm"):
    clip = VideoFileClip(input_p)
    clip = clip.fx(vfx.mirror_x)
    clip = clip.rotate(random.choice([-2.5, 2.5]))
    
    if mode == "tk":
        fondo = ColorClip(size=(1080, 1920), color=(0, 102, 204)).set_duration(clip.duration)
        clip_res = clip.resize(width=1080).set_position('center')
        clip = CompositeVideoClip([fondo, clip_res])

    clip.write_videofile(output_p, codec="libx264", audio_codec="aac", remove_temp=True)
    clip.close()

# --- MANEJADORES ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 ¡Listo! Envíame un video y te daré las opciones.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        file_id = message.video.file_id
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("🚀 Triturar Normal", callback_data=f"norm|{file_id}")
        btn2 = types.InlineKeyboardButton("📱 Formato TikTok", callback_data=f"tk|{file_id}")
        markup.add(btn1, btn2)
        
        bot.send_message(message.chat.id, "✅ Video detectado. Elige una opción:", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"❌ Error al procesar: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data.split('|')
    mode, file_id = data[0], data[1]
    
    bot.answer_callback_query(call.id, "Procesando...")
    status = bot.send_message(call.message.chat.id, "⏳ Trabajando en tu video...")

    try:
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        input_path = f"VIDEO/{file_id}.mp4"
        output_path = f"US/edit_{file_id}.mp4"

        with open(input_path, 'wb') as f:
            f.write(downloaded)

        triturar_pro(input_path, output_path, mode=mode)

        with open(output_path, 'rb') as video:
            bot.send_video(call.message.chat.id, video, caption="🔥 Aquí tienes el video editado.")
        
        # Limpieza
        os.remove(input_path)
        os.remove(output_path)
        bot.delete_message(call.message.chat.id, status.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error: {str(e)}")

# --- INTERFAZ STREAMLIT ---
st.title("🤖 Servidor de Agencia OFM")
st.write("Estado: Activo y esperando videos.")

# --- INICIO ---
bot.infinity_polling(timeout=20)
