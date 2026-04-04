import os, telebot, random, base64, io, threading
import PIL.Image
import numpy as np
import streamlit as st
from telebot import types
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip, concatenate_videoclips, vfx
from moviepy.audio.fx.all import volumex
from skimage.filters import gaussian

TOKEN = st.secrets["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
user_data = {}

for folder in ["VIDEO", "US", "TEMP"]:
    os.makedirs(folder, exist_ok=True)

OVERLAY_B64 = """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"""

FFMPEG_PARAMS = [
    "-map_metadata", "-1",
    "-fflags", "+bitexact",
    "-flags:v", "+bitexact",
    "-flags:a", "+bitexact",
]

# ─────────────────────────────────────────────────────
#  TEXTOS BILINGUES
# ─────────────────────────────────────────────────────
TEXTS = {
    "es": {
        "choose_lang":      "🌐 Elige un idioma / Choose a language:",
        "lang_set":         "✅ Idioma: *Español*\n\n📤 Sube tu video para empezar.",
        "video_received":   "✅ *¡Video recibido!* ¿Qué quieres hacer?",
        "no_video":         "❌ Primero sube un video.",
        "processing":       "⏳ Ya hay un video procesándose.",
        "btn_navidad":      "🎄 Plantilla Navidad",
        "btn_cliper":       "✂️ Cliper",
        "btn_cine":         "🎬 Cine",
        "btn_reconfig":     "⚙️ Reconfigurar",
        "btn_hyped":        "hyped⚠️",
        "btn_nuevo":        "📤 Subir nuevo video",
        "menu_final":       "✅ ¿Quieres procesar otro video?",
        "processing_nav":   "⏳ Procesando plantilla navideña...",
        "processing_cine":  "⏳ Procesando efecto cine {}...",
        "processing_gen":   "⏳ Procesando...",
        "processing_hyped": "⏳ Aplicando efecto hyped⚠️...",
        "done_navidad":     "🎄 ¡Listo!",
        "done_cliper":      "✂️ ¡Cliper listo!",
        "done_cine":        "🎬 ¡Listo!",
        "done_reconfig":    "⚙️ Video {}/{}",
        "done_hyped":       "⚠️ ¡Hyped listo!",
        "error":            "❌ Error: {}",
        "video2":           "✅ Video 1 guardado.\n\n📤 Ahora sube el *segundo video*:",
        "cine_type":        "🎬 ¿Qué tipo de barras quieres?",
        "btn_negro":        "⬛ Negro",
        "btn_azul":         "🔵 Azul",
        "btn_borroso":      "🌫️ Borroso",
        "reconfig_intro":   "⚙️ *Vamos a configurar el procesamiento.*\n\nResponde cada pregunta con un número:\n\n",
        "reconfig_saved":   "✅ Configuración guardada. Voy a crear *{}* video(s)...",
        "invalid_number":   "⚠️ Por favor escribe solo un número.",
    },
    "en": {
        "choose_lang":      "🌐 Elige un idioma / Choose a language:",
        "lang_set":         "✅ Language: *English*\n\n📤 Upload your video to get started.",
        "video_received":   "✅ *Video received!* What do you want to do?",
        "no_video":         "❌ Please upload a video first.",
        "processing":       "⏳ A video is already being processed.",
        "btn_navidad":      "🎄 Christmas Template",
        "btn_cliper":       "✂️ Cliper",
        "btn_cine":         "🎬 Cinema",
        "btn_reconfig":     "⚙️ Reconfigure",
        "btn_hyped":        "hyped⚠️",
        "btn_nuevo":        "📤 Upload new video",
        "menu_final":       "✅ Do you want to process another video?",
        "processing_nav":   "⏳ Processing Christmas template...",
        "processing_cine":  "⏳ Processing cinema effect {}...",
        "processing_gen":   "⏳ Processing...",
        "processing_hyped": "⏳ Applying hyped⚠️ effect...",
        "done_navidad":     "🎄 Done!",
        "done_cliper":      "✂️ Cliper ready!",
        "done_cine":        "🎬 Done!",
        "done_reconfig":    "⚙️ Video {}/{}",
        "done_hyped":       "⚠️ Hyped ready!",
        "error":            "❌ Error: {}",
        "video2":           "✅ Video 1 saved.\n\n📤 Now upload the *second video*:",
        "cine_type":        "🎬 What type of bars do you want?",
        "btn_negro":        "⬛ Black",
        "btn_azul":         "🔵 Blue",
        "btn_borroso":      "🌫️ Blurred",
        "reconfig_intro":   "⚙️ *Let's configure the processing.*\n\nAnswer each question with a number:\n\n",
        "reconfig_saved":   "✅ Config saved. Creating *{}* video(s)...",
        "invalid_number":   "⚠️ Please write only a number.",
    }
}

PREGUNTAS = {
    "es": [
        ("doBlurIn",   "1️⃣ ¿Desenfoque al inicio?\n1 = SÍ | 0 = NO"),
        ("doblur",     "2️⃣ ¿Desenfocar todo el video?\n1 = SÍ | 0 = NO"),
        ("doMirror",   "3️⃣ ¿Voltear el video horizontalmente?\n1 = SÍ | 0 = NO"),
        ("doRotate",   "4️⃣ ¿Inclinar el video levemente?\n1 = SÍ | 0 = NO"),
        ("showEffect", "5️⃣ ¿El video aparece suavemente al inicio?\n1 = SÍ | 0 = NO"),
        ("rel",        "6️⃣ Efectos de color aleatorios\n(0 = ninguno, máximo 10):"),
        ("vidc",       "7️⃣ ¿Cuántos videos quieres crear? (1-10):"),
        ("mind",       "8️⃣ ¿Desde qué segundo empieza?\n(0 = desde el inicio):"),
        ("maxd",       "9️⃣ ¿Hasta qué segundo?\n(9999 = hasta el final):"),
    ],
    "en": [
        ("doBlurIn",   "1️⃣ Blur at the beginning?\n1 = YES | 0 = NO"),
        ("doblur",     "2️⃣ Blur the entire video?\n1 = YES | 0 = NO"),
        ("doMirror",   "3️⃣ Flip the video horizontally?\n1 = YES | 0 = NO"),
        ("doRotate",   "4️⃣ Slightly tilt the video?\n1 = YES | 0 = NO"),
        ("showEffect", "5️⃣ Does the video fade in smoothly?\n1 = YES | 0 = NO"),
        ("rel",        "6️⃣ Random color effects\n(0 = none, max 10):"),
        ("vidc",       "7️⃣ How many videos do you want? (1-10):"),
        ("mind",       "8️⃣ Starting from which second?\n(0 = from the beginning):"),
        ("maxd",       "9️⃣ Until which second?\n(9999 = until the end):"),
    ]
}

def t(cid, key):
    """Helper: returns text in the user's chosen language."""
    lang = user_data.get(cid, {}).get("lang", "es")
    return TEXTS[lang][key]

def get_preguntas(cid):
    lang = user_data.get(cid, {}).get("lang", "es")
    return PREGUNTAS[lang]


# ─────────────────────────────────────────────────────
#  PARÁMETROS DE PROCESAMIENTO
# ─────────────────────────────────────────────────────
def get_params():
    return {
        "speed":  random.uniform(1.01, 1.03),
        "fps":    random.uniform(29.97, 30.03),
        "volume": random.uniform(0.97, 1.03),
    }

def get_params_cine():
    return {
        "speed":      random.uniform(1.01, 1.03),
        "fps":        random.uniform(29.97, 30.03),
        "volume":     random.uniform(0.97, 1.03),
        "brightness": random.uniform(0.88, 1.12),
        "zoom":       random.uniform(1.04, 1.08),
        "crop_pct":   random.uniform(0.07, 0.10),
    }

COLOR_FILTERS = [
    "colorbalance=rs=.3", "colorbalance=gs=-0.20", "colorbalance=gs=0.20",
    "colorbalance=bs=-0.30", "colorbalance=bs=0.30", "colorbalance=rm=0.30",
    "colorbalance=rm=-0.30", "colorbalance=gm=-0.25", "colorbalance=bm=-0.25",
    "colorbalance=rh=-0.15", "colorbalance=gh=-0.20", "colorbalance=bh=-0.20"
]
NOISES   = [10, 12, 14, 15]
ANGLES   = [-3, 3]


# ─────────────────────────────────────────────────────
#  PLANTILLA NAVIDEÑA
# ─────────────────────────────────────────────────────
def procesar_video(in_path, out_path):
    p    = get_params()
    clip = VideoFileClip(in_path)
    W, H = clip.w, clip.h

    clip = clip.fx(vfx.mirror_x)
    crop_x = int(W * 0.02)
    crop_y = int(H * 0.02)
    clip = clip.crop(x1=crop_x, y1=crop_y, x2=W - crop_x, y2=H - crop_y)
    clip = clip.resize((W, H))
    clip = clip.fx(vfx.speedx, p["speed"])
    if clip.audio:
        clip = clip.set_audio(clip.audio.fx(volumex, p["volume"]))

    data    = base64.b64decode(OVERLAY_B64)
    img     = PIL.Image.open(io.BytesIO(data)).convert("RGBA")
    if img.size != (W, H):
        img = img.resize((W, H), PIL.Image.LANCZOS)
    tmp_png = f"TEMP/ov_{random.randint(10000,99999)}.png"
    img.save(tmp_png)

    overlay   = ImageClip(tmp_png).set_duration(clip.duration).set_position((0, 0))
    final     = CompositeVideoClip([clip, overlay], size=(W, H))
    tmp_audio = f"TEMP/audio_{random.randint(1000,9999)}.m4a"
    final.write_videofile(out_path, codec="libx264", audio_codec="aac",
                          fps=p["fps"], threads=2, preset="ultrafast",
                          logger=None, temp_audiofile=tmp_audio,
                          ffmpeg_params=FFMPEG_PARAMS)
    clip.close(); final.close()
    if os.path.exists(tmp_png):   os.remove(tmp_png)
    if os.path.exists(tmp_audio): os.remove(tmp_audio)


# ─────────────────────────────────────────────────────
#  CLIPER
# ─────────────────────────────────────────────────────
def procesar_cliper(path1, path2, out_path):
    p = get_params()
    W_final, H_final, H_half = 1080, 1920, 960

    def recortar_centro(path):
        clip = VideoFileClip(path)
        W, H = clip.w, clip.h
        if W != W_final:
            clip = clip.resize(width=W_final)
            W, H = clip.w, clip.h
        y1 = max(0, (H - H_half) // 2)
        return clip.crop(x1=0, y1=y1, x2=W_final, y2=y1 + H_half)

    clip1 = recortar_centro(path1)
    clip2 = recortar_centro(path2)
    dur   = min(clip1.duration, clip2.duration)
    clip1 = clip1.subclip(0, dur)
    clip2 = clip2.subclip(0, dur)
    if clip1.audio:
        clip1 = clip1.set_audio(clip1.audio.fx(volumex, p["volume"]))
    clip1 = clip1.set_position((0, 0))
    clip2 = clip2.set_position((0, H_half))
    final = CompositeVideoClip([clip1, clip2], size=(W_final, H_final))
    tmp_audio = f"TEMP/audio_{random.randint(1000,9999)}.m4a"
    final.write_videofile(out_path, codec="libx264", audio_codec="aac",
                          fps=p["fps"], threads=2, preset="ultrafast",
                          logger=None, temp_audiofile=tmp_audio,
                          ffmpeg_params=FFMPEG_PARAMS)
    clip1.close(); clip2.close(); final.close()
    if os.path.exists(tmp_audio): os.remove(tmp_audio)


# ─────────────────────────────────────────────────────
#  CINE  (tipo: "negro" | "azul" | "borroso")
# ─────────────────────────────────────────────────────
def procesar_cine(in_path, out_path, tipo="negro"):
    p = get_params_cine()
    W_final, H_final = 1080, 1920
    bar_h   = int(H_final * 0.20)
    H_video = H_final - bar_h * 2

    clip = VideoFileClip(in_path)
    W, H = clip.w, clip.h
    clip = clip.fx(vfx.mirror_x)

    zoom  = p["zoom"]
    new_w, new_h = int(W * zoom), int(H * zoom)
    clip  = clip.resize((new_w, new_h))
    cx, cy = new_w // 2, new_h // 2
    clip  = clip.crop(x1=cx - W//2, y1=cy - H//2, x2=cx + W//2, y2=cy + H//2)

    cp = p["crop_pct"]
    clip = clip.crop(x1=int(W*cp), y1=int(H*cp), x2=int(W*(1-cp)), y2=int(H*(1-cp)))
    clip = clip.resize((W_final, H_video))
    clip = clip.fl_image(lambda f: np.clip(f * p["brightness"], 0, 255).astype("uint8"))
    clip = clip.fx(vfx.speedx, p["speed"])
    if clip.audio:
        clip = clip.set_audio(clip.audio.fx(volumex, p["volume"]))

    if tipo == "azul":
        color = [30, 80, 180]
        barra_top = ColorClip(size=(W_final, bar_h), color=color).set_duration(clip.duration)
        barra_bot = ColorClip(size=(W_final, bar_h), color=color).set_duration(clip.duration)

    elif tipo == "borroso":
        from PIL import Image as PilImg, ImageFilter
        frame     = clip.get_frame(clip.duration / 2)
        img_full  = PilImg.fromarray(frame).resize((W_final, H_final))
        img_blur  = img_full.filter(ImageFilter.GaussianBlur(radius=25))
        arr_blur  = np.array(img_blur)

        franja_top = arr_blur[:bar_h, :]
        franja_bot = arr_blur[H_final - bar_h:, :]

        barra_top = ImageClip(franja_top).set_duration(clip.duration)
        barra_bot = ImageClip(franja_bot).set_duration(clip.duration)

    else:  # negro (default)
        barra_top = ColorClip(size=(W_final, bar_h), color=[0,0,0]).set_duration(clip.duration)
        barra_bot = ColorClip(size=(W_final, bar_h), color=[0,0,0]).set_duration(clip.duration)

    barra_top = barra_top.set_position((0, 0))
    clip      = clip.set_position((0, bar_h))
    barra_bot = barra_bot.set_position((0, bar_h + H_video))

    final = CompositeVideoClip([barra_top, clip, barra_bot], size=(W_final, H_final))
    tmp_audio = f"TEMP/audio_{random.randint(1000,9999)}.m4a"
    final.write_videofile(out_path, codec="libx264", audio_codec="aac",
                          fps=p["fps"], threads=2, preset="ultrafast",
                          logger=None, temp_audiofile=tmp_audio,
                          ffmpeg_params=FFMPEG_PARAMS)
    clip.close(); final.close()
    if os.path.exists(tmp_audio): os.remove(tmp_audio)


# ─────────────────────────────────────────────────────
#  RECONFIGURAR
# ─────────────────────────────────────────────────────
def apply_blur(image):
    return gaussian(image.astype(float), sigma=5)

def procesar_reconfigurar(in_path, out_path, cfg):
    clip = VideoFileClip(in_path)

    rmaxd = min(cfg["maxd"], clip.duration)
    if cfg["mind"] < rmaxd:
        clip = clip.subclip(cfg["mind"], rmaxd)

    if cfg["showEffect"]:
        clip = clip.fx(vfx.fadein, duration=2)

    if cfg["doMirror"]:
        clip = clip.fx(vfx.mirror_x)

    if cfg["doblur"]:
        clip = clip.fl_image(apply_blur)

    if cfg["doBlurIn"] and clip.duration > 1:
        smclip = clip.subclip(0, 1).fl_image(apply_blur)
        ogclip = clip.subclip(1, clip.duration)
        clip   = concatenate_videoclips([smclip, ogclip])

    noise_val = random.choice(NOISES)
    def add_noise(frame):
        noise = np.random.randint(-noise_val, noise_val, frame.shape, dtype=np.int16)
        return np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    clip = clip.fl_image(add_noise)

    if cfg["rel"] > 0:
        filters = [random.choice(COLOR_FILTERS) for _ in range(cfg["rel"])]
        addargs = ["-vf", ",".join(filters)]
    else:
        addargs = []

    tmp_audio = f"TEMP/audio_{random.randint(1000,9999)}.m4a"
    clip.write_videofile(
        out_path,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="ultrafast",
        logger=None,
        temp_audiofile=tmp_audio,
        ffmpeg_params=["-map_metadata", "-1"] + addargs
    )
    clip.close()
    if os.path.exists(tmp_audio): os.remove(tmp_audio)


# ─────────────────────────────────────────────────────
#  HYPED ⚠️  — Perturbación adversarial por frame
# ─────────────────────────────────────────────────────
def procesar_hyped(in_path, out_path, epsilon=0.03):
    """
    Aplica una perturbación adversarial aleatoria a cada frame del video.
    epsilon controla la intensidad (0.03 = ±7.65 en escala 0-255).
    El resultado es visualmente casi igual al original pero único digitalmente.
    """
    p    = get_params()
    clip = VideoFileClip(in_path)

    def adversarial_frame(frame):
        img_float   = frame.astype(np.float32) / 255.0
        perturbation = np.random.uniform(-epsilon, epsilon, img_float.shape).astype(np.float32)
        adversarial  = np.clip(img_float + perturbation, 0.0, 1.0)
        return (adversarial * 255).astype(np.uint8)

    clip = clip.fl_image(adversarial_frame)
    clip = clip.fx(vfx.speedx, p["speed"])
    if clip.audio:
        clip = clip.set_audio(clip.audio.fx(volumex, p["volume"]))

    tmp_audio = f"TEMP/audio_{random.randint(1000,9999)}.m4a"
    clip.write_videofile(
        out_path,
        codec="libx264",
        audio_codec="aac",
        fps=p["fps"],
        threads=2,
        preset="ultrafast",
        logger=None,
        temp_audiofile=tmp_audio,
        ffmpeg_params=FFMPEG_PARAMS
    )
    clip.close()
    if os.path.exists(tmp_audio): os.remove(tmp_audio)


# ─────────────────────────────────────────────────────
#  HANDLERS
# ─────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(m):
    user_data[m.chat.id] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
    )
    bot.send_message(m.chat.id, "🌐 Elige un idioma / Choose a language:", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data in ("lang_es", "lang_en"))
def cb_lang(c):
    cid  = c.message.chat.id
    lang = c.data.replace("lang_", "")
    user_data.setdefault(cid, {})["lang"] = lang
    bot.answer_callback_query(c.id)
    bot.send_message(cid, t(cid, "lang_set"), parse_mode="Markdown")


@bot.message_handler(content_types=["video", "document"])
def recibir_video(m):
    cid     = m.chat.id
    # Si el usuario no eligió idioma, asignar español por defecto
    if "lang" not in user_data.get(cid, {}):
        user_data.setdefault(cid, {})["lang"] = "es"

    file_id = m.video.file_id if m.content_type == "video" else m.document.file_id
    estado  = user_data.get(cid, {})

    # Esperando video 2 para cliper
    if estado.get("step") == "cliper_video2":
        user_data[cid]["video2_id"] = file_id
        user_data[cid]["step"]      = None
        status = bot.send_message(cid, t(cid, "processing_gen"))
        threading.Thread(target=_hilo_cliper, args=(cid, status.message_id), daemon=True).start()
        return

    saved_lang = user_data.get(cid, {}).get("lang", "es")
    user_data[cid] = {"video_id": file_id, "procesando": False, "lang": saved_lang}

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(cid, "btn_navidad"),  callback_data="overlay_navidad"))
    markup.add(types.InlineKeyboardButton(t(cid, "btn_cliper"),   callback_data="cliper"))
    markup.add(types.InlineKeyboardButton(t(cid, "btn_cine"),     callback_data="cine"))
    markup.add(types.InlineKeyboardButton(t(cid, "btn_reconfig"), callback_data="reconfigurar"))
    markup.add(types.InlineKeyboardButton(t(cid, "btn_hyped"),    callback_data="hyped"))
    bot.send_message(cid, t(cid, "video_received"),
                     parse_mode="Markdown", reply_markup=markup)


