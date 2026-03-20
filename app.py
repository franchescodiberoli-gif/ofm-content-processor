import os
import telebot
import random
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, vfx

# --- SEGURIDAD ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)

# Diccionario temporal para guardar el video más reciente por usuario
user_videos = {}

# --- CARPETAS ---
for folder in ['VIDEO', 'US', 'TEMP']:
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

    clip.write_videofile(output_p, codec="libx264", audio_codec="aac", remove_temp=True, threads=4)
    clip.close()

# --- MANEJADORES ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 ¡Listo Ricardo! Envíame un video y lo trituramos.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    # Guardamos el ID del video en memoria para este usuario
    user_videos[message.chat.id] = message.video.file_id
    
    markup = types.InlineKeyboardMarkup()
    # Ahora la callback_data es súper corta: solo el modo
    markup.add(types.InlineKeyboardButton("🚀 Triturar Normal", callback_data="norm"))
    markup.add(types.InlineKeyboardButton("📱 Formato TikTok", callback_data="tk"))
    
    bot.send_message(message.chat.id, "✅ Video recibido. ¿Qué modo aplicamos?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    mode = call.data
    chat_id = call.message.chat.id
    
    if chat_id not in user_videos:
        bot.send_message(chat_id, "❌ No encontré el video. Por favor, envíalo de nuevo.")
        return

    file_id = user_videos[chat_id]
    bot.answer_callback_query(call.id, "Procesando...")
    status = bot.send_message(chat_id, "⏳ Iniciando edición... (esto puede tardar)")

    try:
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        input_path = f"VIDEO/{file_id[:10]}.mp4"
        output_path = f"US/edit_{file_id[:10]}.mp4"

        with open(input_path, 'wb') as f:
            f.write(downloaded)

        triturar_pro(input_path, output_path, mode=mode)

        with open(output_path, 'rb') as video:
            bot.send_video(chat_id, video, caption="🔥 Aquí tienes el video triturado.")
        
        os.remove(input_path)
        os.remove(output_path)
        bot.delete_message(chat_id, status.message_id)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Detalle técnico: {str(e)}")

# --- INTERFAZ ---
st.title("🤖 OFM Bot Server")
st.write("Bot activo. No cierres esta pestaña.")

bot.infinity_polling(timeout=20)
