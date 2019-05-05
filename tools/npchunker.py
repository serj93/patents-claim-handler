# -*- coding: utf-8 -*-
import pprint as pp

import pycrfsuite
import os, subprocess, json, sys

from pymystem3 import Mystem
from tools.appconfig import AppConfig

# Чанкер Именных групп русского языка
class NPChunker(object):

    en_convert_dict = {
        "наст":"praes",
        "непрош":"inpraes",
        "прош":"praet",
        "им":"nom",
        "род":"gen",
        "дат":"dat",
        "вин":"acc",
        "твор":"ins",
        "пр":"abl",
        "парт":"part",
        "местн":"loc",
        "зват":"voc",
        "ед":"sg",
        "мн":"pl",
        "деепр":"ger",
        "инф":"inf",
        "прич":"partcp",
        "изъяв":"indic",
        "пов":"imper",
        "кр":"brev",
        "полн":"plen",
        "притяж":"poss",
        "прев":"supr",
        "срав":"comp",
        "1-л":"1p",
        "2-л":"2p",
        "3-л":"3p",
        "муж":"m",
        "жен":"f",
        "сред":"n",
        "несов":"ipf",
        "сов":"pf",
        "действ":"act",
        "страд":"pass",
        "од":"anim",
        "неод":"inan",
        "пе":"tran",
        "нп":"intr",
        "вводн":"parenth",
        "гео":"geo",
        "затр":"awkw",
        "имя":"persn",
        "искаж":"dist",
        "мж":"mf",
        "обсц":"obsc",
        "отч":"patrn",
        "прдк":"praed",
        "разг":"inform",
        "редк":"rare",
        "сокр":"abbr",
        "устар":"obsol",
        "фам":"famn",
        "A":"A",
        "ADV":"ADV",
        "ADVPRO":"ADVPRO",
        "ANUM":"ANUM",
        "APRO":"APRO",
        "COM":"COM",
        "CONJ":"CONJ",
        "INTJ":"INTJ",
        "NUM":"NUM",
        "PART":"PART",
        "PR":"PR",
        "S":"S",
        "SPRO":"SPRO",
        "V":"V",
        "-":"-",
        "reserved":"reserved",
    }

    def __init__(self):
        self.mystem = None
        # Init model
        self.tagger = pycrfsuite.Tagger()
        self.config = AppConfig()
        self.tagger.open(self.config.CHUNKER_MODEL_PATH)

    def makePrediction(self, text, features, do_braketize = True):
        """
        Takes test data to model and show results
        :param: features: test-data-features (pos-tagas)
        :return: result
        """

        #pp.pprint(features)
        #exit(0)

        labels = self.tagger.tag(features)
        if do_braketize:
            result = self.bracketize(text, labels)
        else:
            result = labels

        #pp.pprint(text)
        #pp.pprint(labels)
        #print('')
        #exit(0)

        return result

    def prepareFeatures(self, data_mystem):
        features_array = []
        text_sentence =[]
        last_token = ''

        #pp.pprint(data_mystem)
        #exit(0);

        index = -1
        data_len = len(data_mystem)

        for data in data_mystem:
            index += 1

            if data["text"] != ' ' and data["text"] != '\n':
                # Drop separator words [WARN: Feature from OUTSIDE - refactor]
                if "analysis" not in data or "mark" in data:
                    # WARN: Experimental design
                    features_array.append("V")
                    '''
                    # + ignore dashes on split
                    if data["text"] == '-':
                        features_array.append("V")
                    else:
                        features_array.append("-")
                    '''
                else:
                    word_info = data["analysis"]
                    if len(word_info) == 0:
                        features_array.append("-")
                    else:
                        word = word_info[0]
                        features_array.append(word["gr"])

                text_sentence.append(data["text"])
        features = []
        for feature in features_array:
            feature = self.normalizeFeatures(feature)
            if feature[0] == 'V':
                feature = feature[0]
            features.append(feature)

        return text_sentence, features

    def normalizeFeatures(self, feature):
        """
        Made a normal grammar tags.without =
        :param feature:
        :return:
        """
        part_gram = feature.split("=")
        norm_grammar = [] # array with all grammar for one word one analysis
        for gram in part_gram:
            if gram != "":
                if gram.find('(')==0:
                    gram = gram.strip('()')
                    if gram.find('|')>=0:
                        gram = gram.split('|')
                        gram = list(filter(None, gram))
                        gram = gram[0]

                if gram.find(",")>0:
                    norm = gram.split(",")
                else:
                    norm = [gram]

                try:
                    norm_new = []
                    for x in norm:
                        if x in self.en_convert_dict:
                            norm_new.append(self.en_convert_dict[x])
                        else:
                            norm_new.append(x)

                    # Old version
                    #norm = [self.en_convert_dict[x] if x in self.en_convert_dict]

                    norm = norm_new
                except:
                    print("Feature error.")
                    pp.pprint(feature)
                    pp.pprint(norm)
                    exit(0)

                norm_grammar+=norm
        return ",".join(norm_grammar)

    def sentenceProcess(self, data_mystem, complete_text):
        """
        Function takes results from mystem for whole text
        :param results: sentences from the text after mystem
        :param complete_text: string for new text
        :return: complete_text: the result - string with brackets.
        """
        " Warning features are not normal!"
        for sentence in data_mystem:
            text_sentence =[]
            features_array = []
            for data in sentence:
                if data["text"] != ' ' and data["text"] != '\n':
                    if "analysis" in data:
                        word_info = data["analysis"]
                        if len(word_info) == 0:
                            features_array.append("-")
                        else:
                            word = word_info[0]
                            features_array.append(word["gr"])
                    else:
                        features_array.append("-")
                    text_sentence.append(data["text"])
            features = []
            for feature in features_array:
                feature = self.normalizeFeatures(feature)
                if feature[0] == 'V':
                    feature = feature[0]
                features.append(feature)

            OK_sentence = self.makePrediction(text_sentence, features)

        return OK_sentence

    def initMystem(self):
        if not self.mystem:
            self.mystem = Mystem(disambiguation=True)
            self.mystem.start()

    def predictOneself(self, text):
        """
        Takes text. Makes normal dots, encodecs and so on.
        Than divides in sentences and gives sentences to mystem and than send to
        functions to process.
        :param text: Text from my django_site
        :return:Complete text with analyse (with NP-brackets)
        """
        self.initMystem()

        data_mystem = []
        sentences = text.split("\n")
        for sentence in sentences:
            data_mystem.append(self.mystem.analyze(text))

        complete_text = ""
        complete_text = self.sentenceProcess(data_mystem, complete_text)

        return complete_text

    def bracketize(self, text, bios):
        """
        Function makes brackets instead BIOs
        If B -> [ : if BI continue; if BO -> ]; if IO -> ]
        :param: text: text
        :param: bios: array with BIO-tags
        :return: text with brackets
        """
        new_text = []
        paar = list(zip(text, bios))

        first_word, first_bio = paar[0]
        '''
        try:
            first_word, first_bio = paar[0]
        except:
            sys.stderr.write("An error occurred when running NPChunker:'bracketize'!")
            pp.pprint(text)
            pp.pprint(bios)
            exit(0)
        '''

        if first_bio == u"I":
            new_text.append(u"[")
        for i in range(0,len(paar)-1):
            word, bio = paar[i]
            post_word, post_bio = paar[i+1]

            if i == 0:
                prev_word = prev_bio = None
            else:
                prev_word, prev_bio = paar[i-1]

            # DEBUGGER
            #print("<" + str(prev_bio) + "> ["+ str(bio) +"] <" + str(post_bio) + ">")

            if bio == u"O":
                    new_text.append(word)
            elif bio == u"B" and post_bio == u"I" and not prev_bio == u"B":
                    new_text.append(u"[")
                    new_text.append(word)
            elif bio == u"B" and post_bio == u"O":
                    if prev_bio != u"B":
                        new_text.append(u"[")
                    new_text.append(word)
                    new_text.append(u"]")
            elif bio == u"B" and post_bio == u"B":
                    new_text.append(u"[")
                    new_text.append(word)
                    #new_text.append(u"]")
            elif bio == u"I" and post_bio == u"O":
                    new_text.append(word)
                    new_text.append(u"]")
            elif bio == u"I" and post_bio == u"B":
                    new_text.append(word)
                    new_text.append(u"]")
            else:
                    new_text.append(word)
        last_word, last_bio = paar[-1]
        if last_bio == u"I":
            new_text.append(last_word)
            new_text.append(u"]")
        elif last_bio == u"B":
            new_text.append(u"[")
            new_text.append(last_word)
            new_text.append(u"]")
        else:
            new_text.append(last_word)

        return u" ".join(new_text), bios