# ── Respuestas de texto (Reconfigurar) ──
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "reconfigurar_pregunta")
def respuesta_reconfigurar(m):
    cid = m.chat.id
    try:
        val = int(m.text.strip())
    except ValueError:
        bot.send_message(cid, t(cid, "invalid_number"))
        return

    cfg  = user_data[cid].setdefault("reconfig", {})
    idx  = user_data[cid].get("pregunta_idx", 0)
    preguntas = get_preguntas(cid)
    key, _ = preguntas[idx]
    cfg[key] = bool(val) if key in ("doMirror","showEffect","doRotate","doblur","doBlurIn") else val

    idx += 1
    user_data[cid]["pregunta_idx"] = idx

    if idx < len(preguntas):
        _, texto = preguntas[idx]
        bot.send_message(cid, texto)
    else:
        user_data[cid]["step"] = None
        cfg  = user_data[cid]["reconfig"]
        vidc = cfg.get("vidc", 1)
        bot.send_message(cid, t(cid, "reconfig_saved").format(vidc), parse_mode="Markdown")
        status = bot.send_message(cid, t(cid, "processing_gen"))
        threading.Thread(target=_hilo_reconfigurar, args=(cid, status.message_id), daemon=True).start()


# ─────────────────────────────────────────────────────
#  HILOS
# ─────────────────────────────────────────────────────

