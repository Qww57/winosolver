from winosolver.cknowledge.WikipediaDatabase import WikipediaDatabase
from winosolver.nlptools import Tokenizer
from pymining import itemmining
import unittest

# https://github.com/bartdag/pymining

# Connection to local Wikipedia article data base
database = WikipediaDatabase("WordListDB")


def get_sentences(keywords, type):
    """
    Returns sentences containing keywords from the Wikipedia database.

    :param keywords: set of keywords that should appear in some way in the sentences
    :param type: defines if we want to have all or at least one of the key words
    :return: set of sentences
    """
    sentences = []
    articles = database.get_articles_by_keywords(keywords)
    print(str(len(articles)) + " articles found in the database for " + str(keywords))
    for article in articles:
        tokens = Tokenizer.interesting_sentences(article.content, keywords, type)
        if tokens:
            sentences.extend(tokens)
    print(str(len(list(set(sentences)))) + " sentences found in the database for " + str(keywords))
    return list(set(sentences))


def plural(word):
    # TODO CORRECTLY
    return word + "s"


def get_frequent_related_itemsets(keywords, support):
    # Get sentences
    sentences = get_sentences(keywords, "Exclusive")
    keywords = [word.lower() for word in keywords]
    tokens = [Tokenizer.meaningful_words(sentence) for sentence in sentences]
    relim_input = itemmining.get_relim_input(tuple(tokens))
    report = itemmining.relim(relim_input, min_support=support)
    results = []
    for word in keywords:
        results.extend([itemset for itemset in report if word in itemset or plural(word) in itemset])
    results = list(set(results))
    print(str(len(results)) + " frequent item sets with min support of " + str(support) + " for " + str(keywords))
    return results, sentences


test = get_frequent_related_itemsets(["Dog", "Cat"], 3)
print(" ")
[print(sentence) for sentence in test[1]]
print(" ")
print(test[0])
