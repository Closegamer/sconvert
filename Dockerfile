FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libfontconfig1 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import matplotlib; matplotlib.use('Agg'); from matplotlib.mathtext import math_to_image; import io; d=chr(36); b=io.BytesIO(); math_to_image(d+'x'+d, b, dpi=72, format='png')"

COPY app/ ./

EXPOSE 8501

CMD ["streamlit", "run", "Home.py", "--server.address=0.0.0.0", "--server.port=8501"]
