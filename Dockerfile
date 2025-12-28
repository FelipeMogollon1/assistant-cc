# 1. Imagen base oficial de Python (versión estable de 2025)
FROM python:3.12-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar solo el archivo de requerimientos primero (optimiza el caché)
COPY requirements.txt .

# 4. Instalar las dependencias directamente en el sistema del contenedor
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código de tu proyecto
COPY . .

# 6. Comando para iniciar tu aplicación (ajusta según tu archivo principal)
CMD ["python", "app.py"]
