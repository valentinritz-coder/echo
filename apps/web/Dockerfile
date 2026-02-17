FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app.py ./

RUN pip install --no-cache-dir .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
