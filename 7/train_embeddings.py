import pandas as pd
import spacy
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

nlp = spacy.load("ru_core_news_md")

def get_vector(text):
    return nlp(text).vector

data = pd.read_csv("dataset.csv")

print("Векторизация текстов (это может занять время)...")
X = np.array([get_vector(str(text)) for text in data['text']])
y = data['intent']

print("Обучаем модель на векторах...")
model = LogisticRegression(max_iter=1000)
model.fit(X, y)

joblib.dump(model, "bot_embeddings_model.joblib")
print("Готово! Новая модель сохранена в bot_embeddings_model.joblib")