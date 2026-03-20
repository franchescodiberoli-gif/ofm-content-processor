import os
import telebot
import random
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, vfx

# --- SEGURIDAD ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)

# Memoria temporal
user_videos = {}

# --- CARPETAS ---
for folder in ['VIDEO', 'US', 'TEMP']:
    os.makedirs(folder, exist_ok=True)

# --- FUNCIÓN DE EDICIÓN ---
def triturar_pro(input_p, output_p, mode="norm"):
    # Cargamos el video asegurando que no se bloquee
    with VideoFileClip(input_p) as clip:
        clip_mirror = clip.fx(vfx.mirror_x)
        clip_final = clip_mirror.rotate(random.choice([-2.5, 2.5]))
        
        if mode == "tk":
            fondo = ColorClip(size=(1080, 1920), color=(0, 102, 204)).set_duration(clip.duration)
            clip_res = clip_final.resize(width=1080).set_position('center')
            clip_final = CompositeVideoClip([fondo, clip_res])

        clip_final.write_videofile(output_p, codec="libx264", audio_codec="aac", temp_audiofile='TEMP/temp-audio.m4a', remove_temp=True)

# --- MANEJADORES ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 ¡Bot Reiniciado! Envíame un video.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_videos[message.chat.id] = message.video.file_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Triturar Normal", callback_data="norm"))
    markup.add(types.InlineKeyboardButton("📱 Formato TikTok", callback_data="tk"))
    bot.send_message(message.chat.id, "✅ Video recibido. Selecciona modo:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Esto confirma a Telegram que el botón fue presionado
    bot.answer_callback_query(call.id, "Iniciando proceso...")
    
    chat_id = call.message.chat.id
    mode = call.data
    
    if chat_id not in user_videos:
        bot.send_message(chat_id, "❌ Error: Reenvía el video.")
        return

    status = bot.send_message(chat_id, f"⏳ Editando en modo {mode}... espera un poco.")

    try:
        file_info = bot.get_file(user_videos[chat_id])
        downloaded = bot.download_file(file_info.file_path)
        
        # Nombres de archivos únicos para evitar choques
        input_path = f"VIDEO/in_{chat_id}.mp4"
        output_path = f"US/out_{chat_id}.mp4"

        with open(input_path, 'wb') as f:
            f.write(downloaded)

        triturar_pro(input_path, output_path, mode=mode)

        with open(output_path, 'rb') as video:
            bot.send_video(chat_id, video, caption="🔥 Triturado con éxito.")
        
        # Limpiar
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        bot.delete_message(chat_id, status.message_id)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error en servidor: {str(e)}")

# --- STREAMLIT ---
st.title("🤖 OFM Processor")
st.write("Servidor encendido.")

# Muy importante: polling sin parar
bot.infinity_polling(timeout=60, long_polling_timeout=30)
