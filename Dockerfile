FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY data/raw ./data/raw
EXPOSE 8501
CMD ["streamlit", "run", "src/datajustica/dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