def _hilo_navidad(cid, status_id):
    in_p  = f"VIDEO/in_{cid}.mp4"
    out_p = f"US/navidad_{cid}.mp4"
    try:
        raw = bot.download_file(bot.get_file(user_data[cid]["video_id"]).file_path)
        with open(in_p, "wb") as f: f.write(raw)
        procesar_video(in_p, out_p)
        with open(out_p, "rb") as v:
            bot.send_video(cid, v, caption=t(cid, "done_navidad"), supports_streaming=True)
    except Exception as e:
        bot.send_message(cid, t(cid, "error").format(str(e)))
    finally:
        for p in [in_p, out_p]:
            if os.path.exists(p): os.remove(p)
        try: bot.delete_message(cid, status_id)
        except: pass
        _menu_final(cid)
        user_data[cid]["procesando"] = False


def _hilo_cliper(cid, status_id):
    in1, in2 = f"VIDEO/c1_{cid}.mp4", f"VIDEO/c2_{cid}.mp4"
    out_p    = f"US/cliper_{cid}.mp4"
    try:
        raw1 = bot.download_file(bot.get_file(user_data[cid]["video_id"]).file_path)
        with open(in1, "wb") as f: f.write(raw1)
        raw2 = bot.download_file(bot.get_file(user_data[cid]["video2_id"]).file_path)
        with open(in2, "wb") as f: f.write(raw2)
        procesar_cliper(in1, in2, out_p)
        with open(out_p, "rb") as v:
            bot.send_video(cid, v, caption=t(cid, "done_cliper"), supports_streaming=True)
    except Exception as e:
        bot.send_message(cid, t(cid, "error").format(str(e)))
    finally:
        for p in [in1, in2, out_p]:
            if os.path.exists(p): os.remove(p)
        try: bot.delete_message(cid, status_id)
        except: pass
        _menu_final(cid)
        user_data[cid]["procesando"] = False


