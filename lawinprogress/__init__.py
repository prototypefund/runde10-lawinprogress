"""Preload spacy and model here, to reuse and speed up the process."""
import spacy

NLP = spacy.load("de_core_news_sm", exclude=["tok2vec", "tagger", "ner", "parser"])
NLP.enable_pipe("senter")
