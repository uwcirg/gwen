FROM python:3.7

WORKDIR /opt/app

COPY requirements.txt .
RUN pip install --requirement requirements.txt

ENV FLASK_APP=gwen.wsgi:app
COPY . .

EXPOSE 5000

CMD \
    flask bootstrap && \
    gunicorn --bind "0.0.0.0:${P_PORT:-5000}" ${FLASK_APP}