def _hilo_cine(cid, status_id, tipo):
    in_p  = f"VIDEO/in_{cid}.mp4"
    out_p = f"US/cine_{cid}.mp4"
    try:
        raw = bot.download_file(bot.get_file(user_data[cid]["video_id"]).file_path)
        with open(in_p, "wb") as f: f.write(raw)
        procesar_cine(in_p, out_p, tipo)
        with open(out_p, "rb") as v:
            bot.send_video(cid, v, caption=t(cid, "done_cine"), supports_streaming=True)
    except Exception as e:
        bot.send_message(cid, t(cid, "error").format(str(e)))
    finally:
        for p in [in_p, out_p]:
            if os.path.exists(p): os.remove(p)
        try: bot.delete_message(cid, status_id)
        except: pass
        _menu_final(cid)
        user_data[cid]["procesando"] = False


def _hilo_reconfigurar(cid, status_id):
    cfg   = user_data[cid]["reconfig"]
    vidc  = cfg.get("vidc", 1)
    in_p  = f"VIDEO/in_{cid}.mp4"
    try:
        raw = bot.download_file(bot.get_file(user_data[cid]["video_id"]).file_path)
        with open(in_p, "wb") as f: f.write(raw)

        for i in range(vidc):
            out_p = f"US/reconfig_{cid}_{i}.mp4"
            procesar_reconfigurar(in_p, out_p, cfg)
            with open(out_p, "rb") as v:
                bot.send_video(cid, v,
                               caption=t(cid, "done_reconfig").format(i+1, vidc),
                               supports_streaming=True)
            if os.path.exists(out_p): os.remove(out_p)

    except Exception as e:
        bot.send_message(cid, t(cid, "error").format(str(e)))
    finally:
        if os.path.exists(in_p): os.remove(in_p)
        try: bot.delete_message(cid, status_id)
        except: pass
        _menu_final(cid)
        user_data[cid]["procesando"] = False


