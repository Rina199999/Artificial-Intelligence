import pandas as pd
import spacy
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

nlp = spacy.load("ru_core_news_sm")

def preprocess(text):
    doc = nlp(str(text).lower())
    tokens = [t.lemma_ for t in doc if not t.is_stop and not t.is_punct]
    return " ".join(tokens)

data = pd.read_csv("dataset.csv")

print("Чистим датасет...")
data['text'] = data['text'].apply(preprocess)

model_pipeline = Pipeline([
    ('vectorizer', TfidfVectorizer()),
    ('clf', LogisticRegression())
])

print("Обучаем модель...")
model_pipeline.fit(data['text'], data['intent'])

joblib.dump(model_pipeline, "bot_model.joblib")
print("Готово! Модель сохранена в bot_model.joblib")