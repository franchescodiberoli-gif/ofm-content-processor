import os
import telebot
import random
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, vfx
import PIL.Image

# --- FIX ANTIALIAS (ESTO ES LO QUE LO QUEBRABA) ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# --- SEGURIDAD ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
user_videos = {}

# Crear carpetas
for folder in ['VIDEO', 'US', 'TEMP']:
    os.makedirs(folder, exist_ok=True)

# --- FUNCIÓN DE EDICIÓN ---
def triturar_pro(input_p, output_p, mode="norm"):
    with VideoFileClip(input_p) as clip:
        # Efectos base
        clip_final = clip.fx(vfx.mirror_x).rotate(random.choice([-2.5, 2.5]))
        
        if mode == "tk":
            # Fondo azul OFM
            fondo = ColorClip(size=(1080, 1920), color=(0, 102, 204)).set_duration(clip.duration)
            clip_res = clip_final.resize(width=1080).set_position('center')
            clip_final = CompositeVideoClip([fondo, clip_res])

        clip_final.write_videofile(output_p, codec="libx264", audio_codec="aac", remove_temp=True)

# --- MANEJADORES ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Bot reiniciado y listo. Envíame un video.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_videos[message.chat.id] = message.video.file_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Triturar Normal", callback_data="norm"))
    markup.add(types.InlineKeyboardButton("📱 Formato TikTok", callback_data="tk"))
    bot.send_message(message.chat.id, "✅ Video recibido. Elige modo:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    if chat_id not in user_videos:
        bot.send_message(chat_id, "❌ Reenvía el video.")
        return

    status = bot.send_message(chat_id, "⏳ Procesando... espera un momento.")
    try:
        file_info = bot.get_file(user_videos[chat_id])
        downloaded = bot.download_file(file_info.file_path)
        in_path, out_path = f"VIDEO/in_{chat_id}.mp4", f"US/out_{chat_id}.mp4"

        with open(in_path, 'wb') as f: f.write(downloaded)
        triturar_pro(in_path, out_path, mode=call.data)

        with open(out_path, 'rb') as v: bot.send_video(chat_id, v, caption="🔥 ¡Listo!")
        
        os.remove(in_path)
        os.remove(out_path)
        bot.delete_message(chat_id, status.message_id)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")

# --- INTERFAZ ---
st.title("🤖 OFM Processor")
bot.infinity_polling(timeout=60)
