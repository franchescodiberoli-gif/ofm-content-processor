import os
import telebot
import random
import time
import streamlit as st  # Necesario para leer los Secrets
from telebot import types
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, TextClip, vfx

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Intentamos leer el Token desde los Secrets de Streamlit
try:
    TOKEN = st.secrets["TELEGRAM_TOKEN"]
except Exception:
    # Si lo corres localmente, buscará esta variable, si no, fallará avisándote
    TOKEN = os.getenv('TELEGRAM_TOKEN', 'TU_TOKEN_AQUI')

# --- INICIALIZACIÓN DEL BOT ---
def start_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print("✅ Bot intentando conectar...")
        return bot
    except Exception as e:
        print(f"❌ Error inicial: {e}")
        time.sleep(5)
        return start_bot()

bot = start_bot()

# Crear carpetas de trabajo con permisos
for d in ['TEMP', 'VIDEO', 'US']:
    if not os.path.exists(d):
        os.makedirs(d)

# --- LÓGICA DE EDICIÓN (TRITURADO) ---
def triturar_pro(input_p, output_p, mode="norm"):
    clip = VideoFileClip(input_p)
    
    # Efecto espejo y rotación aleatoria para saltar algoritmos
    clip = clip.fx(vfx.mirror_x)
    clip = clip.rotate(random.choice([-2.5, 2.5]))
    
    if mode == "tk":
        # Formato Vertical 9:16 (Fondo azul para OFM)
        fondo = ColorClip(size=(1080, 1920), color=(0, 102, 204)).set_duration(clip.duration)
        clip_res = clip.resize(width=1080).set_position('center')
        clip = CompositeVideoClip([fondo, clip_res])
    elif mode == "txt":
        # Franja negra con texto personalizado
        franja = ColorClip(size=(clip.w, 180), color=(0,0,0)).set_opacity(0.6).set_position(('center', clip.h * 0.7))
        # Nota: TextClip requiere ImageMagick. Si falla, el bot enviará un error.
        try:
            txt = TextClip("CONTENIDO EXCLUSIVO", fontsize=50, color='white', font='Arial').set_position(('center', clip.h * 0.71))
            clip = CompositeVideoClip([clip, franja.set_duration(clip.duration), txt.set_duration(clip.duration)])
        except:
            clip = CompositeVideoClip([clip, franja.set_duration(clip.duration)])

    clip.write_videofile(output_p, codec="libx264", audio_codec="aac", remove_temp=True, threads=4)
    clip.close()

# --- MANEJADORES DE TELEGRAM ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 ¡Hola Ricardo! Soy el Triturador de la Agencia. Envíame un video para empezar.")

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
    msg_status = bot.send_message(call.message.chat.id, "⏳ Triturando video... Esto puede tardar un minuto.")

    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_path = f"VIDEO/{file_id}.mp4"
        output_path = f"US/edit_{file_id}.mp4"

        with open(input_path, 'wb') as f:
            f.write(downloaded_file)

        triturar_pro(input_path, output_path, mode=mode)

        with open(output_path, 'rb') as video:
            bot.send_video(call.message.chat.id, video, caption="🔥 ¡Video triturado con éxito!")
        
        # Limpieza de archivos para no llenar el servidor
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        bot.delete_message(call.message.chat.id, msg_status.message_id)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Hubo un detalle: {str(e)}")

# --- INTERFAZ MÍNIMA PARA STREAMLIT ---
st.title("🤖 OFM Bot Server")
st.write("El bot está corriendo en segundo plano.")
st.info("No cierres esta pestaña para mantener el bot activo mientras trabajas.")

# --- INICIO DEL POLLING ---
bot.infinity_polling(timeout=20, long_polling_timeout=10)
