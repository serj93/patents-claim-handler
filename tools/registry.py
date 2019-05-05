import pprint as pp

# Реестр словарей для обработки
class DictRegistry(object):

    # MorphoTool, TemplaterHandler: Types of segments, which dropped in handlers
    drop_segments = [
        'SEPARATOR',
        'PURPOSE',
        'NAMED',
    ]

    # MorphoTool: список разделителей (маркировка начала сегментов, отсев сегментов)
    separators = [
        'при этом',
        'а также',
        'a именно',
        'причем',
        'кроме того',
        'наоборот',
    ]

    # MorphoTool: для подтвердения исправления с ADJ (udpipe) на VERB (mystem)
    can_be_verb = [
        'лежать',
    ]

    # Глаголы - синонимы (для обоих словарей); разные леммы;
    verbs_synonyms = {
        'установленный': 'устанавливать',
        'образованный': 'образовывать',
        'согласованный': 'согласовывать',
        'сообщать': 'сообщаться',
        'изолированный': 'изолировать',
        'соединенный': 'соединять',
        'уложенный': 'укладывать',
    }

    # ConvHandler: семантический класс глаголов СОСТАВА конструкций
    # approved = True / False - однозначно определяет элемент конструкций
    composition_verbs = {
        'содержать': {
                'approved': True,
                'obj': [
                    {
                        'before': None,
                        'case': ['Acc', 'Nom'], # - Nom
                    },
                ],
                'add': [
                    {
                        'type': 'ON',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['на'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 0,
                'how': True,
            },
        'оснащать': {
                'approved': True,
                'obj': [
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 0,
                'how': True,
            },
        'включать': {
                'approved': True,
                'obj': [
                    {
                        'before': None,
                        'case': ['Acc', 'Nom'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['между', 'с'],
                        },
                        'case': ['Ins'],
                    },
                    {
                        'before': {
                            'type': 'WORD',
                            'mandatory': True,
                            'tokens': ['в себя'],
                        },
                        'case': ['Acc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': False,
                            'tokens': ['в','во'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'иметь': {
                'approved': True,
                'obj': [
                    {
                        'before': None,
                        'case': ['Acc', 'Nom'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'снабжать': {
                'approved': True,
                'obj': [
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 0,
                'how': True,
            },
        'вводить': {
                'approved': True,
                'reversed': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в','во'],
                        },
                        'case': ['Acc'],
                    },
                    {
                        'before': None,
                        'case': ['Nom'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'состоять': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['из'],
                        },
                        'case': ['Gen'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'изготавливать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['из'],
                        },
                        'case': ['Gen'],
                    },
                    {
                        'before': {
                            'type': 'WORD',
                            'mandatory': True,
                            'tokens': ['в виде'],
                        },
                        'case': ['Gen'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'составлять': {
                'approved': False,
                'obj': [
                    {
                        'before': None,
                        'case': ['Acc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['из'],
                        },
                        'case': ['Gen'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'выполнять': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'WORD',
                            'mandatory': True,
                            'tokens': ['в виде'],
                        },
                        'case': ['Gen', 'Acc'], # +Acc
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'во'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'WORD',
                            'mandatory': True,
                            'tokens': ['на основе'],
                        },
                        'case': ['Acc', 'Nom'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['на'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['из'],
                        },
                        'case': ['Gen', 'Acc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с'],
                        },
                        'case': ['Ins'],
                    },
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'использоваться': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'являться': {
                'approved': False,
                'obj': [
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'служить': {
                'approved': False,
                'obj': [
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'образовывать': {
                'approved': False,
                'obj': [
                    {
                        'before': None,
                        'case': ['Acc', 'Nom', 'Ins'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'добавлять': {
                'approved': False,
                'reversed': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'во'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 2,
                'how': False,
            },
        'помещать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'на'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': None,
                        'case': ['Gen','Acc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'укладывать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'на'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
    }

    connection_verbs = {
        'устанавливать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['на'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['сверху'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в'],
                            'except' : ['виде'],
                        },
                        'case': ['Loc', 'Acc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'укладывать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['на'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['сверху'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в'],
                        },
                        'case': ['Loc', 'Acc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'подключать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['к','ко'],
                        },
                        'case': ['Dat'],
                    },
                ],
                'add': [
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'подтягивать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['к','ко'],
                        },
                        'case': ['Dat'],
                    },
                ],
                'add': [
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'соединять': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с','со'],
                        },
                        'case': ['Ins'],
                    },
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                    {
                        'before': None,
                        'case': ['Nom', 'Acc'],     # +Acc
                    },
                ],
                'add': [
                    #{
                    #    'type': 'WHOM',
                    #    'before': None,
                    #    'case': ['Acc'],
                    #},
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'взаимодействовать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с','со'],
                        },
                        'case': ['Ins'],
                    },
                ],
                'add': [
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'скреплять': {
                'approved': False,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с','со'],
                        },
                        'case': ['Ins'],
                    },
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'add': [
                    {
                        'type': 'WHOM',
                        'before': None,
                        'case': ['Acc'],
                    },
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 0,
                'how': True,
            },
        'крепиться': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['к','ко'],
                        },
                        'case': ['Loc', 'Dat'],
                    },
                ],
                'add': [
                    {
                        'type': 'WHOM',
                        'before': None,
                        'case': ['Acc'],
                    },
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                    {
                        'type': 'BY',
                        'before': {
                            'type': 'WORD',
                            'mandatory': True,
                            'tokens': ['с помощью'],
                        },
                        'case': ['Gen'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'согласовывать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с','со'],
                        },
                        'case': ['Ins'],
                    },
                ],
                'add': [
                    {
                        'type': 'WHOM',
                        'before': None,
                        'case': ['Acc'],
                    },
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'закреплять': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'на'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'пересекаться': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'на'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'связанный': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с','со'],
                        },
                        'case': ['Ins'],
                    },
                ],
                'add': [
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Acc', 'Nom'],
                    },
                    {
                        'type': 'BY',
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'шунтировать': {
                'approved': False,
                'obj': [
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'находиться': {
                'approved': False,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['на'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'надевать': {
                'approved': False,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['на'],
                        },
                        'case': ['Loc', 'Acc'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'размещать': {
                'approved': False,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'на', 'у'],
                        },
                        'case': ['Loc'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'располагать': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'WORD',
                            'mandatory': True,
                            'tokens': ['внутри'],
                        },
                        'case': ['Gen', 'Acc'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['между'],
                        },
                        'case': ['Ins'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['по'],
                        },
                        'case': ['Dat'],
                    },
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в'],
                        },
                        'case': ['Loc'],
                    },
                    {
                        'before': {
                            'type': 'WORD',
                            'mandatory': True,
                            'tokens': ['в контакте с'],
                        },
                        'case': ['Ins'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
        'сообщаться': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с','со'],
                        },
                        'case': ['Ins'],
                    },
                ],
                'add': [
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                    {
                        'type': 'WHOM',
                        'before': None,
                        'case': ['Acc'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'сопряженный': {
                'approved': True,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['с','со'],
                        },
                        'case': ['Ins'],
                    },
                ],
                'add': [
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['через'],
                        },
                        'case': ['Nom', 'Acc'],
                    },
                    {
                        'type': 'WHOM',
                        'before': None,
                        'case': ['Acc'],
                    },
                ],
                'entry': 1,
                'how': False,
            },
        'открывать': {
                'approved': False,
                'obj': [
                    {
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['в', 'во'],
                        },
                        'case': ['Acc'],
                    },
                ],
                'entry': 0,
                'how': False,
            },
        'изолировать': {
                'approved': False,
                'obj': [
                    {
                        'before': None,
                        'case': ['Ins'],
                    },
                ],
                'add': [
                    {
                        'type': 'VIA',
                        'before': {
                            'type': 'ADP',
                            'mandatory': True,
                            'tokens': ['от'],
                        },
                        'case': ['Gen'],
                    },
                ],
                'entry': 1,
                'how': True,
            },
    }

    # Стандартная точка разрыва маркировки
    break_pos = ['ADV', 'SCONJ']
    # Перечник вешек для маркировки
    label_points = {
        'np_sbj_roots': ['N-SBJ','A-SBJ'],
        'np_obj_roots': ['N-OBJ'],
        'np_roots': ['N-SBJ','A-SBJ','N-OBJ','N-ON','N-VIA','N-BY','N-WHOM'],
        'np_obj': ['P-OBJ','N-OBJ', 'I-OBJ'],
        'np_sbj': ['P-SBJ','N-SBJ', 'I-SBJ', 'A-SBJ'],
        'np_add': ['P-ON','P-VIA','N-ON','N-VIA','N-BY','N-WHOM'],
    }

    univers_preps = {
        'со': 'с',
        'ко': 'к',
        'во': 'в',
        'надо': 'над',
        'изо': 'из',
        'об': 'о',
        'обо': 'об',
        'ото': 'от',
    }

    # Singleton
    __instance = None

    def __new__(cls):
        if DictRegistry.__instance is None:
            DictRegistry.__instance = object.__new__(cls)

            # Future: заполнение словарей с файлов / БД !

        return DictRegistry.__instance

    def getVerbDescrByLemma(self, lemma):
        """
        Универсализация получения описания глагола.
        """
        result = None
        if self.isLemmaInCompDict(lemma):
            result = self.getCompVerb(lemma)
        elif self.isLemmaInConnDict(lemma):
            result = self.getConnVerb(lemma)
        return result

    def isVerbReversed(self, lemma, verb_descr = None):
        """
        Проверка и выставление флага 'reversed' (смена направления sbj->obj)
        для отметки в структуре triplet (и последующего применения)
        """
        result = False

        if not verb_descr:
            verb_descr = self.getVerbDescrByLemma(lemma)

        if verb_descr:
            if 'reversed' in verb_descr:
                result = bool(verb_descr['reversed'])

        return result

    def isLemmaInCompDict(self, lemma):
        """
        Проверка вхождения слова в словарь СОСТАВА конструкций.
        С проверкой синонимов.
        """
        result = False
        if lemma in self.composition_verbs:
            result = True
        elif lemma in self.verbs_synonyms:
            key = self.verbs_synonyms[lemma]
            if key in self.composition_verbs:
                result = True
        return result

    def isLemmaInConnDict(self, lemma):
        """
        Проверка вхождения слова в словарь СВЯЗЕЙ.
        С проверкой синонимов.
        """
        result = False
        if lemma in self.connection_verbs:
            result = True
        elif lemma in self.verbs_synonyms:
            key = self.verbs_synonyms[lemma]
            if key in self.connection_verbs:
                result = True
        return result

    def getCompVerb(self, lemma):
        """
        Возвращает структуру глагола СОСТАВА по лемме;
        Присутствие ключа - внешняя проверка!
        С проверкой синонимов.
        """
        result = None
        # Reference key
        if lemma in self.verbs_synonyms:
            key = self.verbs_synonyms[lemma]
        else:
            key = lemma

        if key in self.composition_verbs:
            result = self.composition_verbs[key]

        return result

    def getConnVerb(self, lemma):
        """
        Возвращает структуру глагола СВЯЗИ по лемме;
        Присутствие ключа - внешняя проверка!
        С проверкой синонимов.
        """
        result = None
        # Reference key
        if lemma in self.verbs_synonyms:
            key = self.verbs_synonyms[lemma]
        else:
            key = lemma

        if key in self.connection_verbs:
            result = self.connection_verbs[key]

        return result
