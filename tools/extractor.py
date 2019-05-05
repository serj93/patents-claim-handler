import pprint as pp
import copy

from tools.registry import DictRegistry
from tools.helpers.seghelper import SegmentHelper

# Извлечение триплетов
class SAOExtractor(object):

    def __init__(self):
        self.registry = DictRegistry()
        self.shelper = SegmentHelper()

    def startExtraction(self, segments):
        # DEBUGGER
        self.is_print_sao = False
        self.can_print = False
        self.print_counter = 0

        triplets = self.extractTriplets(segments)

        return triplets

    def extractTriplets(self, segments):
        triplets = []
        # Родовое понятие
        generic_term = None
        # Фильтр "полных" предложений
        full_segm_types = ['N_V_N', 'N_который_V_N', 'который_V_N', 'SC']

        for seg_index in range(0, len(segments)):
            segment = segments[seg_index]

            if segment['type'] in self.registry.drop_segments:
                continue

            #print(segment['segm'])

            # Выделение родового понятия --------------------------------------\
            if seg_index == 0:
                is_convert = True
                if segment['type'] == 'N_V_N':
                    verbs = self.findTargetVerbs(segment)
                    # Преобразование напрямую если нет глаголов "содержания"
                    is_convert = not verbs

                if is_convert:
                    generic_term = self.getGenericTerm(segment)

                    if False:
                        print(segment['type'])
                        pp.pprint(generic_term['labels'])
                        pp.pprint(generic_term['text'])
            #------------------------------------------------------------------/

            segment_link_type = segment['link']['type']
            # DEBUGGER
            self.can_print = segment['id'] == 333

            if segment['type'] == 'V_N':

                parent_segm_id = segment['link']['parent']
                parent_point_id = segment['link']['point']
                sent_len = len(segment['morph'])

                # Case 1
                if segment_link_type == 'sub':

                    if parent_segm_id == None or parent_point_id == None:
                        continue

                    # Если первый сегмент - взять родовое понятие
                    if parent_segm_id == 1 and generic_term:
                        sbj_data = copy.deepcopy(generic_term)
                    # Иначе - извлекаем родителя напрямую
                    else:
                        # Поиск левой части (субъекта) -----------------------------------------------\
                        parent_segm = self.shelper.getListElementById(segments, parent_segm_id)
                        if not parent_segm:
                            continue

                        # aka SBJ
                        sbj_data = self.getParentNP(parent_segm['morph'], parent_point_id)
                        if not sbj_data:
                            continue
                        # Коррекциия ИД родительского сегмента
                        sbj_data['seg_id'] = parent_segm_id
                        if self.can_print and False:
                            print("Segment:\n{} {}\n".format(segment['id'], segment['segm']))
                            pp.pprint(sbj_data)
                            exit(0)
                        #--------------------------------------------------------------------------/

                    # Проверка на структуру V_V_N
                    nested_verbs = self.checkNestedVerbs(segment['morph'])

                    # Обработка структуры V_V_N
                    if nested_verbs:
                        ext_verb_index = nested_verbs[0]
                        int_verb_index = nested_verbs[1]

                        # DEBUGGER ---------------------\
                        if False:
                            print(segment['segm'])
                            pp.pprint(nested_verbs)
                            print('')
                        #-------------------------------/

                        # Add marker
                        segment['morph'][int_verb_index]['ref'] = ext_verb_index

                        # Check borders
                        if int_verb_index + 1 >= sent_len:
                            continue

                        # Find OBJECT
                        right_range = range(int_verb_index + 1, sent_len)
                        right_labels = ['' for i in right_range]

                        left_text, right_text = self.splitTextByVerbIndex(segment['text'], segment['morph'], int_verb_index)
                        if not right_text:
                            continue

                        # Валентность глагола (! 1-го !)
                        act_text = segment['morph'][ext_verb_index]['lemma']
                        verb = self.registry.getVerbDescrByLemma(act_text)

                        # Попытка обнаружения объекта
                        obj_data = self.extractObject(segment['morph'], right_range, right_labels, right_text, verb, [])
                        # Создание SAO
                        if obj_data:
                            obj_data['seg_id'] = segment['id']
                            true_verb_key = str(segment['id']) + '.' + segment['morph'][ext_verb_index]['id']
                            self_verb_key = str(segment['id']) + '.' + segment['morph'][int_verb_index]['id']
                            act_data = {'text': act_text, 'key': self_verb_key, 'ref': true_verb_key, 'side': 'r'}

                            # Check reversing
                            is_reversed = self.registry.isVerbReversed(act_text, verb)
                            if is_reversed:
                                act_data['reversed'] = True

                            triplet = {'SBJ': sbj_data, 'ACT': act_data, 'OBJ': obj_data}
                            triplets.append(triplet)
                            # DEBUGGER
                            self.printTriplet(triplet)
                    # Поиск по всем глаголам структуры V_N
                    else:
                        sub_triplets = self.findAllAOInSegment(segment)

                        if self.can_print and False:
                            pp.pprint(sub_triplets)
                            exit(0)

                        if sub_triplets:
                            for triplet in sub_triplets:
                                triplet['SBJ'] = sbj_data
                                triplets.append(triplet)
                                # DEBUGGER
                                self.printTriplet(triplet)

                # Case 2
                elif segment_link_type == 'homo':

                    self_point_id = segment['link']['child']

                    if parent_segm_id == None or parent_point_id == None or self_point_id == None:
                        continue

                    # Проверка родительского ключа в словаре (должен быть СУБЪЕКТ или ОБЪЕКТ)
                    parent_segm = self.shelper.getListElementById(segments, parent_segm_id)
                    if not parent_segm:
                        continue

                    # Уже должна быть точка привязки (субъект или объект)
                    verb_parent_key = str(parent_segm_id) + '.' + parent_point_id
                    # Is (sbj_data, act_data, obj_data)
                    parent_data = self.findSAOByKey(triplets, verb_parent_key)
                    if not parent_data:
                        continue

                    verb_index = self.shelper.getListIndexByVal(segment['morph'], 'id', self_point_id)
                    if not verb_index:
                        continue

                    right_range = range(verb_index + 1, sent_len)
                    right_labels = ['' for i in right_range]

                    left_text, right_text = self.splitTextByVerbIndex(segment['text'], segment['morph'], verb_index)
                    if not right_text:
                        continue

                    # Валентность глагола из родительской связки
                    act_text = parent_data[1]['text']
                    verb = self.registry.getVerbDescrByLemma(act_text)
                    # Попытка обнаружения объекта
                    obj_data = self.extractObject(segment['morph'], right_range, right_labels, right_text, verb, [])
                    # Создание SAO
                    if obj_data:
                        obj_data['seg_id'] = segment['id']
                        # Ссылка на замененный глагол в родном сегменте!!!
                        self_verb_key = str(segment['id']) + '.' + self_point_id
                        sbj_data = parent_data[0]
                        act_data = {'text': act_text, 'key': self_verb_key, 'ref': verb_parent_key, 'side': 'r'}
                        # Check reversing
                        is_reversed = self.registry.isVerbReversed(act_text, verb)
                        if is_reversed:
                            act_data['reversed'] = True

                        triplet = {'SBJ': sbj_data, 'ACT': act_data, 'OBJ': obj_data}
                        triplets.append(triplet)
                        # DEBUGGER
                        #self.printTriplet(triplet)

                # Case 3
                elif segment_link_type == 'gap':
                    # Условие GAP: segment['template'].find('V<F>') == 0
                    if parent_segm_id == None:
                        continue

                    # Find verb
                    verbs = self.findTargetVerbs(segment)
                    if not verbs:
                        continue

                    # Провекра только первого глагола!
                    verbs_indexes = verbs.keys()
                    verb_index = list(verbs_indexes)[0]
                    if verb_index + 1 >= sent_len:
                        continue

                    # Find OBJECT
                    right_range = range(verb_index + 1, sent_len)
                    right_labels = ['' for i in right_range]
                    left_text, right_text = self.splitTextByVerbIndex(segment['text'], segment['morph'], verb_index)
                    if not right_text:
                        continue

                    # Get left_part
                    parent_segment = self.shelper.getListElementById(segments, parent_segm_id)
                    if not parent_segment:
                        continue

                    parent_segm_len = len(parent_segment['morph'])
                    left_range = range(0, parent_segm_len)
                    left_labels = ['' for i in left_range]
                    left_text = parent_segment['text']

                    left_data = {
                        'morph': parent_segment['morph'],
                        'range': left_range,
                        'labels': left_labels,
                        'text': left_text,
                        'seg_id': parent_segment['id'],
                    }

                    right_data = {
                        'morph': segment['morph'],
                        'range': right_range,
                        'labels': right_labels,
                        'text': right_text,
                        'seg_id': segment['id'],
                    }

                    verb = verbs[verb_index]
                    verb_token = segment['morph'][verb_index]

                    triplet = self.findStructures(right_data, left_data, verb, verb_token)
                    if triplet:
                        triplets.append(triplet)
                        # DEBUGGER
                        self.printTriplet(triplet)

                # Case 4
                elif segment_link_type == 'self':
                    # Нет родового понятния
                    if not generic_term:
                        continue

                    sub_triplets = self.findAllAOInSegment(segment)
                    if sub_triplets:
                        for triplet in sub_triplets:
                            # Add SBJ!
                            triplet['SBJ'] = generic_term
                            triplets.append(triplet)
                            # DEBUGGER
                            self.printTriplet(triplet)

            # N_V_N & Co
            elif segment['type'] in full_segm_types:

                # Find verb
                verbs = self.findTargetVerbs(segment)
                if not verbs:
                    continue

                # DEBUGGER -----------------\
                if self.can_print and False:
                    print("{}\n{}, {}\n".format(segment['segm'], segment['tracking'], segment['type']))
                    pp.pprint(verbs)
                    exit(0)
                #---------------------------/

                # Проверка на структуру V_V_N
                nested_verbs = self.checkNestedVerbs(segment['morph'])
                # Обработка структуры V_V_N
                if nested_verbs:
                    ext_verb_index = nested_verbs[0]
                    int_verb_index = nested_verbs[1]

                    # Add marker
                    segment['morph'][int_verb_index]['ref'] = ext_verb_index

                    if int_verb_index in verbs.keys():
                        del verbs[int_verb_index]

                if not verbs:
                    continue

                verbs_indexes = verbs.keys()
                sent_len = len(segment['morph'])

                # Специальная маркировка для дальнейшего уточнения ------------\
                mark_which = None
                if segment['type'] == 'N_который_V_N':
                    mark_which = 'which1'
                elif segment['type'] == 'который_V_N':
                    mark_which = 'which2'
                #--------------------------------------------------------------/

                #if self.can_print:
                #    pp.pprint(verbs)
                #    exit(0)

                # Handling each verb
                for verb_index in verbs_indexes:
                    # Check borders
                    if verb_index + 1 >= sent_len or verb_index <= 0:
                        continue

                    # Find OBJECT
                    left_range = range(0, verb_index)
                    right_range = range(verb_index + 1, sent_len)

                    left_labels = ['' for i in left_range]
                    right_labels = ['' for i in right_range]

                    left_text, right_text = self.splitTextByVerbIndex(segment['text'], segment['morph'], verb_index)

                    if not right_text or not left_text:
                        continue

                    right_data = {
                        'morph': segment['morph'],
                        'range': right_range,
                        'labels': right_labels,
                        'text': right_text,
                        'seg_id': segment['id'],
                    }

                    left_data = {
                        'morph': segment['morph'],
                        'range': left_range,
                        'labels': left_labels,
                        'text': left_text,
                        'seg_id': segment['id'],
                    }

                    verb = verbs[verb_index]
                    verb_token = segment['morph'][verb_index]

                    #if self.can_print:
                    #    pp.pprint(segment['morph'])
                    #    exit(0)

                    triplet = self.findStructures(right_data, left_data, verb, verb_token, mark_which)
                    if triplet:

                        # Сохранить линк для дальнейшего анализа (генерация неявной связки)
                        if mark_which:
                            if mark_which in triplet['SBJ']:
                                triplet['SBJ'][mark_which] = segment['link']
                            elif mark_which in triplet['OBJ']:
                                triplet['OBJ'][mark_which] = segment['link']

                        if 'after_sep' in segment:
                            triplet['SBJ']['after_sep'] = True
                            triplet['OBJ']['after_sep'] = True

                        triplets.append(triplet)

                        # Родовое понятие как СУБЪЕКТ первой связки - ADD -----\
                        if seg_index == 0 and generic_term == None:
                            generic_term = triplet['SBJ']
                        #------------------------------------------------------/

                        # DEBUGGER
                        self.printTriplet(triplet)

            elif segment['type'] == 'N_-_N':

                parent_segm_id = segment['link']['parent']
                parent_point_id = segment['link']['point']
                sent_len = len(segment['morph'])

                if parent_segm_id == None or parent_point_id == None:
                    continue

                # Поиск ключа в собранных конструкциях
                parent_segm = self.shelper.getListElementById(segments, parent_segm_id)
                if not parent_segm:
                    continue

                verb_token = self.shelper.getListElementById(parent_segm['morph'], parent_point_id)
                if not verb_token:
                    continue

                verb = self.registry.getVerbDescrByLemma(verb_token['lemma'])
                if not verb:
                    continue

                split_index = self.getFirstIndexByLemma(segment['morph'], '-')
                if not split_index:
                    continue

                # Check borders
                if split_index + 1 >= sent_len or split_index <= 0:
                    continue

                # Find OBJECT
                left_range = range(0, split_index)
                right_range = range(split_index + 1, sent_len)

                left_labels = ['' for i in left_range]
                right_labels = ['' for i in right_range]

                left_text, right_text = self.splitTextByVerbIndex(segment['text'], segment['morph'], split_index)

                if not right_text or not left_text:
                    continue

                right_data = {
                    'morph': segment['morph'],
                    'range': right_range,
                    'labels': right_labels,
                    'text': right_text,
                    'seg_id': segment['id'],
                }

                left_data = {
                    'morph': segment['morph'],
                    'range': left_range,
                    'labels': left_labels,
                    'text': left_text,
                    'seg_id': segment['id'],
                }

                triplet = self.findStructures(right_data, left_data, verb, verb_token)

                #if self.can_print:
                #    print("LOL")
                #    pp.pprint(triplet)
                #    exit(0)

                if triplet:
                    # Отметка специфичного
                    triplet['ACT']['type'] = segment['link']['type']
                    # Коррекция ключа!!! Сегмент свой, а токен (ИД глагола) из другого...
                    triplet['ACT']['key'] = str(segment['id']) + '.' + segment['morph'][split_index]['id']
                    # Ссылка на настоящий глагол
                    triplet['ACT']['ref'] = str(parent_segm['id']) + '.' + parent_point_id

                    triplets.append(triplet)
                    # DEBUGGER
                    #self.printTriplet(triplet)

                else:
                    # Поиск родительской связки (субъект или объект)
                    verb_parent_key = str(parent_segm_id) + '.' + parent_point_id
                    # Is (sbj_data, act_data, obj_data)
                    parent_data = self.findSAOByKey(triplets, verb_parent_key)
                    if not parent_data:
                        continue

                    # Проверка наличия ОБЪЕКТА в последовательности
                    markers = ['N-OBJ']
                    is_found_obj = self.checkMarkersInLabels(markers, right_labels)
                    if is_found_obj:
                        # Используем размеченные данные правой части (ОБЪЕКТ)
                        del right_data['morph']
                        triplet = {
                            'SBJ': parent_data[0],
                            'ACT': parent_data[1],
                            'OBJ': right_data
                        }

                        # Отметка специфичного
                        #triplet['ACT']['type'] = segment['link']['type']
                        triplets.append(triplet)
                        # DEBUGGER
                        #self.printTriplet(triplet)

            elif segment['type'] == 'N' and segment_link_type == 'homo':

                # Пропуск частей Gap
                if 'used' in segment:
                    continue

                parent_segm_id = segment['link']['parent']
                parent_point_id = segment['link']['point']

                if parent_segm_id == None or parent_point_id == None:
                    continue

                # Валентность глагола из родительского сегмента
                parent_segment = self.shelper.getListElementById(segments, parent_segm_id)
                verb_token = self.shelper.getListElementById(parent_segment['morph'], parent_point_id)
                if not verb_token:
                    continue

                verb_lemma = verb_token['lemma']
                verb = self.registry.getVerbDescrByLemma(verb_lemma)
                if not verb:
                    continue

                # Правая часть из своего сегмента
                sent_len = len(segment['morph'])
                right_range = range(0, sent_len)
                right_labels = ['' for i in right_range]
                right_text = segment['text'].lower()

                # Уже должна быть точка привязки (субъект или объект)
                verb_parent_key = str(parent_segm_id) + '.' + parent_point_id
                # Is (sbj_data, act_data, obj_data)
                parent_data = self.findSAOByKey(triplets, verb_parent_key)

                # Возможно есть ссылка на внешний глагол (структура V1(ext)_V(int)_N)
                if not parent_data and 'ref' in verb_token:
                    ext_verb_id = parent_segment['morph'][verb_token['ref']]['id']
                    verb_parent_key = str(parent_segm_id) + '.' + ext_verb_id
                    parent_data = self.findSAOByKey(triplets, verb_parent_key)


                # Есть точка привязки
                if parent_data:
                    # Учет того, что именно (СУБЪЕКТ или ОБЪЕКТ) искать с правой стороны
                    # aka is_obj_in_right or where Obj
                    is_successful = False
                    if parent_data[1]['side'] == 'r':
                        # Попытка обнаружения объекта
                        obj_data = self.extractObject(segment['morph'], right_range, right_labels, right_text, verb, [])
                        if obj_data:
                            obj_data['seg_id'] = segment['id']
                            sbj_data = parent_data[0]
                            is_successful = True
                    else:
                        sbj_data = self.extractSubject(segment['morph'], right_range, right_labels, right_text, verb, [])
                        if sbj_data:
                            sbj_data['seg_id'] = segment['id']
                            obj_data = parent_data[2]
                            is_successful = True

                    # Доп. эвристика: если явно указаны точки привязки, но не нашли на предыдущем этапе
                    # Sample: состоящим ИЗ корпуса, ротора с центробежным колесом (нет предлога в однородных - не найдет)
                    point_id = segment['link']['child']
                    if not is_successful and point_id != None:

                        ### Не всегда хомо как объект, надо смотреть по глаголу!!! Как выше...

                        obj_data = self.getParentNP(segment['morph'], point_id, prefix = 'OBJ')
                        if obj_data:
                            obj_data['seg_id'] = segment['id']
                            sbj_data = parent_data[0]
                            is_successful = True

                    if is_successful:
                        # Создание SAO
                        act_data = parent_data[1]
                        triplet = {'SBJ': sbj_data, 'ACT': act_data, 'OBJ': obj_data}
                        triplets.append(triplet)
                        # DEBUGGER
                        self.printTriplet(triplet)

                # Если готовых связок нет, нужно поискать вместе
                else:
                    # Поиск структур
                    verb_index = self.shelper.getListIndexByVal(parent_segment['morph'], 'id', parent_point_id)

                    # Find OBJECT
                    left_range = range(0, verb_index)
                    left_labels = ['' for i in left_range]

                    left_text, right_text = self.splitTextByVerbIndex(parent_segment['text'], parent_segment['morph'], verb_index)
                    if not left_text:
                        continue

                    right_data = {
                        'morph': segment['morph'],
                        'range': right_range,
                        'labels': right_labels,
                        'text': right_text,
                        'seg_id': segment['id'],
                    }

                    left_data = {
                        'morph': parent_segment['morph'],
                        'range': left_range,
                        'labels': left_labels,
                        'text': left_text,
                        'seg_id': parent_segment['id'],
                    }

                    mark_which = None
                    triplet = self.findStructures(right_data, left_data, verb, verb_token, mark_which)
                    if triplet:
                        triplets.append(triplet)
                        # DEBUGGER
                        self.printTriplet(triplet)

        # DEBUGGER
        if self.is_print_sao:
            print("TRIPLETS COUNT: {}\n".format(len(triplets)))

        return generic_term, triplets

    def printTriplet(self, triplet):
        """
        Debug-отрисовка связок
        """
        is_full = False
        if self.is_print_sao:

            self.print_counter += 1
            print("# {}".format(self.print_counter))

            if is_full:
                print("S: {}\n   {}".format(triplet['SBJ']['text'], triplet['SBJ']['labels']))
                print("A: {}".format(triplet['ACT']['text']))
                print("O: {}\n   {}\n".format(triplet['OBJ']['text'], triplet['OBJ']['labels']))
            else:
                print("S: {}".format(triplet['SBJ']['text']))
                print("A: {}".format(triplet['ACT']['text']))
                print("O: {}\n".format(triplet['OBJ']['text']))

    def checkMarkersInLabels(self, markers, x_labels):
        '''
        Проверка вхождения маркеров в последовательность меток.
        result: True | False
        '''
        result = False
        for marker in x_labels:
            if marker in x_labels:
                result = True
                break
        return result

    def getFirstIndexByLemma(self, morph, lemma):
        '''
        Возвращает индекс первого слова по лемме.
        Для поиска промежутка - в dupl.
        '''
        result = None
        for index in range(len(morph)):
            token = morph[index]
            if token['text'] == lemma:
                result = index
                break
        return result

    def findAllAOInSegment(self, segment):
        '''
        Обертка поиска триплетов (БЕЗ СУБЪЕКТА!) в левой части.
        Множественный поиск только ОБЪЕКТА.
        Тип: V_N
        '''
        triplets = []

        # Find verb
        verbs = self.findTargetVerbs(segment)
        if not verbs:
            return None

        verbs_indexes = verbs.keys()
        sent_len = len(segment['morph'])

        #if self.can_print:
        #    pp.pprint(verbs)
        #    exit(0)

        # Handling each verb
        for verb_index in verbs_indexes:
            # Check borders (FOR ALL)
            if verb_index + 1 >= sent_len:
                continue

            # Find OBJECT
            right_range = range(verb_index + 1, sent_len)
            right_labels = ['' for i in right_range]

            left_text, right_text = self.splitTextByVerbIndex(segment['text'], segment['morph'], verb_index)

            if not right_text:
                continue

            # Валентность глагола
            verb = verbs[verb_index]
            # Попытка обнаружения объекта
            obj_data = self.extractObject(segment['morph'], right_range, right_labels, right_text, verb, [])
            # Создание SAO
            if obj_data:
                obj_data['seg_id'] = segment['id']
                verb_key = str(segment['id']) + '.' + segment['morph'][verb_index]['id']
                act_text = segment['morph'][verb_index]['lemma']
                act_data = {'text': act_text, 'key': verb_key, 'side': 'r'}
                # Check reversing
                is_reversed = self.registry.isVerbReversed(act_text, verb)
                if is_reversed:
                    act_data['reversed'] = True

                triplets.append({'SBJ': None, 'ACT': act_data, 'OBJ': obj_data})

        return triplets

    def findStructures(self, right_data, left_data, verb, verb_token, mark_which = None):
        '''
        Обертка поиска ОБЪЕКТА и СУБЪЕКТА в зависимости от типа глагола.
        '''
        is_obj_in_right = False
        is_successful = False
        obj_data = None
        sbj_data = None

        # Пересборка глагола для последовательной проверки частей на объект
        for obj_valence in verb['obj']:
            mod_verb = copy.deepcopy(verb)
            mod_verb['obj'] = [obj_valence]

            drop_valences = []

            # E0 and E1
            if mod_verb['entry'] < 2:

                # Try to find OBJ in RIGHT part
                obj_data = self.extractObject(right_data['morph'], right_data['range'], right_data['labels'], right_data['text'], mod_verb, drop_valences)

                #if self.can_print:
                #    print("#")
                #    pp.pprint(obj_data)
                #    exit(0)

                # Try to find SBJ in LEFT part
                if obj_data:
                    sbj_data = self.extractSubject(left_data['morph'], left_data['range'], left_data['labels'], left_data['text'], mod_verb, drop_valences)
                    if not sbj_data:
                        continue

                    is_obj_in_right = True
                    is_successful = True
                    break

                # Try to find OBJ in LEFT part
                else:
                    # Only S-A-O
                    if mod_verb['entry'] == 0:
                        continue

                    drop_valences = []
                    obj_data = self.extractObject(left_data['morph'], left_data['range'], left_data['labels'], left_data['text'], mod_verb, drop_valences)
                    if not obj_data:
                        continue

                    # Try to find SBJ in RIGHT part
                    sbj_data = self.extractSubject(right_data['morph'], right_data['range'], right_data['labels'], right_data['text'], mod_verb, drop_valences)
                    if not sbj_data:
                        continue

                    is_successful = True
                    break

            # E2 (O-S-A)
            else:
                obj_data = self.extractObject(left_data['morph'], left_data['range'], left_data['labels'], left_data['text'], mod_verb, drop_valences)
                if not obj_data:
                    continue

                # Try to find SBJ in RIGHT part
                sbj_data = self.extractSubject(right_data['morph'], right_data['range'], right_data['labels'], right_data['text'], mod_verb, drop_valences)
                if not sbj_data:
                    continue

                is_successful = True
                break

        # Check result
        if not is_successful:
            return None

        # Data of all sides already filled

        # Коррекциия ИД родительского сегмента
        if is_obj_in_right:
            side_marker = 'r'
            if mark_which:
                sbj_data[mark_which] = None
            sbj_data['seg_id'] = left_data['seg_id']
            obj_data['seg_id'] = right_data['seg_id']
        else:
            side_marker = 'l'
            if mark_which:
                obj_data[mark_which] = None
            sbj_data['seg_id'] = right_data['seg_id']
            obj_data['seg_id'] = left_data['seg_id']

        act_data = {
            'text': verb_token['lemma'],
            'key': str(obj_data['seg_id']) + '.' + verb_token['id'],
            'side': side_marker
        }

        # Check reversing
        is_reversed = self.registry.isVerbReversed(verb_token['lemma'])
        if is_reversed:
            act_data['reversed'] = True

        triplet = {'SBJ': sbj_data, 'ACT': act_data, 'OBJ': obj_data}

        return triplet

    def extractSubject(self, morph, x_range, x_labels, x_text, verb, drop_valences = []):
        '''
        Обвязка всей последовательности извлечения субъекта.
        '''
        result = None

        # Add marker
        if 'add' in verb:
            self.findAddValence(
                morph,
                x_range,
                x_labels,
                x_text,
                verb['add'],
                drop_valences
            )

        # Sbj marker
        is_successful = self.findSbjValence(
            morph,
            x_range,
            x_labels
        )

        # Combine OBJECT
        if is_successful:
            self.correctLeftNPsFill(
                morph,
                x_range,
                x_labels,
                self.registry.label_points['np_roots'],
                self.registry.break_pos
            )

            if self.can_print and False:
                print("#")
                print(x_text)
                pp.pprint(x_labels)
                exit(0)

            sbj_text = self.combineTextOnLabels(
                morph,
                x_range,
                x_labels,
                self.registry.label_points['np_sbj']
            )

            if sbj_text:
                result = {'range': x_range, 'labels': x_labels, 'text': sbj_text, 'seg_id': -1}

        return result

    def findSbjValence(self, morph, x_range, x_labels):
        '''
        Поиск валентности субъекта (Noun<Case> >> Pron<Case> >> Adj<Case>)
        '''
        result = False
        target_poses = ['NOUN', 'PRON', 'NUM', 'ADJ', 'DET']
        target_cases = ['Nom', 'Acc']
        for target_pos in target_poses:
            result = self.markSbjTokens(morph, x_range, x_labels, target_pos, target_cases)
            if result:
                break

        #if self.can_print:
        #    pp.pprint(x_labels)

        # Fill gaps
        points = ['P-SBJ', 'N-SBJ', 'A-SBJ']
        break_pos = ['ADV']
        self.fillNPsGaps(morph, x_range, x_labels, points, break_pos, is_sbj = True)

        return result

    def markSbjTokens(self, morph, x_range, x_labels, target_pos, target_cases):
        result = False
        drop_poses = ['VERB'] # Experimental!!!
        shift = x_range[0]

        skip_border = 2
        token_counter = 0
        for i in x_range:
            token_counter += 1
            pos = morph[i]['pos']

            if pos in drop_poses:
                can_skip = token_counter <= skip_border
                if not can_skip:
                    break

            if pos == target_pos:
                case = self.shelper.getCase(morph[i])
                if case in target_cases:
                    if x_labels[i - shift] == '':

                        # Доп. проверка: у субъекта не может быть предлога перед корнем!
                        prev_i = i - 1
                        if prev_i in x_range:
                            prev_pos = morph[prev_i]['pos']
                            if prev_pos == 'ADP':
                                continue

                        # Метоимения сокращаются и путаются с предлогом (P-SBJ): N-SBJ (местоимение)
                        if target_pos == 'PRON' or 'DET':
                            first_char = 'N'
                        else:
                            first_char = target_pos[0]
                        x_labels[i - shift] = first_char + '-SBJ'
                        result = True

        return result

    def findSAOByKey(self, triplets, target_key):
        '''
        Return Subject-Action-Object for HOMO.
        '''
        result = None
        for triplet in triplets:
            if triplet['ACT']['key'] == target_key:
                result = (triplet['SBJ'], triplet['ACT'], triplet['OBJ'])
                break
            if 'ref' in triplet['ACT']:
                if triplet['ACT']['ref'] == target_key:
                    result = (triplet['SBJ'], triplet['ACT'], triplet['OBJ'])
                    break
        return result

    def findTargetVerbs(self, segment):
        '''
        Возвращает словарь ИНДЕКС целевых глаголов по всему предложению.
        '''
        result = {}
        if 'morph' in segment:
            for index in range(0, len(segment['morph'])):
                token = segment['morph'][index]
                if self.registry.isLemmaInCompDict(token['lemma']) or \
                self.registry.isLemmaInConnDict(token['lemma']):
                    # Add point
                    local_key = index
                    valence = None

                    if self.registry.isLemmaInCompDict(token['lemma']):
                        valence = self.registry.getCompVerb(token['lemma'])
                    elif self.registry.isLemmaInConnDict(token['lemma']):
                        valence = self.registry.getConnVerb(token['lemma'])

                    result[local_key] = valence

        return result

    def extractObject(self, morph, x_range, x_labels, x_text, verb, drop_valences = []):
        '''
        Обвязка всей последовательности извлечения конструкции.
        '''
        result = None

        is_successful = self.findObjValence(
            morph,
            x_range,
            x_labels,
            x_text,
            verb['obj']
        )

        if self.can_print and False:
            print("#")
            pp.pprint(x_text)
            pp.pprint(x_labels)
            #exit(0)

        if is_successful:
            # Add marker -----------------------------\
            if 'add' in verb:
                self.findAddValence(
                    morph,
                    x_range,
                    x_labels,
                    x_text,
                    verb['add'],
                    drop_valences
                )
            #-----------------------------------------/

            self.correctLeftNPsFill(
                morph,
                x_range,
                x_labels,
                self.registry.label_points['np_roots'],
                self.registry.break_pos
            )

            obj_text = self.combineTextOnLabels(
                morph,
                x_range,
                x_labels,
                self.registry.label_points['np_obj']
            )

            if obj_text:
                result = {'range': x_range, 'labels': x_labels, 'text': obj_text, 'seg_id': -1}

        return result

    def combineTextOnLabels(self, morph, x_range, x_labels, points):
        '''
        Extract NPs on labels from morphologyself.
        '''
        result = ''
        buffer = []
        shift = x_range[0]
        for i in x_range:
            label_index = i - shift
            if x_labels[label_index] in points:
                buffer.append(morph[i]['text'])
        if len(buffer) > 0:
            result = ' '.join(buffer).lower()

        return result

    def findAddValence(self, morph, x_range, x_labels, x_text, valences, drop_valences):
        '''
        Поиск вспомогательных валентностей ([PREP] Noun<Case>) в последовательности.
        Промежутки между предлогами и сущ. маркируются так же.
        '''
        result = False
        # Loop for each valence version
        for valence_index in range(0, len(valences)):
            # Drop filled valences
            if valence_index in drop_valences:
                continue
            valence = valences[valence_index]
            marker = valence['type']

            # Can be several starts
            start_indexes = [x_range[0]]
            index_type = 'SENT'

            if valence['before']:
                # Check prepositions ------------------------------------------\
                if valence['before']['mandatory']:
                    index_type = valence['before']['type']
                    # Full words
                    if index_type == 'WORD':
                        target_before = ''
                        for token in valence['before']['tokens']:
                            cor_token = token + ' '
                            if cor_token in x_text:
                                target_before = token
                                break

                        # Check another valence
                        if not target_before:
                            continue

                        # Find each part of word and get new start_indexes
                        word_parts = target_before.split(' ')
                        for i in x_range:
                            buf_i = i
                            is_successful = True
                            for word_part in word_parts:
                                if morph[buf_i]['text'] != word_part:
                                    is_successful = False
                                    break
                                buf_i += 1

                            if is_successful:
                                start_indexes[0] = i
                                break
                    # Prepositions
                    elif index_type == 'ADP':
                        is_successful = False
                        for token in valence['before']['tokens']:
                            for i in x_range:
                                if morph[i]['text'] == token:
                                    # First position
                                    if not is_successful:
                                        start_indexes[0] = i
                                        is_successful = True
                                    else:
                                        start_indexes.append(i)

                        if not is_successful:
                            continue

                #--------------------------------------------------------------/

            # Find N<Case>
            shift = x_range[0]
            for start_index in start_indexes:
                for i in x_range:
                    if i < start_index:
                        continue
                    if morph[i]['pos'] == 'NOUN':
                        case = self.shelper.getCase(morph[i])
                        if case in valence['case']:

                            # Check wrong detection ---------------------------\
                            if not valence['before']:
                                skip_detection = False

                                #print(morph[i]['text'])
                                #pp.pprint(list(reversed(range(shift,i))))
                                #exit()

                                # Strong fill!
                                if x_labels[i - shift] != '':
                                    break

                                for k in reversed(range(shift,i)):
                                    if morph[k]['pos'] == 'ADP':
                                        skip_detection = True
                                        break
                                    elif morph[k]['pos'] == 'ADJ':
                                        continue
                                    else:
                                        break

                                if skip_detection:
                                    break
                            # -------------------------------------------------/

                            # Before marker
                            if index_type != 'SENT':
                                x_labels[start_index - shift] = 'P-' + marker
                                # Marked full WORD
                                if index_type == 'WORD':
                                    parts_len = len(word_parts)
                                    if parts_len > 1:
                                        increment = 1
                                        while increment < parts_len:
                                            x_labels[start_index - shift + increment] = 'P-' + marker
                                            increment += 1

                            result = True
                            drop_valences.append(valence_index)
                            # Noun marker
                            x_labels[i - shift] = 'N-' + marker
                            # Drop any way
                            break

        # Fill marker gaps
        points = self.registry.label_points['np_add']
        break_pos = ['ADV']

        self.fillAddGaps(morph, x_range, x_labels, points, break_pos)

        return result

    def correctLeftNPsFill(self, morph, x_range, x_labels, points, break_pos):
        '''
        Коррекция заполнение левой границы ИГ.
        '''
        can_mark = False
        shift = x_range[0]
        marker = ''

        allowed_homo = ['ADJ', 'NUM', 'ANUM']

        #Experimental_1
        parent_id = None

        for i in reversed(x_range):
            label_index = i - shift
            # Start (continue) of fill
            if x_labels[label_index] in points:
                marker = 'I-' + x_labels[label_index].split('-')[1]
                NP_num = morph[i]['mark']

                #Experimental_1
                if morph[i]['deprel'] == 'nsubj':
                    parent_id = morph[i]['parent']

                can_mark = True
                continue

            token_pos = morph[i]['pos']

            if x_labels[label_index] != '' or token_pos in break_pos:
                continue

            # Experimental_1
            # Fix: посредством [ немагнитного_? диска_? РОТОР медленного вращения...
            if morph[i]['id'] == parent_id:
                break

            if can_mark:
                if NP_num == morph[i]['mark']:
                    x_labels[label_index] = marker
                else:
                    # Проверка на предшествующие однородные
                    # Sample: имеющих [ передние ] и [ задние внутренние каналы охлаждения ]
                    # Переползаем через сочинительный союз
                    if token_pos == 'CCONJ':
                        prev_i = i - 1
                        if prev_i >= 0:
                            if morph[prev_i]['pos'] in allowed_homo:
                                x_labels[label_index] = marker
                                NP_num = morph[prev_i]['mark']
                                continue

                    can_mark = False
        return

    def fillAddGaps(self, morph, x_range, x_labels, points, break_pos):
        '''
        Fill full ADD parts.
        '''
        marker = ''
        can_mark = False
        can_rewrite = False
        shift = x_range[0]

        for i in x_range:
            label_index = i - shift
            # Start (continue) of fill
            if x_labels[label_index] in points:
                marker = 'I-' + x_labels[i - shift].split('-')[1]
                can_mark = True
                can_rewrite = x_labels[label_index].startswith('P-')
                continue

            token_pos = morph[i]['pos']

            #fix002: + x_labels[label_index] != '' - нельзя убирать проверку на пустоту!
            # Но пропускаем начало предлогов Add
            if token_pos in break_pos or (x_labels[label_index] != '' and not can_rewrite):
                continue

            if can_mark:

                #DEBUGGER
                #print('{} {} {}'.format(morph[i]['text'], morph[i]['mark'], is_empty_label))

                is_NP = morph[i]['mark'].isdigit()
                is_empty_label = x_labels[label_index] == ''

                #fix002: + is_empty_label and
                if (is_NP or token_pos == 'CCONJ'):
                    x_labels[label_index] = marker
                else:
                    can_mark = False

        return

    def findObjValence(self, morph, x_range, x_labels, x_text, valences):
        '''
        Поиск валентности объекта ([PREP] Noun<Case>) в последовательности.
        Валентности субъекта конкурирующие!
        '''
        result = False
        target_poses = ['NOUN','PRON','NUM']
        # Loop for each valence version
        for valence in valences:
            # Can be several starts
            start_indexes = [x_range[0]]
            index_type = 'SENT'
            # Experimental
            except_noun = []
            if valence['before']:
                # Check prepositions ------------------------------------------\
                if valence['before']['mandatory']:
                    index_type = valence['before']['type']
                    # Full words
                    if index_type == 'WORD':
                        target_before = ''
                        for token in valence['before']['tokens']:
                            cor_token = token + ' '
                            if cor_token in x_text:
                                target_before = token
                                break

                        # Check another valence
                        if not target_before:
                            continue

                        # Find each part of word and get new start_indexes
                        word_parts = target_before.split(' ')
                        for i in x_range:
                            buf_i = i
                            is_successful = True
                            for word_part in word_parts:
                                if morph[buf_i]['text'] != word_part:
                                    is_successful = False
                                    break
                                buf_i += 1

                            if is_successful:
                                start_indexes[0] = i
                                break
                    # Prepositions
                    elif index_type == 'ADP':

                        is_successful = False
                        for token in valence['before']['tokens']:
                            for i in x_range:
                                if morph[i]['text'] == token:
                                    # Add point
                                    if is_successful:
                                        start_indexes.append(i)
                                    else:
                                        # Check exception
                                        if 'except' in valence['before']:
                                            except_noun = valence['before']['except']
                                        # First position
                                        start_indexes[0] = i
                                        is_successful = True

                        if not is_successful:
                            continue

                #--------------------------------------------------------------/

            if self.can_print and False:
                print("#")
                print(x_text)
                pp.pprint(list(x_range))
                pp.pprint(start_indexes)
                #exit(0)

            # Find N<Case>
            shift = x_range[0]
            # Отслеживание сброса на глаголе:
            # VERB1 (main) | [ADV] [VERB <to skip>] ... N1 ... VERB2 .. N2 <to drop>
            skip_border = 3
            for start_index in start_indexes:
                token_counter = 0

                for i in x_range:
                    token_counter += 1

                    if i < start_index:
                        continue

                    pos = morph[i]['pos']

                    #if self.can_print:
                    #    print("{} ({})".format(morph[i]['text'], pos))

                    if pos == 'VERB':
                        can_skip = token_counter <= skip_border
                        if not can_skip:
                            break

                    # Experimental
                    if pos in self.registry.break_pos and i != start_index:
                       break

                    if pos in target_poses:
                        # Exception!
                        if morph[i]['text'].lower() in except_noun:
                            continue
                        # Exception 2: Прерывание на предлоге, если предлог

                        case = self.shelper.getCase(morph[i])
                        if case in valence['case']:
                            # Before marker
                            if index_type != 'SENT':
                                x_labels[start_index - shift] = 'P-OBJ'
                                # Marked full WORD
                                if index_type == 'WORD':
                                    parts_len = len(word_parts)
                                    if parts_len > 1:
                                        increment = 1
                                        while increment < parts_len:
                                            x_labels[start_index - shift + increment] = 'P-OBJ'
                                            increment += 1

                            result = True
                            # Noun marker
                            first_char = morph[i]['pos'][0]
                            # Метоимения сокращаются и путаются с предлогом (P-OBJ): N-OBJ (местоимение)
                            if morph[i]['pos'] == 'PRON':
                                first_char = 'N'
                            x_labels[i - shift] = first_char + '-OBJ'
                            # Drop in 1 way
                            # Depricated
                            #if index_type != 'ADP':
                            #    break

            # Break on that valence!
            if result:
                break

        if result:
            # Fill gaps
            points = ['P-OBJ', 'N-OBJ']
            break_pos = ['ADV']
            self.fillNPsGaps(morph, x_range, x_labels, points, break_pos, is_sbj = False)

        return result

    def fillNPsGaps(self, morph, x_range, x_labels, points, break_pos, is_sbj = True):
        '''
        Заполенение промежутков именных групп СУБЪЕКТА и ОБЪЕКТА.
        '''
        if is_sbj:
            marker = 'I-SBJ'
        else:
            marker = 'I-OBJ'

        last_pos = None
        last_index = None

        can_mark = False
        shift = x_range[0]

        for i in x_range:
            label_index = i - shift
            # Start (continue) of fill
            if x_labels[label_index] in points:
                can_mark = True
                continue

            token_pos = morph[i]['pos']

            if token_pos in break_pos or x_labels[label_index] != '':
                can_mark = False
                continue

            if can_mark:
                is_NP = morph[i]['mark'].isdigit()
                is_empty_label = x_labels[label_index] == ''

                # Разрывы сочинительным союзом только для СУБЪЕКТА
                # ...  or token_pos == 'ADP'
                ###fix001
                if is_empty_label and (is_NP or token_pos == 'CCONJ' or token_pos == 'ADP'):
                    x_labels[label_index] = marker
                    last_pos = token_pos
                    last_index = label_index
                else:
                    can_mark = False

        # Коррекция последнего маркера (последовательности после союза не было)
        if last_pos == 'CCONJ' or last_pos == 'ADP':
            x_labels[last_index] = ''

        return

    def getGenericTerm(self, segment):
        '''
        Преобразование последовательности в разложенный набор.
        Маркировка СУБЪЕКТА.
        '''
        result = None

        x_lables = []
        x_range = range(0, len(segment['morph']))
        x_labels = ['' for i in x_range]

        noun_cases = ['Nom', 'Acc', 'Voc']

        is_valid = False
        for index in x_range:
            token = segment['morph'][index]
            marker = 'I-SBJ'
            if token['pos'] == 'NOUN':
                case = self.shelper.getCase(token)
                if case in noun_cases:
                    marker = 'N-SBJ'
                    is_valid = True

            x_labels[index] = marker

        if is_valid:
            x_text = segment['text'].lower()
            result = {'range': x_range, 'labels': x_labels, 'text': x_text, 'seg_id': segment['id']}

        return result

    def getParentNP(self, morph, point_id, prefix = 'SBJ'):
        '''
        Извлечение ИГ из сегмента по точке привязки (существительному).
        ! Возможно расширение границ ИГ !
        '''
        result = ''
        NP_num = None
        point_index = 0
        point_pos = None
        for token in morph:
            if token['id'] == point_id:
                NP_num = token['mark']
                point_pos = token['pos']
                break
            point_index += 1

        # Generate NP`s description
        if NP_num:
            x_lables = []
            x_range = range(0, len(morph))
            x_labels = ['' for i in x_range]

            buffer = []

            # Experimental: дозаполнение левой части для числительного (ошибка чанкера!)
            # Sample: и образуют две [ параллельные линии коммутации входного тока ]
            cont_NP_num = None
            if point_pos == 'NUM':
                after_point_index = point_index + 1
                if after_point_index in x_range:
                    if morph[after_point_index]['mark'].isdigit():
                        cont_NP_num = morph[after_point_index]['mark']
            #--------------------------------------------------------------------------/

            np_start_index = None
            for index in x_range:
                # Начинаем заполнять только с самого СУЩ
                # Т.к. может вырываться из контекста
                if index < point_index:
                    continue

                token = morph[index]

                if token['mark'] == NP_num or token['mark'] == cont_NP_num:

                    if np_start_index == None:
                        np_start_index = index

                    if token['id'] == point_id:
                        x_labels[index] = 'N-' + prefix
                    else:
                        x_labels[index] = 'I-' + prefix

                    buffer.append(token['text'])

            # Маркировка ИГ слева от слова
            if point_pos != 'NUM':
                local_break_pos = ['ADV', 'ADP', 'NOUN']
                for index in reversed(x_range):
                    if index >= point_index:
                        continue
                    token = morph[index]

                    if token['pos'] in local_break_pos:
                        break

                    if token['mark'] == NP_num:
                        x_labels[index] = 'I-' + prefix
                        buffer.insert(0, token['text'])
                        np_start_index = index
                    else:
                        break

            # Отметка предлога перед ИГ
            #if np_start_index != None:
            #    if np_start_index > 0:
            #        befor_np_index = np_start_index - 1
            #        if morph[befor_np_index]['pos'] == 'ADP':
            #            x_labels[befor_np_index] = 'P-' + prefix
            #            buffer.insert(0, morph[befor_np_index]['text'])

            if len(buffer) > 0:
                x_text = ' '.join(buffer).lower()
                result = {'range': x_range, 'labels': x_labels, 'text': x_text, 'seg_id': -1}

        return result

    def splitTextByVerbIndex(self, text, morph, verb_index):
        verb_form = morph[verb_index]['text']
        parts = text.split(verb_form)
        part1 = parts[0].lower().strip()
        if len(parts)<=1:
            part2 = None
        else:
            part2 = parts[1].lower().strip()
        return (part1, part2)

    def checkNestedVerbs(self, morph):
        '''
        Проверка структуры V_V_N.
        Return: None | (<ext_verb_indx>,<int_verb_indx>)
        '''
        drop_pos = ['ADV']
        result = None
        mlen = len(morph)
        for index1 in range(0, mlen):
            token1 = morph[index1]
            # First verb
            if self.registry.isLemmaInCompDict(token1['lemma']) or \
            self.registry.isLemmaInConnDict(token1['lemma']):
                # Next verb
                is_find = False
                for index2 in range(index1+1, mlen):
                    token2 = morph[index2]
                    if token2['pos'] in drop_pos:
                        continue
                    if token2['pos'] == 'VERB':
                        result = (index1, index2)
                        is_find = True
                    break
                if is_find:
                    break

        return result
