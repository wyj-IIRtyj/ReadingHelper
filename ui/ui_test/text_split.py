import spacy

# 先安装: pip install spacy
# 下载模型: python -m spacy download en_core_web_sm

def text_to_lemma(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])

print(text_to_lemma("running runners ran happier fair fairer fairest"))