# main.py
from fasttext_processing import FastTextProcessor
from scibert_processing import SciBERTProcessor
import os
from flask import Flask, redirect, url_for, render_template, request, session,jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

data_path = "./Inspec/docsutf8"


fasttextList = []
fasttext_processor = None
scibert_processor = None


app = Flask(__name__)
app.secret_key = 'your_secret_key' 

client = MongoClient("mongodb://localhost:27017")
db = client['yazlab3']
collection = db['kullanıcı']
collection2 = db ['makale']
fasttext_processor, scibert_processor
fasttext_processor = FastTextProcessor(data_path)
scibert_processor = SciBERTProcessor(data_path)

def initialize_processors():
    print("çalıştı")
    

@app.route("/")
def home_page():
    return render_template("home_page.html")


@app.route('/login', methods=['POST'])
def login():
    email = request.form['mail']
    password = request.form['sifre']
    
    user = collection.find_one({"email": email, "sifre": password})
    if user:
        user_id = str(user['_id'])
        session['user_id'] = user_id
        return redirect(url_for('profile_page'))
    else:
        return "Geçersiz email veya şifre. Lütfen tekrar deneyin."
@app.route('/like_article', methods=['POST'])
def like_article():
    user_id = session.get('user_id')
    article_id = request.form['article_id']
    print("liked_article:", article_id)
    if user_id and article_id:
        collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$addToSet": {
                    "begenilen_makaleler": article_id
                }
            }
        )
        return jsonify(success=True)
    return jsonify(success=False),400
@app.route('/update_recommendations', methods=['GET'])
def update_recommendations():
    user_id = session.get('user_id')
    shown_articles = []
    if user_id:
        user = collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user = collection.find_one({"_id": ObjectId(user_id)})
            shown_articles = user.get('okunmus_makale',[]) 
            liked_article_ids = user.get('begenilen_makaleler', [])
            print ("liked_article_ids:", liked_article_ids)
            print("shown_articles:", shown_articles)
            new_fasttext_recommendations = fasttext_processor.recommend_feedback_articles(liked_article_ids, shown_articles)
            print("new_fasttext_recommendations:", new_fasttext_recommendations)
            new_scibert_recommendations = scibert_processor.recommend_feedback_articles(liked_article_ids, shown_articles)
            print("new_scibert_recommendations:", new_scibert_recommendations)
            okunmusVeriler(display_recommendations(new_fasttext_recommendations))
            okunmusVeriler(display_recommendations(new_scibert_recommendations))
            return render_template('updated_recommendations.html', 
                                   fasttext_recommendations=display_recommendations(new_fasttext_recommendations), 
                                   scibert_recommendations=display_recommendations(new_scibert_recommendations))
        
    return jsonify(success=False),400
def display_recommendations(recommendations):
    """Önerileri gösterir ve kullanıcıya içerikleri okur."""
    arr = []
    for (filename, similarity) in recommendations:
        with open(os.path.join(data_path, filename), 'r', encoding='utf-8') as file:
            content = file.read()
            line = content.split('\n')
            title = line[0]
            content = '\n'.join(line[1:])
            arr.append((filename, content, title, similarity))
    
    return arr

def okunmusVeriler(recommendation):
    user_id = session.get('user_id')
    for filename in recommendation:

        filename = filename[0].replace('.txt', '')
        
        collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$push": {
                            "okunmus_makale": filename
                        }
                    }
                )
        
    

@app.route('/anasayfa/')
def anasayfa():
    shown_articles= []
    user_id = session.get('user_id')
    if user_id:
        user = collection.find_one({"_id": ObjectId(user_id)}, {"ilgi_alanlari": 1})
        if user and 'ilgi_alanlari' in user:
            user_interests = user['ilgi_alanlari']
        user = collection.find_one({"_id": ObjectId(user_id)})
        shown_articles = user.get('okunmus_makale',[]) 
        print("************",shown_articles)
   

   #   user_interests = request.form.getlist('interests')
   #   print("user interests:", user_interests)
   #   session['user_interests'] = user_interests
    

    global fasttext_processor, scibert_processor

    fasttext_recommendations = fasttext_processor.recommend_articles(user_interests,shown_articles)
    scibert_recommendations = scibert_processor.recommend_articles(user_interests,shown_articles)
    
    okunmusVeriler(display_recommendations(fasttext_recommendations))
    okunmusVeriler(display_recommendations(scibert_recommendations))
    return render_template('anasayfa.html', fasttext_recommendations=display_recommendations(fasttext_recommendations), scibert_recommendations=display_recommendations(scibert_recommendations))


