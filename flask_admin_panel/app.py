import base64
import os
from kubernetes import client, config as k8s_config
from kubernetes.config.config_exception import ConfigException
from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, session
import requests
from models import db, User  # models.py içinde User modeli tanımlı olmalı
import logging
from requests.auth import HTTPBasicAuth


# Flask uygulamasını başlatır
app = Flask(__name__)
# Veritabanı yapılandırması

app.config['SQLALCHEMY_DATABASE_URI'] =  os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///admin.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'secretkey_secretkey')

# db ile uygulama arasında bağlantı kurulmasını sağlar
db.init_app(app)

# Uygulama bağlamı içinde veritabanı tablolarını oluştur
with app.app_context():
    db.create_all()

# Anasayfa rotasını tanımlar (giriş formu gösterilir)
@app.route('/')
def home():
    return render_template('login.html')


# Kullanıcıyı veritabanına kaydeden rota
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]

        # Kullanıcı adının veritabanında olup olmadığını kontrol etme
        exist_user = User.query.filter_by(username=username).first()
        if exist_user:
            flash("Bu kullanıcı adı zaten var!", 'error')
        else:
            # Yeni kullanıcıyı veritabanına ekleme
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()

            flash("Kullanıcı başarıyla kaydedildi!", 'success')

    # Kayıttan sonra tüm kullanıcıları tekrar çek
    users = User.query.all()
    return render_template('login.html', users=users)




# Docker Hub'daki en son imaj sürümünü çeken fonksiyon
def get_latest_image_version():
    #docker hubdaki repository name ve kullanıcı adım
    dockerhub_username = "nuraner"
    repository_name = "flask-app"

    # Docker Hub API'si aracılığıyla repository tag'larını alıyoruz
    url = f"https://hub.docker.com/v2/repositories/{dockerhub_username}/{repository_name}/tags/"
    
    # URL'ye GET isteği gönderir ve yanıtı response değişkenine alır.
    response = requests.get(url)

    if response.status_code == 200:     #yanıt kodu --> 200 (başarılı ise)
        data = response.json()      #yanıt verisi JSON formatında alınır.

        #JSON verisinde 'results' anahtarının var olup olmadığı ve uzunluğunun 0'dan büyük olup olmadığı kontrol edilir.
        # "results" JSON verisinde bir key olarak bulunması beklenen bir şeydir.
        if 'results' in data and len(data['results']) > 0:
            tags = [result['name'] for result in data['results']]       #tag isimleri tag listesine eklenir
            latest_tags = tags[:1]  # Son iki tag'ı seçmek için

            # son 2 tagın docker image ismi döndürülür
            return f":{latest_tags}"
    return None


# Kubernetes apı üzerinden  deployment'ın image'ını çekmek için
def get_operator_deployment_image():
    #Kubernetes Apisını çağırma
    try:
        k8s_config.load_incluster_config()
    except ConfigException:
        k8s_config.load_kube_config()
    
    v1 = client.AppsV1Api()

    #operator-deployment adlı deployment'ı "default" namespace'inden çeker:
    deployment= v1.read_namespaced_deployment(name="flask-app-deployment", namespace="default")
   

    """Deployment'ın spec (specification) kısmına gider, ardından template ve spec öğelerine ulaşır 
        ve bu alanda yer alan container listesinin ilk elemanını alır."""
    container_image = deployment.spec.template.spec.containers[0].image
    
    # Image ismini ':' karakterine göre ayırır ve son kısmı (versiyon) döndürür
    if ':' in container_image:
        version = container_image.split(':')[-1]
    else:
        version = 'latest'  # Eğer bir versiyon yoksa 'latest' olarak kabul edilir.

    return version


# Docker Hub'daki en son imaj sürümünü JSON formatında dönen rota
@app.route('/flask-app')
def operator_image():
    operator_image = get_latest_image_version()
    kub_image = get_operator_deployment_image()
    if operator_image and kub_image:
        print(f'{operator_image}')
        print(f'{kub_image}')
        return jsonify({'image': operator_image, 'kub_image': kub_image})
    else:
        return jsonify({'error': 'HATA'})
    


@app.route('/get-configmap/<configmap_name>', methods=['GET'])
def get_configmap(configmap_name):
    v1 = client.CoreV1Api()
    namespace = "default"  # İlgili namespace'i belirt
    try:
        # ConfigMap güncelleme işlemini burada yap
        configmap = v1.read_namespaced_config_map(name=configmap_name, namespace=namespace)
       
         # ConfigMap'i JSON formatına dönüştür ve frontend'e gönder
        return jsonify(configmap.to_dict())
    except client.exceptions.ApiException as e:
        return jsonify({"error": str(e)}), 500


# Flask uygulamasını çalıştırır
if __name__ == '__main__':
    app.run(debug=True)