def _hilo_hyped(cid, status_id):
    in_p  = f"VIDEO/in_{cid}.mp4"
    out_p = f"US/hyped_{cid}.mp4"
    try:
        raw = bot.download_file(bot.get_file(user_data[cid]["video_id"]).file_path)
        with open(in_p, "wb") as f: f.write(raw)
        procesar_hyped(in_p, out_p)
        with open(out_p, "rb") as v:
            bot.send_video(cid, v, caption=t(cid, "done_hyped"), supports_streaming=True)
    except Exception as e:
        bot.send_message(cid, t(cid, "error").format(str(e)))
    finally:
        for p in [in_p, out_p]:
            if os.path.exists(p): os.remove(p)
        try: bot.delete_message(cid, status_id)
        except: pass
        _menu_final(cid)
        user_data[cid]["procesando"] = False


def _menu_final(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(cid, "btn_nuevo"), callback_data="nuevo_video"))
    bot.send_message(cid, t(cid, "menu_final"), reply_markup=markup)


# ─────────────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: c.data == "overlay_navidad")
def cb_overlay(c):
    cid = c.message.chat.id
    bot.answer_callback_query(c.id)
    if "video_id" not in user_data.get(cid, {}):
        bot.send_message(cid, t(cid, "no_video")); return
    if user_data[cid].get("procesando"):
        bot.send_message(cid, t(cid, "processing")); return
    user_data[cid]["procesando"] = True
    status = bot.send_message(cid, t(cid, "processing_nav"))
    threading.Thread(target=_hilo_navidad, args=(cid, status.message_id), daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == "cliper")
