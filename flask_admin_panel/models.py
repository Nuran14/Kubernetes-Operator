"""SQLAlchemy, Python için bir Object-Relational Mapping (ORM) kütüphanesidir. 
    ORM, veritabanı işlemlerini Python nesneleriyle yönetmemi sağlar."""

from flask_sqlalchemy import SQLAlchemy  

# Flask uygulamamda kullanılacak bir SQLAlchemy nesnesi oluşturur.(db)
# veritabanı etkileşiminde bulunmamı sağlayacak
db = SQLAlchemy()

# user adında bir python sınıfı tanımlıyorum
# User sınıfım db.Model'i miras alır. (db.model SQLAlchemy tarafından sağlanan temel bir sınıf)
# db.Model --> User sınıfınızı bir veritabanı tablosu haline getiriyorum
class User(db.Model):
    # user tablosundaki bir sınıfı temsil ediyorum
    #db.Integer --> türünü belirttim ve primary key olarak belirledim 
    id = db.Column(db.Integer, primary_key=True)
    #aynı şekilde username ve password satırı oluşturdum
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

  
