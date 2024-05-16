FROM python:3.11.9-slim

WORKDIR /app/

RUN apt-get update && apt-get install -y \
  # python3.11 \
  # python3-pip \
  python3-dev \
  pkg-config \
  default-libmysqlclient-dev \
  build-essential \
  curl \
  software-properties-common \
  git \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry
# RUN apt install -y dirmngr gnupg apt-transport-https software-properties-common ca-certificates curl
# RUN curl -fsSL https://www.mongodb.org/static/pgp/server-4.2.asc | apt-key add -
# RUN add-apt-repository 'deb https://repo.mongodb.org/apt/debian buster/mongodb-org/4.2 main'
# RUN apt-get update
# RUN apt-get install -y mongodb-database-tools

# RUN wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-macos-arm64-100.9.4.zip
# RUN curl -o mongodb-database-tools.deb https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian11-arm64-100.9.4.deb
# RUN curl -o mongodb-database-tools.deb https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-arm64-100.9.4.deb
RUN curl -o mongodb-database-tools.deb https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-x86_64-100.9.4.deb

# https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian11-x86_64-100.9.4.deb
# # https://downloads.mongodb.com/compass/mongodb-mongosh_2.2.5_amd64.deb
# # https://fastdl.mongodb.org/tools/db/mongodb-database-tools-rhel90-x86_64-100.9.4.tgz
# # https://fastdl.mongodb.org/tools/db/mongodb-database-tools-macos-arm64-100.9.4.zip
RUN apt install -y ./mongodb-database-tools.deb

COPY requirements.txt .
COPY src/app/auto_indexing/requirements.txt ./sub_requirements.txt

RUN pip3 install --no-cache-dir -r /app/sub_requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/index.py", "--server.port=8501", "--server.address=0.0.0.0"]