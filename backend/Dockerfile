FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py auth.py memory.py pdf_intake.py rag_engine.py pipeline.yaml metadata.yaml ./

# Run as an unprivileged user; it only needs to write RAGWire's log folder.
RUN useradd --create-home --uid 10001 gymrag \
    && mkdir -p /app/.log \
    && chown -R gymrag:gymrag /app
USER gymrag

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
