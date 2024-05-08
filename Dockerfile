FROM python:3.11.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  software-properties-common \
  git \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry


RUN git clone --recurse-submodules https://github.com/patentpia-kgt/simple_tools.git .

RUN pip3 install -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/index.py", "--server.port=8501", "--server.address=0.0.0.0"]