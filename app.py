import os
import telebot
import random
import time
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, TextClip, vfx

# --- CONFIGURACIÓN ---
TOKEN = '8781615100:AAFJV14w0kkbFSHBSB7ZCVNlupF6amapXzE'

# Intentar conectar con reintentos por si la red del servidor tarda en despertar
def start_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print("Bot intentando conectar...")
        return bot
    except Exception as e:
        print(f"Error inicial: {e}")
        time.sleep(5)
        return start_bot()

bot = start_bot()

# Crear carpetas de trabajo
for d in ['TEMP', 'VIDEO', 'US']:
    if not os.path.exists(d):
        os.makedirs(d)

def triturar_pro(input_p, output_p, mode="norm"):
    clip = VideoFileClip(input_p)
    clip = clip.fx(vfx.mirror_x)
    clip = clip.rotate(random.choice([-2.5, 2.5]))
    
    if mode == "tk":
        fondo = ColorClip(size=(1080, 1920), color=(0, 102, 204)).set_duration(clip.duration)
        clip_res = clip.resize(width=1080).set_position('center')
        clip = CompositeVideoClip([fondo, clip_res])
    elif mode == "txt":
        franja = ColorClip(size=(clip.w, 180), color=(0,0,0)).set_opacity(0.6).set_position(('center', clip.h * 0.7))
        txt = TextClip("CONTENIDO EXCLUSIVO", fontsize=50, color='white', font='Arial').set_position(('center', clip.h * 0.71))
        clip = CompositeVideoClip([clip, franja.set_duration(clip.duration), txt.set_duration(clip.duration)])

    clip.write_videofile(output_p, codec="libx264", audio_codec="aac", remove_temp=True)
    clip.close()

@bot.message_handler(content_types=['video'])
def handle_video(message):
    file_id = message.video.file_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Triturar Normal", callback_data=f"norm|{file_id}"))
    markup.add(types.InlineKeyboardButton("📱 Formato TikTok", callback_data=f"tk|{file_id}"))
    markup.add(types.InlineKeyboardButton("🎬 Franja + Texto", callback_data=f"txt|{file_id}"))
    bot.reply_to(message, "✅ Video recibido. ¿Cómo quieres editarlo?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data.split('|')
    mode, file_id = data[0], data[1]
    bot.answer_callback_query(call.id, "Procesando...")
    msg_status = bot.send_message(call.message.chat.id, "⏳ Editando video...")

    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_path = f"VIDEO/{file_id}.mp4"
        output_path = f"US/edit_{file_id}.mp4"

        with open(input_path, 'wb') as f:
            f.write(downloaded_file)

        triturar_pro(input_path, output_path, mode=mode)

        with open(output_path, 'rb') as video:
            bot.send_video(call.message.chat.id, video, caption="🔥 Listo.")
        
        os.remove(input_path)
        os.remove(output_path)
        bot.delete_message(call.message.chat.id, msg_status.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error: {str(e)}")

bot.infinity_polling(timeout=10, long_polling_timeout=5)