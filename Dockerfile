FROM python:3.12-alpine
WORKDIR /code
ENV FLASK_APP=src/main.py
ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-w", "4", "src.main:app"]
