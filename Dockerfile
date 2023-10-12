# 基本イメージをPython 3.9として指定
FROM python:3.9-slim-buster

# 作業ディレクトリを設定
WORKDIR /app

# 必要なライブラリやツールをインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコンテナにコピー
COPY . /app/

# コンテナが起動する際に実行するコマンドを指定
CMD ["python3"]
