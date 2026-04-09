import os
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split

os.environ['HF_HOME'] = 'D:/huggingface'
os.environ['TRANSFORMERS_CACHE'] = 'D:/huggingface/transformers'
os.environ['TMPDIR'] = 'D:/temp'

SAVE_PATH = "D:/models/intent_model"

df = pd.read_csv("dataset.csv")

label2id = {label: idx for idx, label in enumerate(df['intent'].unique())}
id2label = {idx: label for label, idx in label2id.items()}
df["label"] = df["intent"].map(label2id)

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['text'].tolist(), df['label'].tolist(), test_size=0.2
)

MODEL_NAME = "DeepPavlov/rubert-base-cased"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(label2id)
)

def tokenize_func(texts):
    return tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")

train_encodings = tokenize_func(train_texts)
val_encodings = tokenize_func(val_texts)

class IntentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item
    def __len__(self):
        return len(self.labels)

train_dataset = IntentDataset(train_encodings, train_labels)
val_dataset = IntentDataset(val_encodings, val_labels)

training_args = TrainingArguments(
    output_dir="D:/results",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    report_to="none",
    learning_rate=2e-5,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

print("Начинаем обучение BERT...")
trainer.train()


model.save_pretrained(SAVE_PATH)
tokenizer.save_pretrained(SAVE_PATH)

import json
with open(f"{SAVE_PATH}/label_map.json", "w") as f:
    json.dump(id2label, f)

print(f"Модель сохранена в папку {SAVE_PATH}")