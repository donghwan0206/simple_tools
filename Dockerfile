FROM python:3.11.9-slim

WORKDIR /app/

RUN apt-get update && apt-get install -y \
  python3-dev \
  pkg-config \
  default-libmysqlclient-dev \
  build-essential \
  curl \
  software-properties-common \
  git \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry
COPY requirements.txt .
COPY src/app/auto_indexing/requirements.txt ./sub_requirements.txt

RUN pip3 install --no-cache-dir -r /app/sub_requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/index.py", "--server.port=8501", "--server.address=0.0.0.0"]