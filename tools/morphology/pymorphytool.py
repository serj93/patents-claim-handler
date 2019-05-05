import pymorphy2
import pprint as pp

class PymorphyTool(object):

    # ConllU to Pymorphy2 features
    feature_converter = {
        'Nom': 'nomn',
        'Gen': 'gent',
        'Dat': 'datv',
        'Acc': 'accs',
        'Loc': 'loct',
        'Ins': 'ablt',
        'Masc': 'masc',
        'Fem': 'femn',
        'Neut': 'neut',
        'Sing': 'sing',
        'Plur': 'plur',
        'Ptan': 'sing',
        'Coll': 'plur',
    }

    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()

    def analyzeWord(self, word):
        return self.morph.parse(word)[0]

    def inflectWord(self, word, target_case, parent_gnc = None):
        """
        Изменение падежа слова
        :param:word: text word
        :param:target_case: Case in UdPipe Notation!!!
        :result: None (on err) | Word
        """
        result = None
        try:
            target_case = self.feature_converter[target_case]
            p = self.morph.parse(word)[0].inflect({target_case})
            word = p.word

            # Выравнивание по роду и числу
            if parent_gnc:
                # Выравнивание по роду (после преобразования на падеж может не та форма)
                if parent_gnc['Gender']:
                    target_gender = self.feature_converter[parent_gnc['Gender']]
                    if target_gender not in p.tag:
                        p = self.morph.parse(word)[0].inflect({target_gender})
                        word = p.word

                # Выравнивание по числу
                if parent_gnc['Number']:
                    target_number = self.feature_converter[parent_gnc['Number']]
                    if target_number not in p.tag:
                        p = self.morph.parse(word)[0].inflect({target_number})
                        word = p.word

            result = word

        except Exception as e:
            #print(word)
            #print(e)
            #exit(0)
            pass

        return result
