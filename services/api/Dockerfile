FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --no-deps . && useradd --uid 10001 --create-home notebook && mkdir /data && chown notebook /data
USER notebook
EXPOSE 8010
CMD ["python", "-m", "field_notebook", "--host", "0.0.0.0", "--port", "8010", "--database", "/data/notebook.sqlite3", "--root-path", "/api"]
