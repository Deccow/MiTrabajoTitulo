import nltk
import spacy
import re
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

nltk.download('stopwords')

try:
    nlp_en = spacy.load("en_core_web_sm")
except:
    print("Install English spaCy model with: python -m spacy download en_core_web_sm")
    raise

try:
    nlp_es = spacy.load("es_core_news_sm")
except:
    print("Install Spanish spaCy model with: python -m spacy download es_core_news_sm")
    raise

stopwords_en = set(stopwords.words("english"))
stopwords_es = set(stopwords.words("spanish"))

stemmer_en = SnowballStemmer("english")
stemmer_es = SnowballStemmer("spanish")


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = text.replace("_", " ")  
    return text


def remove_stopwords(tokens, language):
    if language == "EN":
        return [w for w in tokens if w not in stopwords_en]
    elif language == "ES":
        return [w for w in tokens if w not in stopwords_es]
    else:
        raise ValueError("Language must be 'EN' or 'ES'")


def stem_tokens(tokens, language):
    if language == "EN":
        return [stemmer_en.stem(w) for w in tokens]
    elif language == "ES":
        return [stemmer_es.stem(w) for w in tokens]


def lemmatize_text(text, language):
    if language == "EN":
        doc = nlp_en(text)
    elif language == "ES":
        doc = nlp_es(text)
    else:
        raise ValueError("Language must be 'EN' or 'ES'")

    return [token.lemma_ for token in doc]


def preprocess_text(text, language="EN"):

    text = clean_text(text)

    tokens = text.split()

    tokens_no_stop = remove_stopwords(tokens, language)

    lemmas = lemmatize_text(" ".join(tokens_no_stop), language)

    return {
        "tokens": tokens,
        "no_stopwords": tokens_no_stop,
        "lemmatized": lemmas
    }



text_en = "Natural language processing is incredibly interesting and powerful."
text_es = "El procesamiento del lenguaje natural es increíblemente interesante."

print("English example:")
text = preprocess_text(text_en, "EN")
print(" ".join(text["lemmatized"]))


print("\nSpanish example:")
texto = preprocess_text(text_es, "ES")
print(" ".join(texto["lemmatized"]))