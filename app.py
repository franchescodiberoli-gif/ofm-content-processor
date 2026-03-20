import os
import telebot
import random
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, vfx
import moviepy.video.io.ffmpeg_writer as ffmpeg_writer

# --- CONFIGURACIÓN ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
user_videos = {}

# Crear carpetas
for folder in ['VIDEO', 'US', 'TEMP']:
    os.makedirs(folder, exist_ok=True)

# --- TRUCO ANTIALIAS (ESTO ARREGLA EL ERROR DE TIKTOK) ---
# Forzamos el uso de LANCZOS en lugar de ANTIALIAS
import PIL
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# --- FUNCIÓN DE EDICIÓN ---
def triturar_pro(input_p, output_p, mode="norm"):
    with VideoFileClip(input_p) as clip:
        clip_mirror = clip.fx(vfx.mirror_x)
        clip_final = clip_mirror.rotate(random.choice([-2.5, 2.5]))
        
        if mode == "tk":
            # Fondo azul de la agencia
            fondo = ColorClip(size=(1080, 1920), color=(0, 102, 204)).set_duration(clip.duration)
            # Redimensionamos asegurando que no de error
            clip_res = clip_final.resize(width=1080)
            clip_res = clip_res.set_position('center')
            clip_final = CompositeVideoClip([fondo, clip_res])

        # Aseguramos la escritura rápida
        clip_final.write_videofile(output_p, codec="libx264", audio_codec="aac", remove_temp=True)

# --- MANEJADORES TELEGRAM ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 ¡Bot Activo Ricardo! Triturado Normal OK. Probando TikTok.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_videos[message.chat.id] = message.video.file_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Triturar Normal", callback_data="norm"))
    markup.add(types.InlineKeyboardButton("📱 Formato TikTok", callback_data="tk"))
    bot.send_message(message.chat.id, "✅ Video recibido. ¿Qué modo aplicamos?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id, "Procesando...")
    chat_id = call.message.chat.id
    mode = call.data
    
    if chat_id not in user_videos:
        bot.send_message(chat_id, "❌ No encontré el video, reenvíalo.")
        return

    status = bot.send_message(chat_id, f"⏳ Editando en modo {mode}... por favor espera.")

    try:
        file_info = bot.get_file(user_videos[chat_id])
        downloaded = bot.download_file(file_info.file_path)
        
        # Archivos únicos por chat para no mezclar videos de modelos
        input_path = f"VIDEO/in_{chat_id}.mp4"
        output_path = f"US/out_{chat_id}.mp4"

        with open(input_path, 'wb') as f:
            f.write(downloaded)

        triturar_pro(input_path, output_path, mode=mode)

        with open(output_path, 'rb') as video:
            bot.send_video(chat_id, video, caption="🔥 ¡Triturado con éxito!")
        
        # Limpieza de servidor
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        bot.delete_message(chat_id, status.message_id)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Detalle técnico en servidor: {str(e)}")

# --- INTERFAZ STREAMLIT ---
st.title("🤖 OFM Bot Server v2.1")
st.write("Estado: En linea.")

bot.infinity_polling(timeout=60, long_polling_timeout=30)
