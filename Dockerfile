# Imagem base - Python 3.12
FROM python:3.12-slim

# Definir diretório de trabalho
WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configurar localidade para pt_BR.UTF-8
RUN sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    update-locale LANG=pt_BR.UTF-8 LC_ALL=pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]