def cb_cliper(c):
    cid = c.message.chat.id
    bot.answer_callback_query(c.id)
    if "video_id" not in user_data.get(cid, {}):
        bot.send_message(cid, t(cid, "no_video")); return
    user_data[cid]["step"] = "cliper_video2"
    bot.send_message(cid, t(cid, "video2"), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda c: c.data == "cine")
def cb_cine(c):
    cid = c.message.chat.id
    bot.answer_callback_query(c.id)
    if "video_id" not in user_data.get(cid, {}):
        bot.send_message(cid, t(cid, "no_video")); return
    if user_data[cid].get("procesando"):
        bot.send_message(cid, t(cid, "processing")); return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(cid, "btn_negro"),   callback_data="cine_negro"))
    markup.add(types.InlineKeyboardButton(t(cid, "btn_azul"),    callback_data="cine_azul"))
    markup.add(types.InlineKeyboardButton(t(cid, "btn_borroso"), callback_data="cine_borroso"))
    bot.send_message(cid, t(cid, "cine_type"), reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data in ("cine_negro", "cine_azul", "cine_borroso"))
def cb_cine_tipo(c):
    cid  = c.message.chat.id
    tipo = c.data.replace("cine_", "")
    bot.answer_callback_query(c.id)
    if "video_id" not in user_data.get(cid, {}):
        bot.send_message(cid, t(cid, "no_video")); return
    if user_data[cid].get("procesando"):
        bot.send_message(cid, t(cid, "processing")); return

    user_data[cid]["procesando"] = True
    status = bot.send_message(cid, t(cid, "processing_cine").format(tipo))
    threading.Thread(target=_hilo_cine, args=(cid, status.message_id, tipo), daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == "reconfigurar")
