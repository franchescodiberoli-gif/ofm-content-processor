FROM python:3.9

# Instalamos herramientas de sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Permisos de ImageMagick
RUN find /etc/ImageMagick* -name "policy.xml" -exec sed -i 's/policy domain="path" rights="none" pattern="@\*"/policy domain="path" rights="read|write" pattern="@\*"/g' {} +

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /app

# Copiamos archivos
COPY --chown=user . /app

# Forzamos la instalación de las librerías
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]