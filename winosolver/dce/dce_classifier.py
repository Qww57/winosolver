import random
import nltk
import time
from winosolver import Serializer
from winosolver.nlptools.Chunker import Chunker, get_main_pos, pre_process_document
from winosolver.nlptools.structure_mining import *


chunker = Chunker()


def features(schema):
    feature_set = {}

    snippet = analyze(schema.snippet)
    main_prop = get_main_prop(schema)
    sentence = analyze(main_prop)

    # Creating a tree structure for the sentence
    full_structure = chunker.parse(schema.sentence)
    main_structure = get_main_pos(full_structure)

    # Main structure of the sentence after chucking: should reflect:
    # X (NP) action (VB) Y (NP) complements (?) link (IN) Z (NP) action (VB) complements (?)
    # TODO as boolean: matches structure or not.
    feature_set['sentence'] = str([tag for (tag, words) in main_structure])

    # Full structure of the snippet
    feature_set['snippet'] = str(snippet.get_tag_sequence())

    # TODO categorize schema_type of verb like action or state
    verb_set = [word.lemma for word in snippet if "V" in word.postag]
    if verb_set:
        feature_set['snippet_verb'] = verb_set[0]
    else:
        feature_set['snippet_verb'] = ""

    # Criteria 2
    str_main_prop = nltk.word_tokenize(main_prop)
    link_set = [w.lemma for w in sentence if (w.postag == "IN" or w.postag == "RB") and w.word == str_main_prop[-1]]
    if link_set:
        feature_set['logical_link'] = link_set[0]
    else:
        feature_set['logical_link'] = ""

    # TODO replace then by schema_type of conjunction (causal, concession, etc)
    # TODO add feature with case of the Y, COI or COD

    return feature_set


class DirectCausalEventClassifier:

    """
    Classifier used in order to classify scheme as Direct Causal Event or not
    """

    classifiers = {
        'naive_bayes' : nltk.NaiveBayesClassifier,
        'decision_tree' : nltk.DecisionTreeClassifier
    }

    def __init__(self, classifier_type, set_length=None):
        """
        Default value of set_length is -1.
        :param classifier_type: schema_type of classifier chosen
        :param set_length: number of schemas used in order to train and test the classifier
        """
        self.accuracy = 0
        self.cm = "not defined"
        self.classifier_type = classifier_type

        debut = time.time()

        # Creation of the feature set
        schemes = parse_xml()
        add_labels(schemes) # Only done on the 160 first ones
        random.shuffle(schemes)

        # Creating the train, dev and test sets: 273 * 0.632 = 172
        length = len(schemes) if set_length is None else set_length
        print(length)
        train_length = int(length * 0.632)  # 172
        dev_length = int(length * 0.77)  # 207
        self.train_schemes = schemes[0:train_length]
        self.dev_schemes = schemes[(train_length + 1):dev_length]
        self.test_schemes = schemes[(dev_length + 1):270]
        self.train_set = [(features(schema), schema.get_type()) for schema in self.train_schemes]
        self.dev_set = [(features(schema), schema.get_type()) for schema in self.dev_schemes]
        self.test_set = [(features(schema), schema.get_type()) for schema in self.test_schemes]
        print("Feature set created - " + str(time.time() - debut))

        # Training the classifier
        self.classifier = self.classifiers[classifier_type].train(self.train_set)
        print("Classifier trained - " + str(time.time() - debut))

        # Testing the classifier accuracy
        self.accuracy = nltk.classify.accuracy(self.classifier, self.test_set)
        print("Accuracy of answers: {} %".format(self.accuracy * 100))

        # Generating the classifier's errors list
        self.errors = []
        for (schema, tag) in self.dev_set:
            guess = self.classifier.classify(features(schema))
            if guess != tag:
                self.errors.append((tag, guess, schema))
        print("Error set created - " + str(time.time() - debut))

    def get_classifier(self):
        return self.classifier

    def get_classifier_type(self):
        return self.classifier_type

    def answer(self, schema):
        return self.classifier.classify(features(schema))

    # Get classifier's accuracy properties

    def get_accuracy(self):
        return self.accuracy * 100

    def information(self, nb):
        return self.classifier.show_most_informative_features(nb)

    def get_errors(self):
        return self.errors

    def create_confusion_matrix(self):
        ref = [schema.get_type() for schema in parse_xml()]
        test = [self.answer(schema) for schema in parse_xml()]
        self.cm = nltk.ConfusionMatrix(ref, test)
        print(self.cm.pretty_format(sort_by_count=True, show_percents=True, truncate=9))

    def get_confusion_matrix(self):
        return self.cm

    # Saving the classifier

    def save_classifier(self, name):
        Serializer.save(self, name)