def cb_reconfigurar(c):
    cid = c.message.chat.id
    bot.answer_callback_query(c.id)
    if "video_id" not in user_data.get(cid, {}):
        bot.send_message(cid, t(cid, "no_video")); return
    if user_data[cid].get("procesando"):
        bot.send_message(cid, t(cid, "processing")); return

    user_data[cid]["step"]         = "reconfigurar_pregunta"
    user_data[cid]["pregunta_idx"] = 0
    user_data[cid]["reconfig"]     = {}

    preguntas = get_preguntas(cid)
    _, texto = preguntas[0]
    bot.send_message(cid, t(cid, "reconfig_intro") + texto, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda c: c.data == "hyped")
def cb_hyped(c):
    cid = c.message.chat.id
    bot.answer_callback_query(c.id)
    if "video_id" not in user_data.get(cid, {}):
        bot.send_message(cid, t(cid, "no_video")); return
    if user_data[cid].get("procesando"):
        bot.send_message(cid, t(cid, "processing")); return

    user_data[cid]["procesando"] = True
    status = bot.send_message(cid, t(cid, "processing_hyped"))
    threading.Thread(target=_hilo_hyped, args=(cid, status.message_id), daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == "nuevo_video")
def cb_nuevo(c):
    cid = c.message.chat.id
    bot.answer_callback_query(c.id)
    saved_lang = user_data.get(cid, {}).get("lang", "es")
    user_data[cid] = {"lang": saved_lang}
    bot.send_message(cid, "📤 " + ("Envía tu nuevo video:" if saved_lang == "es" else "Upload your new video:"))


st.title("🤖 OFM Pro — Bot activo ✅")
st.caption("El bot está corriendo.")
bot.infinity_polling()
