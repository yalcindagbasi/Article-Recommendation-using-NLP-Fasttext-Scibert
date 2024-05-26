import os
from bson.objectid import ObjectId
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client['yazlab3']
collection = db['makale']

dizin = "./Inspec/docsutf8"

for dosya_adi in os.listdir(dizin):
    if dosya_adi.endswith(".txt"):
        dosya_yolu = os.path.join(dizin, dosya_adi)
        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            ozet = ""
            baslik = dosya.readline().rstrip()  
            for satir in dosya:  
                ozet += satir.rstrip() + " "
           
            belge_id = ObjectId()
   
            dosya_numarasi = dosya_adi.split(".")[0]
            collection.insert_one({
                "_id": belge_id,
                "id" : dosya_numarasi,
                "baslik": baslik,
                "ozet": ozet
            })
            print(f"{dosya_adi} dosyasının özeti MongoDB'ye eklendi.")