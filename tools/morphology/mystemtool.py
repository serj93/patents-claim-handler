from pymystem3 import Mystem
import pprint as pp

# Mystem func agregation
class MystemTool(object):

    # Convert from Mystem 2 UdPipe Feature
    feature_converter = {
        'муж' : ('Masc', 'Gender'),
        'жен' : ('Fem', 'Gender'),
        'сред' : ('Neut', 'Gender'),

        'ед' : ('Sing', 'Number'),
        'мн' : ('Plur', 'Number'),

        'им' : ('Nom', 'Case'),
        'род' : ('Gen', 'Case'),
        'дат' : ('Dat', 'Case'),
        'вин' : ('Acc', 'Case'),
        'местн' : ('Loc', 'Case'),
        'твор' : ('Ins', 'Case'),
        'пр' : ('Loc', 'Case'),
        'парт' : ('Gen', 'Case'),

        'изъяв' : ('Fin', 'VerbForm'),
        'инф' : ('Inf', 'VerbForm'),
        'прич' : ('Part', 'VerbForm'),
        'деепр' : ('Trans', 'VerbForm'),

        'изъяв' : ('Ind', 'Mood'),
        'пов' : ('Imp', 'Mood'),

        'прош' : ('Past', 'Tense'),
        'наст' : ('Pres', 'Tense'),
        'непрош' : ('Fut', 'Tense'),

        'несов' : ('Imp', 'Aspect'),
        'сов' : ('Perf', 'Aspect'),

        'действ' : ('Act', 'Voice'),
        'страд' : ('Pass', 'Voice'),

        '1-л' : ('1', 'Person'),
        '2-л' : ('2', 'Person'),
        '3-л' : ('3', 'Person'),

        'срав' : ('Cmp', 'Degree'),
        'прев' : ('Sup', 'Degree'),

        'од' : ('Anim', 'Animacy'),
        'неод' : ('Inan', 'Animacy'),
    }

    # Singleton
    __instance = None

    def __new__(cls):
        if MystemTool.__instance is None:
            MystemTool.__instance = object.__new__(cls)

            MystemTool.__instance.mystem = Mystem(disambiguation=True)
            MystemTool.__instance.mystem.start()

        return MystemTool.__instance

    # Decorator
    def analyze(self, text):
        return self.mystem.analyze(text)

    # Decorator
    def lemmatize(self, text):
        return self.mystem.lemmatize(text)

    def getMystemPOS(self, item):
        result = None
        if 'analysis' not in item:
            return result

        if len(item['analysis'])==0:
            return result

        try:
            grammar = item['analysis'][0]['gr']
        except:
            print("Error: getMystemPOS.\n")
            pp.pprint(item)
            exit(0)

        if grammar.find(',') > 0:
            grammar = grammar.split(',')[0]
        if grammar.find('=') > 0:
            grammar = grammar.split('=')[0]
        return grammar

    def findWordInMystemData(self, data_mystem, word):
        result = None
        link = None
        for index in range(0,len(data_mystem)):
            item = data_mystem[index]
            if item['text'] == word and 'used' not in item:
                result = item
                item['used'] = True
                link = index
                break
        return result, link

    def convertM2UGrammar(self, fword):
        """
        Get mystem grammar and retrn in UdPipe dict
        WARN: dict for VERBS only!!!
        :param feature:
        :return:
        """
        result = {}
        if 'analysis' not in fword:
            return result

        if len(fword['analysis']) <= 0:
            return result

        feature = fword['analysis'][0]['gr']
        part_gram = feature.split("=")
        feature_set = []
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

                feature_set += norm

        if feature_set:
            for feature in feature_set:
                if feature in self.feature_converter:
                    pair = self.feature_converter[feature]
                    result[pair[1]] = pair[0]

        return result
