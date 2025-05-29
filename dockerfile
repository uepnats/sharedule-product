# 使用するPythonのバージョンを指定
FROM python:3.12

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# requirements.txt を作業ディレクトリにコピーし、依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピーします。
COPY main.py .
COPY config.py .
COPY google_calendar.py .
COPY commands/ ./commands/

# コンテナが起動したときに実行するコマンド
CMD ["python", "main.py"]