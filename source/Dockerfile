FROM python:3.12-slim

# Instalar pandoc
RUN apt update && apt install -y pandoc

# Crear directorio de trabajo
WORKDIR /workspace

# Instalar dependencias opcionales
RUN pip install python-docx markdownify requests

# Mantener contenedor vivo
CMD