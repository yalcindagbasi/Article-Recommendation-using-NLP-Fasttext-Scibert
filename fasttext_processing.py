import os
import numpy as np
import fasttext.util
from sklearn.metrics.pairwise import cosine_similarity
from preprocessing import Preprocessor

class FastTextProcessor:
    def __init__(self, data_path):
        self.data_path = data_path
        
        self.preprocessor = Preprocessor()
        fasttext.util.download_model('en', if_exists='ignore')
        self.model = fasttext.load_model('cc.en.300.bin')

    def create_fasttext_vectors(self, texts):
        vectors = []
        for text in texts:
            preprocessed_text = self.preprocessor.preprocess(text)
            word_vectors = [self.model.get_word_vector(word) for word in preprocessed_text.split() if word in self.model.words]
            if word_vectors:
                vector = np.mean(word_vectors, axis=0)
                vectors.append(vector)
        return vectors

    def save_vectors(self, vectors, filename):
        np.save(filename, vectors)

    def load_vectors(self, filename):
        return np.load(filename, allow_pickle=True)

    def create_article_vectors(self, filename='fasttext_vectors.npy'):
        if os.path.exists(filename):
            return self.load_vectors(filename)
        else:
            texts = [open(os.path.join(self.data_path, filename), 'r', encoding='utf-8').read() for filename in os.listdir(self.data_path)]
            vectors = self.create_fasttext_vectors(texts)
            self.save_vectors(vectors, filename)
            return vectors

    def get_articles_by_ID(self, liked_article_ids):
        articles = []
        for article_id in liked_article_ids:
            filename = f"{article_id}.txt"
            if os.path.exists(os.path.join(self.data_path, filename)):
                with open(os.path.join(self.data_path, filename), 'r', encoding='utf-8') as file:
                    articles.append(file.read())
        return articles
    
    def search_articles(self, query, filename='fasttext_vectors.npy'):
        preprocessed_query = self.preprocessor.preprocess(query)
        user_profile_vector = np.mean(self.create_fasttext_vectors([preprocessed_query]), axis=0, keepdims=True)
        article_vectors = self.create_article_vectors(filename)
        similarities = cosine_similarity(user_profile_vector, article_vectors).flatten()
        sorted_indices = np.argsort(similarities)[::-1]
        
        recommendations = []
        i = 0
        while len(recommendations) < 5 and i < len(sorted_indices):
            index = sorted_indices[i]
            filename = os.listdir(self.data_path)[index]
            
            recommendations.append((filename, similarities[index]))
            i += 1
        return recommendations

    def recommend_feedback_articles(self, liked_article_ids, shown_articles, filename='fasttext_vectors.npy'):
        liked_articles = self.get_articles_by_ID(liked_article_ids)
        liked_article_vectors = self.create_fasttext_vectors(liked_articles)
        liked_article_vectors_mean = np.mean(liked_article_vectors, axis=0, keepdims=True)
        article_vectors = self.create_article_vectors(filename)
        similarities = cosine_similarity(liked_article_vectors_mean, article_vectors).flatten()
        sorted_indices = np.argsort(similarities)[::-1]
        
        recommendations = []
        i = 0
        while len(recommendations) < 5 and i < len(sorted_indices):
            index = sorted_indices[i]
            filename = os.listdir(self.data_path)[index]
            if filename.strip(".txt") not in shown_articles:
                recommendations.append((filename, similarities[index]))
            i += 1
                
        return recommendations

    def recommend_articles(self, user_interests, shown_articles, filename='fasttext_vectors.npy'):
        user_profile_vector = np.mean(self.create_fasttext_vectors(user_interests), axis=0, keepdims=True)
        article_vectors = self.create_article_vectors(filename)
        similarities = cosine_similarity(user_profile_vector, article_vectors).flatten()
        sorted_indices = np.argsort(similarities)[::-1]
        
        recommendations = []
        i = 0
        while len(recommendations) < 5 and i < len(sorted_indices):
            index = sorted_indices[i]
            filename = os.listdir(self.data_path)[index]
            if filename.strip(".txt") not in shown_articles:
                recommendations.append((filename, similarities[index]))
            i += 1
                
        return recommendations
