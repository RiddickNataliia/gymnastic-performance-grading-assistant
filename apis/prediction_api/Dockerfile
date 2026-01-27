FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl

RUN rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
	&& python -c "import torch; print('Torch version:', torch.__version__)"

COPY . .

CMD ["fastapi", "run", "app.py"]