@app.route('/signup', methods=['POST'])
def signup():
    ad = request.form['ad']
    soyad = request.form['soyad']
    email = request.form['mail']
    sifre = request.form['sifre']
    if(sifre):
        user_document = {
        "ad": ad,
        "soyad": soyad,
        "email": email,
        "sifre": sifre,
        "telefon": "",
        "dogum": "",
        "hakkında": "",
        "ulke": "",
        "yas": ""
        "okunan_makale"
       
    }

    result = collection.insert_one(user_document)
    return render_template("home_page.html")
   
    
    


@app.route('/profile_page/')
def profile_page():
    user_id = session.get('user_id')
    if user_id:
        user = collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return render_template("profile_page.html", user=user)
    return redirect(url_for('home_page'))




@app.route('/ilgiekle',methods= ['POST'] )
def ilgiekle():
    user_id = session.get('user_id')
    ilgialani = request.form['yeni_ilgi']
    if ilgialani:
        collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$push": {
                            "ilgi_alanlari": ilgialani
                        }
                    }
                )   
    return redirect(url_for('profile_page'))

@app.route('/degistir', methods=['POST'])
def degistir():
    user_id = session.get('user_id')
    if user_id:
        ad = request.form['ad']
        soyad = request.form['soyad']
        email = request.form['email']
        telefon = request.form['telefon']
        dogum = request.form['dogum']
        sifre = request.form['newpass']
        ilgialani = request.form['yeni_ilgi']
        ozet = request.form['about']
        country = request.form['country']
        yas = request.form['age']
        if ilgialani:
            collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$push": {
                            "ilgi_alanlari": ilgialani
                        }
                    }
                )
        if sifre :
            x = request.form['currpass']
            gecicisifre = collection.find_one({"_id": ObjectId(user_id)})  # Corrected this line
            if gecicisifre and gecicisifre['sifre'] == x:
                collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {
                            "ad": ad,
                            "soyad": soyad,
                            "email": email,
                            "telefon": telefon,
                            "dogum": dogum,
                            "sifre": sifre,
                            "hakkında" : ozet,
                            "ulke" : country,
                            "age": yas
                        }
                        
                    }
                )
            else:
                return "YANLIŞ ŞİFRE GİRİLDİ"
        else:
            collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "ad": ad,
                        "soyad": soyad,
                        "email": email,
                        "telefon": telefon,
                        "dogum": dogum,
                        "hakkında" : ozet,
                        "ulke" : country,
                        "age": yas
                    }
                    
                }
            )
        
        return redirect(url_for('profile_page'))
 

        return redirect(url_for('home_page'))
    
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        print("query:",query)
        fasttext_results = fasttext_processor.search_articles(query)
        scibert_results = scibert_processor.search_articles(query)
        return render_template('search_results.html', fasttext_results=display_recommendations(fasttext_results), scibert_results=display_recommendations(scibert_results), query=query)
    return redirect(url_for('anasayfa'))

@app.route('/sil', methods=['POST'])
def sil():
    user_id = session.get('user_id')
    if user_id:
        interest = request.form.get('ilgialani')

       
        collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"ilgi_alanlari": interest}}
        )

        return redirect(url_for('profile_page'))

    return "Oturum bulunamadı.", 401


    

@app.route('/gecmis_okumalar')
def gecmis_okumalar():
    user_id = session.get('user_id')
    makale_dizisi = []
    if user_id:
        user = collection.find_one({"_id": ObjectId(user_id)}, {"okunmus_makale": 1})
        if user and 'okunmus_makale' in user:
            okunmusMakaleler = user['okunmus_makale']

    for i in okunmusMakaleler:
       makale = collection2.find_one({"id":i})
       if makale:
            makale_ozeti = makale.get("ozet", "")
            makale_baslıgı = makale.get("baslik","")  # 'ozet' yoksa boş string kullan
            makale_dizisi.append([str(i), makale_ozeti,makale_baslıgı])
        
            
            

    return render_template("gecmis_okumalar.html",makale = makale_dizisi)


@app.route('/deneme')
def deneme():
    return render_template("deneme.html")
    

if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=5000) 
        
         
    

