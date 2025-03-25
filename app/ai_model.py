import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load the pre-trained BERT model (Change model if needed)
MODEL_NAME = "cardiffnlp/twitter-roberta-base-offensive"  # Example model

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Function to classify text
def classify_text(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predicted_class = torch.argmax(logits).item()

    # Define categories (Modify based on model output labels)
    categories = ["Neutral", "Offensive", "Hate Speech"]
    return categories[predicted_class]
