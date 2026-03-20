import os, telebot, random, PIL.Image, PIL.ImageDraw, PIL.ImageFont
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx, ImageClip

TOKEN = "TU_TOKEN_AQUI"
bot = telebot.TeleBot(TOKEN)
user_data = {}

def crear_imagen_texto_pro(texto, ancho_video):
    # FUENTE GIGANTE: 18% del ancho para que sea Título 1 real
    font_size = int(ancho_video * 0.18) 
    img = PIL.Image.new('RGBA', (ancho_video, font_size + 250), (255, 255, 255, 0))
    draw = PIL.ImageDraw.Draw(img)
    
    try:
        # Forzamos una fuente Bold del sistema (DejaVu es estándar en Linux/Cloud)
        font = PIL.ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = PIL.ImageFont.load_default()

    pos_x, pos_y = ancho_video // 2, (font_size + 250) // 2
    txt = texto.upper()

    # CONTORNO NEGRO BRUTAL: 15px para que resalte sí o sí
    for ox in range(-15, 16):
        for oy in range(-15, 16):
            draw.text((pos_x + ox, pos_y + oy), txt, fill="black", font=font, anchor="mm")

    draw.text((pos_x, pos_y), txt, fill="white", font=font, anchor="mm")
    path = f"TEMP/t_{random.randint(1000,9999)}.png"
    img.save(path)
    return path

def procesar(in_p, out_p, txt, pos):
    with VideoFileClip(in_p) as clip:
        clip_b = clip.fx(vfx.mirror_x).rotate(random.choice([-2, 2]))
        img_p = crear_imagen_texto_pro(txt, clip_b.w)
        
        # POSICIONES TIKTOK (Literalmente arriba y abajo)
        y_final = 60 if pos == "arriba" else (clip_b.h - 550 if pos == "abajo" else "center")

        overlay = ImageClip(img_p).set_duration(clip_b.duration).set_position(("center", y_final)).resize(width=clip_base.w * 0.95)
        
        final = CompositeVideoClip([clip_b, overlay])
        final.write_videofile(out_p, codec="libx264", audio_codec="aac", threads=4, preset="ultrafast", logger=None)

@bot.message_handler(commands=['start'])
def st(m):
    user_data[m.chat.id] = {}
    bot.send_message(m.chat.id, "✅ Bot Listo. Manda video.")

@bot.message_handler(content_types=['video'])
def vid(m):
    user_data[m.chat.id] = {'id': m.video.file_id}
    bot.send_message(m.chat.id, "✍️ Escribe el TÍTULO:")

@bot.message_handler(func=lambda m: True)
def run(m):
    if m.text.startswith('/') or m.chat.id not in user_data: return
    t, cid = m.text, m.chat.id
    bot.send_message(cid, "⏳ Procesando 3 versiones...")
    try:
        info = bot.get_file(user_data[cid]['id'])
        f = bot.download_file(info.file_path)
        in_p = f"VIDEO/i_{cid}.mp4"
        with open(in_p, 'wb') as file: file.write(f)

        for p in ["arriba", "medio", "abajo"]:
            out_p = f"US/{p}_{cid}.mp4"
            procesar(in_p, out_p, t, p)
            with open(out_p, 'rb') as v: bot.send_video(cid, v, caption=f"✅ {p.upper()}")
            os.remove(out_p)
        os.remove(in_p)
    except Exception as e: bot.send_message(cid, f"❌ Error: {e}")

bot.infinity_polling()
