FROM python:3.12
WORKDIR /app
# requirements.txt ve nuranoperator.py dosyalarını Docker build konteynerinin çalışma dizinine (/app) kopyalar.
COPY requirements.txt .


RUN pip install -r requirements.txt
# python --> dilinde yazılmış dosyayı çalıştırmak için
# /app/nuranoperator.py --> çalıştıracak dosya 
COPY . .
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
# Flask uygulamasının çalışacağı portu belirtiyoruz
EXPOSE 5000 

CMD ["flask", "run"]
#CMD ["python", "app.py"]


