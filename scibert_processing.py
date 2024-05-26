import os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from preprocessing import Preprocessor

class SciBERTProcessor:
    def __init__(self, data_path):
        self.data_path = data_path
        
        self.preprocessor = Preprocessor()
        self.tokenizer = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased')
        self.model = AutoModel.from_pretrained('allenai/scibert_scivocab_uncased')

    def vectorize(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()

    # Vektörleri dosyaya kaydeder
    def save_vectors(self, vectors, filename):
        print(f"Saving vectors to {filename}")
        np.save(filename, vectors)

    # Vektörleri dosyadan yükler
    def load_vectors(self, filename):
        print(f"Loading vectors from {filename}")
        return np.load(filename, allow_pickle=True)

    # Vektörleri oluşturur
    def create_vectors(self, filename='scibert_vectors.npy'):
        doc_vectors = []
        doc_files = []
        # Vektör dosyası var mı diye bakar
        if os.path.exists(filename):
            print(f"Loading vectors from {filename}")
            doc_vectors = self.load_vectors(filename)
            doc_files = [f for f in os.listdir(self.data_path) if f.endswith(".txt")]
        # Yoksa oluşturur
        else:
            print(f"Could not find vectors in {filename}")
            print(f"Creating vectors from {self.data_path}")
            counter = 0
            count = len(os.listdir(self.data_path))
            for file in os.listdir(self.data_path):
                counter += 1
                if counter % 50 == 0:
                    print(f"Creating progress: {counter} / {count}")
                if file.endswith(".txt"):
                    with open(os.path.join(self.data_path, file), 'r', encoding='utf-8') as f:
                        text = f.read()
                        preprocessed_text = self.preprocessor.preprocess(text)
                        vector = self.vectorize(preprocessed_text)
                        doc_vectors.append(vector)
                        doc_files.append(file)
            self.save_vectors(doc_vectors, filename)
        return np.array(doc_vectors), doc_files

    def get_articlesbyID(self, liked_article_ids):
        articles = []
        for i in liked_article_ids:
            filename = str(i) + ".txt"  
            with open(os.path.join(self.data_path, filename), 'r', encoding='utf-8') as file:
                articles.append(file.read())
        return articles
    def search_articles(self, query, filename='scibert_vectors.npy'):
        print("SciBERT Vectors Started...")
        user_interests_text = ' '.join(query)
        preprocessed_interests = self.preprocessor.preprocess(user_interests_text)
        interest_vector = self.vectorize(preprocessed_interests)

        
        if interest_vector.ndim != 2:
            print(f"interest_vector is {interest_vector.ndim}D. Reshaping to 2D.")
            interest_vector = interest_vector.reshape(1, -1)

        doc_vectors, doc_files = self.create_vectors(filename)

        
        if doc_vectors.ndim == 3:
            print(f"doc_vectors is {doc_vectors.ndim}D. Reshaping to 2D.")
            doc_vectors = np.vstack(doc_vectors)
        similarities = cosine_similarity(interest_vector, doc_vectors).flatten()
        sorted_indices = np.argsort(similarities)[::-1]
        recommendations = []
        i = 0
        while len(recommendations) < 5 and i < len(sorted_indices):
            index = sorted_indices[i]
            filename = doc_files[index]
            
            print("filename", filename)
            recommendations.append((filename, similarities[index]))
            i += 1

        return recommendations
    def recommend_feedback_articles(self, liked_article_ids, shown_articles, filename='scibert_vectors.npy'):
        liked_articles = self.get_articlesbyID(liked_article_ids)
        liked_article_vectors = []
        for liked_article in liked_articles:
            preprocessed_text = self.preprocessor.preprocess(liked_article)
            vector = self.vectorize(preprocessed_text)
            liked_article_vectors.append(vector)

        liked_article_vectors_avg = np.mean(liked_article_vectors, axis=0)

        
        if liked_article_vectors_avg.ndim != 2:
            print(f"liked_article_vectors_avg is {liked_article_vectors_avg.ndim}D. Reshaping to 2D.")
            liked_article_vectors_avg = liked_article_vectors_avg.reshape(1, -1)

        doc_vectors, doc_files = self.create_vectors(filename)

        
        if doc_vectors.ndim == 3:
            print(f"doc_vectors is {doc_vectors.ndim}D. Reshaping to 2D.")
            doc_vectors = np.vstack(doc_vectors)

        similarities = cosine_similarity(liked_article_vectors_avg, doc_vectors).flatten()
        sorted_indices = np.argsort(similarities)[::-1]

        recommendations = []
        i = 0
        while len(recommendations) < 5 and i < len(sorted_indices):
            index = sorted_indices[i]
            filename = doc_files[index]
            if filename.strip(".txt") not in shown_articles:
                print("filename", filename)
                recommendations.append((filename, similarities[index]))
            i += 1

        return recommendations

    def recommend_articles(self, user_interests, shown_articles, filename='scibert_vectors.npy'):
        print("SciBERT Vectors Started...")
        user_interests_text = ' '.join(user_interests)
        preprocessed_interests = self.preprocessor.preprocess(user_interests_text)
        interest_vector = self.vectorize(preprocessed_interests)

        
        if interest_vector.ndim != 2:
            print(f"interest_vector is {interest_vector.ndim}D. Reshaping to 2D.")
            interest_vector = interest_vector.reshape(1, -1)

        doc_vectors, doc_files = self.create_vectors(filename)

        if doc_vectors.ndim == 3:
            print(f"doc_vectors is {doc_vectors.ndim}D. Reshaping to 2D.")
            doc_vectors = np.vstack(doc_vectors)
        similarities = cosine_similarity(interest_vector, doc_vectors).flatten()
        sorted_indices = np.argsort(similarities)[::-1]
        recommendations = []
        i = 0
        while len(recommendations) < 5 and i < len(sorted_indices):
            index = sorted_indices[i]
            filename = doc_files[index]
            if filename.strip(".txt") not in shown_articles:
                print("filename", filename)
                recommendations.append((filename, similarities[index]))
            i += 1

        return recommendations
