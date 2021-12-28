"""Preload spacy and model here, to reuse and speed up the process."""
import spacy


NLP = spacy.load(
    "de_core_news_sm",
    disable=["tok2vec", "tagger", "parser", "ner", "attribute_ruler", "lemmatizer", "morphologizer"]
)
NLP.enable_pipe("senter")
