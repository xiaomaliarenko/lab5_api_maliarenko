FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir flask numpy scipy
COPY app.py .
CMD ["python", "app.py"]
