import pprint as pp
import re

from tools.registry import DictRegistry
from tools.morphology.udpipetool import UdPipeTool
from tools.helpers.seghelper import SegmentHelper

# Обработчик свертки структуры
class ConvHandler(object):

    def __init__(self):
        self.udpipe = UdPipeTool()
        self.registry = DictRegistry()
        self.seghelper = SegmentHelper()
        self.PRINT_DEBUG = False

    def startConvolution(self, segments):

        # First - GAPs
        segments = self.collectGaps(segments)

        # Another processing
        segments = self.straightPassing(segments)

        # DEBUGGER ------------------------------------------------------------\
        if False:
            print("\nLinkers:")
            for segment in segments:
                if 'link' in segment:
                    print('{}\n{}\t{}\t{}\n'.format(segment['numbered'], segment['id'], segment['type'], str(segment['link'])))
            print('')
            #exit(0)
        #----------------------------------------------------------------------/


        return segments

    def straightPassing(self, segments):

        # Точки привязки (валентности) -----\
        # Last Compositional Verb (LCV)
        # LCV = (<segm_id>,<verb_id>)
        LCV = None
        # Last Active Verb (LAV)
        # LAV = (<segm_id>,<verb_id>,<n_case>)
        LAV = None
        #-----------------------------------/

        # Service vars
        last_part = segments[0]['part']
        last_type = segments[0]['type']

        seg_length = len(segments)
        last_index = seg_length - 1;

        for index in range(0, seg_length):
            segment = segments[index]

            self.can_print = segment['id'] == 188

            # Флаг смены части клейма
            is_another_part = last_part != segment['part']
            # Сегмент после явного разделителя (разные части клейма)
            is_after_sep =  is_another_part or \
                            last_type in ['SEPARATOR'] or \
                            segment['part'] == 2 and last_type == 'PURPOSE'

            # Clear LCV and LAV (?)
            if is_after_sep:
                LCV = None
                LAV = None

                # Separator marker for coreference
                segments[index]['after_sep'] = True
            # Experimenal depricated (19.02.19)
            #else:
            #    is_sep_begin = self.startsWithSep(segment, except_begins = ['а также'])
            #    if is_sep_begin:
            #        LCV = None

            # DEBUGGER ---------------------------------------\
            if self.PRINT_DEBUG:
                print(segment['id'])
                print(segment['segm'])
                print(segment['numbered'])

                pp.pprint(segment['template'])
                pp.pprint(segment['type'])
                #if 'tracking' in segment:
                #    pp.pprint(segment['tracking'])
                #pp.pprint(segment['morph'])
                #pp.pprint(tmp)
                if segment['id'] == 122:
                    pp.pprint(segment['morph'])
                    exit(0)

                if LCV:
                    segm = self.seghelper.getListIndexByVal(segments, 'id', LCV[0])
                    if segm:
                        word = self.getWordById(segm['morph'], LCV[1])
                        print("LCV [%s:%s] = '%s'" % (LCV[0], LCV[1], word))
                    else:
                        print("LCV = No segment")
                else:
                    print("LCV = None")

                if LAV:
                    segm = self.seghelper.getListIndexByVal(segments, 'id', LAV[0])
                    if segm:
                        word = self.getWordById(segm['morph'], LAV[1])
                        print("LAV [%s:%s] = '%s'" % (LAV[0], LAV[1], word))
                    else:
                        print("LCV = No segment")
                else:
                    print("LAV = None")

                print('\nVERBS::')
                if 'morph' in segment:
                    for token in segment['morph']:
                        if token['pos'] == 'VERB':
                            print("\n{} {} {}".format(token['id'], token['text'], token['lemma']))
                            pp.pprint(token['grammar'])

                print('')
                #continue
            #-------------------------------------------------/

            # Флаг успешной обработки сегмента (для отката на нейзвестный)
            is_succesful = False

            # Prepare Noun-phrases
            if segment['type'] == 'N':
                # Первая ИГ - название изобретения (независимая)
                if index == 0:
                    segment['link'] = {'type': 'self', 'parent': 0, 'point': None, 'child': None}
                    is_succesful = True
                elif 'link' not in segment:
                    # Привязка к LCV/LAV
                    first_noun = self.getFirstPOS(segment['morph'], 'NOUN')
                    if first_noun:
                        noun_gnc = self.seghelper.getGNC(first_noun)
                        noun_id = first_noun['id']

                        # Привязка по умолчанию к ближайшему слева предикату
                        if LAV and noun_gnc:
                            # + correction Gen-Nom Case (?)
                            is_connected = self.fuzzyCaseComparison(LAV[2], noun_gnc['Case'])
                            if self.can_print and False:
                                print(segment['text'])
                                pp.pprint(LAV)
                                pp.pprint(is_connected)
                                exit(0)

                            if is_connected:
                                segment['link'] = {'type': 'homo', 'parent': LAV[0], 'point': LAV[1], 'child': noun_id}
                                is_succesful = True

                        # Если не было привязки - более сильная валентность?
                        if not is_succesful and LCV:
                            segment['link'] = {'type': 'homo', 'parent': LCV[0], 'point': LCV[1], 'child': noun_id}
                            is_succesful = True

                # Maybe already connected
                elif segment['link']['type'] == 'self':
                    is_succesful = True

            # Participial turnover
            elif segment['type'] == 'V_N':

                # Part of GAP link (блок уже обработан)
                is_fin_verb = segment['template'].find("V<F>") == 0
                if is_fin_verb:
                    # Final actions
                    last_part = segment['part']
                    last_type = segment['type']
                    continue

                # Сочинительный союз разрывает привязку (?)
                # Пример: прокладка содержит ... основание, связывающее между собой эти ветви, и расположенный элемент удержания...
                if segment['template'].startswith('CC'):
                    if LAV:
                        segment['link'] = {'type': 'homo', 'parent': LAV[0], 'point': LAV[1], 'child': None}
                        is_succesful = True

                    if LCV and not is_succesful:
                        segment['link'] = {'type': 'homo', 'parent': LCV[0], 'point': LCV[1], 'child': None}
                        is_succesful = True

                    # Маркировка необработанных сегментов
                    if not is_succesful:
                        segment['link'] = {'type': 'unkn', 'parent': 0, 'point': None, 'child': None}

                    # Final actions
                    last_part = segment['part']
                    last_type = segment['type']
                    continue

                # Осуществлять ли привязку к N в конце (True, если не самостоятельный)
                is_v1_connection = not is_after_sep

                # Первый глагол
                verb_count = segment['template'].count("V")
                first_verb = self.getFirstPOS(segment['morph'], 'VERB')
                v1_gnc = self.seghelper.getGNC(first_verb)
                v1_id = first_verb['id']

                if verb_count <= 1:
                    # LAV rewrite
                    noun_gnc = self.findGNCOfSubnoun(segment['morph'], v1_id)
                    if noun_gnc:
                        LAV = (segment['id'], v1_id, noun_gnc['Case'])

                        # DEBUGGER -----------------\
                        if False:
                            print("LAV is:")
                            pp.pprint(LAV)
                        #---------------------------/

                        # Проверка на конструкцию V(мн.ч) N(ед.ч.)
                        next_seg_type = self.getTypeOfNextSegment(segments, index)
                        is_uniform = self.checkTemplate(segment['template'], "V_N_CC_N")

                        ### Refactoring required!!!
                        # Wrong detection on: размещенные в [ корпусе ] с [ образованием рабочих полостей ] => V<P>_N, but not homo
                        # C15_3.3
                        # Wrong detection on: электрически связанными с [ блоками управления и питания ]
                        # C15_10.16
                        # Fixed: del euristic from findGNCOfSubnoun

                        if self.can_print and False:
                            pp.pprint(first_verb)
                            pp.pprint(noun_gnc)
                            exit(0)

                        if v1_gnc['Number'] == 'Plur' and noun_gnc['Number'] == 'Sing' and next_seg_type == 'N' and not is_uniform:
                            is_succesful = True
                            is_v1_connection = False

                            # LCV(<segm_id>,<verb_id>)
                            if LCV:
                                segment['link'] = {'type': 'homo', 'parent': LCV[0], 'point': LCV[1], 'child': v1_id}
                            else:
                                segment['link'] = {'type': 'self', 'parent': 0, 'point': None, 'child': None}
                else:
                    # Check V_V_N scheme
                    is_doubled_v = self.checkTemplate(segment['template'], "V_V_N")

                    if is_doubled_v:

                        second_verb = self.getSecondPOS(segment['morph'], 'VERB')
                        v2_gnc = self.seghelper.getGNC(second_verb)
                        v2_id = second_verb['id']
                        noun_gnc = self.findGNCOfSubnoun(segment['morph'], v2_id)
                        # LAV rewrite
                        if noun_gnc:
                            LAV = (segment['id'], v2_id, noun_gnc['Case'])

                        '''
                        # Проверка на конструкцию V(мн.ч) N(ед.ч.)
                        next_seg_type = self.getTypeOfNextSegment(segments, index)
                        is_uniform = self.checkTemplate(segment['template'], "V_N_CC_N")
                        second_verb = self.getSecondPOS(segment['morph'], 'VERB')

                        if second_verb:
                            v2_gnc = self.seghelper.getGNC(second_verb)
                            v2_id = second_verb['id']
                            noun_gnc = self.findGNCOfSubnoun(segment['morph'], v2_id)

                            if v2_gnc['Number'] == 'Plur' and noun_gnc['Number'] == 'Sing' and next_seg_type == 'N' and not is_uniform:
                                is_succesful = True
                        '''

                    else:
                        # LAV rewrite
                        last_verb = self.getFirstPOS(segment['morph'], 'VERB', is_from_end = True)
                        vl_id =  last_verb['id']
                        noun_gnc = self.findGNCOfSubnoun(segment['morph'], vl_id)
                        if noun_gnc:
                            LAV = (segment['id'], vl_id, noun_gnc['Case'])

                # Если есть точка привязки и начало с разрыва (homo)
                first_mark = segment['morph'][0]['mark']
                if LCV and not is_succesful and first_mark == 'S':
                    # содержит..., а также избирательно управляемое нагревательное средство
                    segment['link'] = {'type': 'homo', 'parent': LCV[0], 'point': LCV[1], 'child': v1_id}
                    is_succesful = True
                    is_v1_connection = False

                # Если есть грамматическая инфа - ищем точку привязки в предыдущих сегментах
                if is_v1_connection and v1_gnc:

                    # DEBUGGER -------------------------------------------------\
                    if False and self.can_print:
                        #print(segment['segm'])
                        print("VERB '%s' is looking for..."%(first_verb['text']))
                        pp.pprint(v1_gnc)
                        print("")
                        #exit(0)
                    #-----------------------------------------------------------/

                    # Warning! is_accurate = False (не различает Вин/Род)
                    is_accurate = True
                    parent_seg_index, point = self.findNounPoint(segments, index, v1_gnc, spec_flag = is_accurate, search_type = 'part')

                    # Try without accurate
                    if parent_seg_index == None:
                        is_accurate = False
                        parent_seg_index, point = self.findNounPoint(segments, index, v1_gnc, spec_flag = is_accurate, search_type = 'part')

                    if self.can_print and False:
                        pp.pprint(parent_seg_index)
                        pp.pprint(point)
                        exit(0)

                    if parent_seg_index != None:

                        # DEBUGGER -----------------------------------------\
                        if False:
                            pp.pprint(segments[parent_seg_index]['segm'])
                            for item in segments[parent_seg_index]['morph']:
                                if item['id'] == point:
                                    print("Parent is '%s'"%(item['text']))
                                    parent_gnc = self.seghelper.getGNC(item)
                                    pp.pprint(parent_gnc)

                            exit(0)
                        #---------------------------------------------------/

                        # Привязка причастного оборота
                        segment['link'] = {'type': 'sub', 'parent': segments[parent_seg_index]['id'], 'point': point, 'child': v1_id}
                        is_succesful = True
                    else:
                        # Попытка привязаться к корню последнего NP
                        prev_seg_index = index-1
                        if v1_gnc['Number'] == 'Plur' and prev_seg_index >= 0:
                            prev_segment = segments[prev_seg_index]
                            last_np_group = self.getLastNPGroup(prev_segment)
                            if last_np_group:
                                np_in_str = self.assembleTokens2String(last_np_group)
                                udpipe_data = self.udpipe.analyzeText(np_in_str)
                                root_n = self.findRootNToken(udpipe_data)
                                if root_n:
                                    root_n = self.findCloneToken(prev_segment, root_n)
                                    # Присоединение к корню
                                    segment['link'] = {'type': 'sub', 'parent': prev_segment['id'], 'point': root_n['id'], 'child': v1_id}
                                    is_succesful = True

                                    # DEBUGGER -----------------------------------------\
                                    if False:
                                        pp.pprint(prev_segment['segm'])
                                        print("Parent is '%s'" % (root_n['text']))
                                        parent_gnc = self.seghelper.getGNC(root_n)
                                        pp.pprint(parent_gnc)
                                    #---------------------------------------------------/
                # Independent Segment
                elif is_after_sep:
                    segment['link'] = {'type': 'self', 'parent': 0, 'point': None, 'child': None}
                    is_succesful = True

                # Валентные глагол ------------------------------------------\
                if self.registry.isLemmaInCompDict(first_verb['lemma']):
                    verb_descr = self.registry.getCompVerb(first_verb['lemma'])
                    is_approved = verb_descr['approved']
                    if is_approved and not self.isPassiveVerb(first_verb):
                        #print("\n#LCV is : '{}' {}\n".format(first_verb['lemma'], str(first_verb['grammar'])))
                        LCV = (segment['id'], v1_id)
                        segment['LCV'] = LCV[1]
                        if self.PRINT_DEBUG:
                            print("HAS LCV")
                #------------------------------------------------------------/

            # Full segment
            elif segment['type'] == 'N_V_N':

                # Part of GAP link (блок уже обработан)
                if 'link' in segment:
                    if segment['link']['type'] == 'gap':
                        # Final actions
                        last_part = segment['part']
                        last_type = segment['type']
                        continue

                # Ищем LCV, но пока не перезаписываем
                maybe_LCV = self.findLCV(segment)
                verb_count = segment['template'].count("V")

                # LAV rewrite
                if verb_count == 1 and maybe_LCV != None:
                    # Можно скопировать с maybe_LCV
                    v_id = maybe_LCV[1]
                else:
                    # Warning!!! Default is_from_end = True (ошибка привязки 8.16)
                    last_verb = self.getFirstPOS(segment['morph'], 'VERB', is_from_end = False)
                    v_id = last_verb['id']

                noun_gnc = self.findGNCOfSubnoun(segment['morph'], v_id)
                if noun_gnc:
                    LAV = (segment['id'], v_id, noun_gnc['Case'])

                # LCV rewrite
                if maybe_LCV != None:
                    LCV = maybe_LCV
                    segment['LCV'] = LCV[1]
                    if self.PRINT_DEBUG:
                        print("HAS LCV")

                # Проверка на возможную ошибку определения сегмента
                if segment['template'].startswith('V<P>'):
                    first_verb = self.getFirstPOS(segment['morph'], 'VERB', is_from_end = False)
                    v_id = first_verb['id']
                    is_participle = self.isParentForPOS(segment['morph'], v_id, child_pos = 'ADV')
                    # У первого причастия есть зависимое наречие
                    if is_participle:
                        # Warning! is_accurate = False (не различает Вин/Род)
                        v_gnc = self.seghelper.getGNC(first_verb)
                        is_accurate = False
                        parent_seg_index, point = self.findNounPoint(segments, index, v_gnc, spec_flag = is_accurate, search_type = 'part')
                        if parent_seg_index != None:
                            # Привязка причастного оборота
                            segment['link'] = {'type': 'sub', 'parent': segments[parent_seg_index]['id'], 'point': point, 'child': v_id}
                            is_succesful = True


                # Default independed segment!!!
                if 'link' not in segment:
                    segment['link'] = {'type': 'self', 'parent': 0, 'point': None, 'child': None}
                    is_succesful = True

            # Separate definition (прилагательное)
            elif segment['type'] == 'A0':
                # Drop 'gap`s'
                if 'link' in segment:
                    if segment['link']['type'] == 'self':
                        last_part = segment['part']
                        last_type = segment['type']
                        continue

                temp = segment['template']
                # Привязка по GNC к существительному
                if temp.startswith('A0') or temp.startswith('A'):
                    first_adj = self.getFirstPOS(segment['morph'], 'ADJ')
                    a1_gnc = self.seghelper.getGNC(first_adj)
                    a1_id = first_adj['id']

                    # Поиск точки привязки
                    s_type = 'part'
                    is_accurate = False
                    parent_seg_index, point =   self.findNounPoint(segments,
                                                    index,
                                                    a1_gnc,
                                                    spec_flag = is_accurate,
                                                    search_type = s_type)
                    # Привязка
                    if parent_seg_index != None:
                        segment['link'] = {'type': 'sub', 'parent': segments[parent_seg_index]['id'], 'point': point, 'child': a1_id}
                        is_succesful = True

                # Иначе - самостоятельный сегмент
                elif ((temp.startswith('N0') or temp.startswith('N')) and temp.endswith('A0')):
                    segment['link'] = {'type': 'self', 'parent': 0, 'point': None, 'child': None}
                    is_succesful = True

            # Относительно самостоятельные
            elif (segment['type'] == 'N_который_V_N' or segment['type'] == 'который_V_N'):

                which_token = self.getWhichWord(segment)
                which_gnc = self.seghelper.getGNC(which_token)
                which_id = which_token['id']

                #pp.pprint(which_gnc)

                # Поиск точки привязки
                s_type = 'which'
                is_reversed = True
                parent_seg_index, point =   self.findNounPoint(segments,
                                                index,
                                                which_gnc,
                                                spec_flag = is_reversed,
                                                search_type = s_type)

                # Привязка (can be 0)
                if parent_seg_index != None:
                    segment['link'] = {'type': 'spec', 'parent': segments[parent_seg_index]['id'], 'point': point, 'child': which_id}
                    is_succesful = True

                # Rewrite LAV
                last_verb = self.getFirstPOS(segment['morph'], 'VERB', True)
                if last_verb:
                    v_id = last_verb['id']
                    noun_gnc = self.findGNCOfSubnoun(segment['morph'], v_id)
                    if noun_gnc:
                        LAV = (segment['id'], v_id, noun_gnc['Case'])

            # Предложения с тире
            elif segment['type'] == 'N_-_N':
                # Привязка только к предыдущему сегменту (0й должен быть)
                if index > 0:
                    prev_index = index - 1
                    if segments[prev_index]['type'] not in self.registry.drop_segments:
                        # Может быть описние формулы: ..., где Х - параметр
                        if segment['template'].find('X') >= 0:
                            segment['link'] = {'type': 'spec', 'parent': segments[prev_index]['id'], 'point': None, 'child': None}
                            is_succesful = True
                        # Или тип с пропущенным глаголом
                        elif LAV:
                            segment['link'] = {'type': 'dupl', 'parent': LAV[0], 'point': LAV[1], 'child': None}
                            is_succesful = True

            # Сравнительные обороты
            elif segment['type'] == 'AV':
                # По умолчанию привязка к последнему сегменту
                prev_seg = self.getPrevSegment(segments, index)
                if prev_seg:
                    segment['link'] = {'type': 'comp', 'parent': prev_seg['id'], 'point': None, 'child': None}
                    is_succesful = True

            # Сложноподчиненные
            elif segment['type'] == 'SC':
                # По умолчанию привязка к последнему сегменту
                prev_seg = self.getPrevSegment(segments, index)
                if prev_seg:
                    segment['link'] = {'type': 'sub', 'parent': prev_seg['id'], 'point': None, 'child': None}
                    is_succesful = True

            # Деепричастие
            elif segment['type'] == 'V<C>':
                # Привязываемся к сегменту с V<Fin>
                parent_seg_index, point = self.findFinVerbPoint(segments, index)
                if parent_seg_index != None:
                    segment['link'] = {'type': 'gerund', 'parent': segments[parent_seg_index]['id'], 'point': point, 'child': None}
                    is_succesful = True

            # Цель
            elif segment['type'] == 'PURPOSE':

                # Check first on Verb
                is_part_form = False
                if 'morph' in segment:
                    maybe_verb = self.getFirstPOS(segment['morph'], "VERB")
                    if maybe_verb:
                        is_part_form = maybe_verb['lemma'] == 'предназначать'

                # Для случая "Прокладка, предназначенная для ..."
                if is_part_form:
                    v_gnc = self.seghelper.getGNC(maybe_verb)
                    v_id = maybe_verb['id']

                    is_accurate = False
                    parent_seg_index, point = self.findNounPoint(segments, index, v_gnc, spec_flag = is_accurate, search_type = 'part')
                    if parent_seg_index != None:
                        segment['link'] = {'type': 'spec', 'parent': segments[parent_seg_index]['id'], 'point': point, 'child': None}
                        is_succesful = True

                    # Прикрепление к последнему сегменту принудительно
                    else:
                        prev_segm = self.getPrevSegment(segments, index)
                        if prev_segm:
                            segment['link'] = {'type': 'spec', 'parent': prev_segm['id'], 'point': None, 'child': None}
                            is_succesful = True

                # Прикрепление к следующему сегменту
                else:
                    next_index = index + 1
                    if next_index <= last_index:
                        segment['link'] = {'type': 'spec', 'parent': segments[next_index]['id'], 'point': None, 'child': None}
                        is_succesful = True

            # Псевдоним
            elif segment['type'] == 'NAMED':
                # Механизм подключения причастного оборота
                first_verb = self.getFirstPOS(segment['morph'], 'VERB')
                v1_gnc = self.seghelper.getGNC(first_verb)
                v1_id = first_verb['id']

                is_accurate = False
                parent_seg_index, point = self.findNounPoint(segments, index, v1_gnc, spec_flag = is_accurate, search_type = 'part')
                if parent_seg_index != None:
                    # Привязка причастного оборота
                    segment['link'] = {'type': 'named', 'parent': segments[parent_seg_index]['id'], 'point': point, 'child': v1_id}
                    is_succesful = True

            # Маркировка необработанных сегментов
            if not is_succesful:
                segment['link'] = {'type': 'unkn', 'parent': 0, 'point': None, 'child': None}

            # Final actions
            last_part = segment['part']
            last_type = segment['type']

            # DEBUGGER ---------------------------\
            if self.PRINT_DEBUG:
                if 'link' in segment:
                    pp.pprint(segment['link'])
                    print('\n')
            #-------------------------------------/

        #exit(0)
        return segments

    def findFinVerbPoint(self, segments, child_seg_index):
        """
        Find V<F> for child V<C> [ Seg(...), Seg(...N[gnc]...N), Seg(...V[gnc]...N) ]
        """
        target_part = segments[child_seg_index]['part']
        parent_seg_index = None
        point = None
        scope = reversed(range(0, child_seg_index))

        for index in scope:
            segment = segments[index]

            if segment['part'] != target_part:
                break

            if segment['type'] in self.registry.drop_segments:
                continue

            # Поиск активного клагола
            for token in reversed(segment['morph']):
                if token['pos'] == 'VERB':
                    if 'grammar' in token:
                        if 'VerbForm' in token['grammar']:
                            if token['grammar']['VerbForm'] == 'Fin':
                                point = token['id']
                                break

            if point != None:
                parent_seg_index = index
                break

        return parent_seg_index, point

    def getPrevSegment(self, segments, base_index):
        """
        Previous conjugate segment (not separator)
        """
        result = None
        prev_index = base_index - 1
        if prev_index >= 0 and prev_index < len(segments):
            if segments[base_index]['part'] == segments[prev_index]['part'] and \
            segments[prev_index]['type'] not in self.registry.drop_segments:
                result = segments[prev_index]
        return result

    def isParentForPOS(self, morph, parent_id, child_pos):
        result = False
        for token in morph:
            if token['parent'] == parent_id and token['pos'] == child_pos:
                result = True
                break
        return result

    def startsWithSep(self, segment, except_begins = ['а также']):
        """
        Check if segment starts with separator (а так же, при этом...)
        """
        result = False
        if 'morph' in segment:
            if 'mark' in segment['morph'][0]:
                # Начинается ли с сепаратора
                result = segment['morph'][0]['mark'] == 'S'
                # Возможна отмена по исключению
                if result:
                    for excpt in except_begins:
                        if segment['text'].startswith(excpt):
                            result = False
        return result

    def getWhichWord(self, segment):
        """
        Find 'который' word
        """
        result = None
        if 'morph' in segment:
            for token in segment['morph']:
                if token['lemma'] == 'который':
                    result = token
                    break
        return result

    def findLCV(self, segment):
        """
        Get first VERB
        """
        result = None
        if 'morph' in segment:
            for token in segment['morph']:
                if token['pos'] == 'VERB' and self.registry.isLemmaInCompDict(token['lemma']):
                    verb_descr = self.registry.getCompVerb(token['lemma'])
                    is_approved = verb_descr['approved']
                    if is_approved:
                        result = (segment['id'], token['id'])
                        break
        return result

    def isPassiveVerb(self, verb):
        """
        For adjective verb`s (включенный...)
        """
        result = False
        grammar = verb['grammar']
        if 'Aspect' in grammar and 'Voice' in grammar:
            result = grammar['Aspect'] == 'Perf' and grammar['Voice'] == 'Pass'

        return result

    # DEBUGGER
    def getWordById(self, morph, id):
        result = None
        for token in morph:
            if token['id'] == id:
                result = token['text']
                break
        return result

    def checkTemplate(self, template, pattern_type):
        result = False
        if pattern_type == "V_N_CC_N":
            pattern = r'V<.>_N0?_CC_N0?'
        elif pattern_type == "V_V_N":
            pattern = r'V<.>_V<.>_(N0?|PR0?)'
        else:
            print("Internal error: wrong pattern.\n")
            exit(0)

        if re.search(pattern, template):
            result = True

        return result

    def getTypeOfNextSegment(self, segments, cur_seg_index):
        result = None
        next_index = cur_seg_index + 1
        if next_index < len(segments):
            result = segments[next_index]['type']
        return result

    def findGNCOfSubnoun(self, morph, verb_id):
        """
        Get context noun case for linking
        ... выполненный<verb_id> на [ основе<noun_id, Case=Loc> поляризованного электромагнитного реле ] => Loc
        Maybe looking for root of NP ?
        """
        allowed_pos = ['NOUN', 'PRON', 'ADJ']
        result = None
        for token in morph:
            if int(token['id']) <= int(verb_id):
                continue

            #if self.can_print:
            #    print(token['text'])

            # Warn!!! электрически связанными с [ блоками управления и питания ] not passed
            # But need:
            # - and (token['deprel'] != 'obl' and token['parent'] != verb_id):
            if token['pos'] in allowed_pos:
                result = self.seghelper.getGNC(token)
                break

        return result

    def findCloneToken(self, segment, target_token):
        result = None
        for token in segment['morph']:
            if token['text'] == target_token['text']:
                result = token
        return result

    def findRootNToken(self, morph):
        result = None
        for token in morph:
            if token['pos'] == 'NOUN' and token['parent'] == '0':
                result = token
                break
        return result

    def assembleTokens2String(self, tokens):
        result = ""
        for token in tokens:
            result += token['text'] + " "
        return result.rstrip()

    def getLastNPGroup(self, segment):
        """
        Get NP tokens[1 O O O 3 3 3]: return last 3`s tokens
        """
        result = []
        if segment['type'] in self.registry.drop_segments:
            return result

        last_index = len(segment['morph']) - 1
        np_num = segment['morph'][last_index]['mark']

        if np_num.isdigit():
            for token in segment['morph']:
                if np_num == token['mark']:
                    result.append(token)

        return result

    def findNounPoint(self, segments, child_seg_index, target_gnc, spec_flag = True, search_type = 'part'):
        """
        Find N for child V [ Seg(...), Seg(...N[gnc]...N), Seg(...V[gnc]...N) ]
        :param:child_seg_index: index of child segment
        :param:target_gnc: for compare
        :param:spec_flag: is_accurate or is_reversed
        :param:con_type: type of searching: 'part' - for participle; 'which' - for 'который'
        :return: parent_seg_index, token_id (N; point)
        """
        target_part = segments[child_seg_index]['part']
        parent_seg_index = None
        point = None
        scope = reversed(range(0, child_seg_index))

        for index in scope:
            segment = segments[index]

            if segment['part'] != target_part:
                break

            if segment['type'] in self.registry.drop_segments:
                continue

            if search_type == 'part':
                point = self.findNoun4Part(segment['morph'], target_gnc, spec_flag)

            elif search_type == 'which':
                point = self.findNoun4Which(segment['morph'], target_gnc, spec_flag)

            if point:
                parent_seg_index = index
                break

        return parent_seg_index, point

    def findNoun4Which(self, morph, target_gnc, is_reversed = False):
        """
        Search noun for which by Number and Gender
        Sample: Разрывной разъединитель[gn], ..., в котором[gn] используются разрушающие элементы
        """
        point = None
        scope = range(0, len(morph))

        if is_reversed:
            scope = reversed(scope)

        candidates = []

        for index in scope:
            token = morph[index]
            if token['pos'] == "NOUN":
                current_gnc = self.seghelper.getGNC(token)
                if current_gnc:
                    #print(current_gnc)
                    if current_gnc['Number'] == target_gnc['Number'] and \
                     (current_gnc['Gender'] == target_gnc['Gender'] or current_gnc['Number'] == 'Plur'):
                        #print("\n#Checked '{}' on {}\n".format(token['text'], str(current_gnc)))
                        candidates.append((token['id'], token['parent'], token['deprel']))
                        #point = token['id']
                        #break
            # Experimenal
            #elif token['pos'] == "ADP" and len(candidates) > 0:
            #    break

        candidates_len = len(candidates)
        if candidates_len == 1:
            point = candidates[0][0]
        elif candidates_len > 1:

            #if self.can_print:
            #    pp.pprint(candidates)

            can_be_point = []
            x_range = range(0, candidates_len)
            for x in x_range:
                current_id = candidates[x][0]

                if candidates[x][2] == 'conj':
                    can_be_point.append(current_id)
                    continue

                is_child = False
                parent_id = candidates[x][1]

                y_range = range(x+1, candidates_len)
                for y in y_range:

                    checked_id = candidates[y][0]

                    #if self.can_print:
                    #    print("Compare {} on {}\n".format(checked_id, parent_id))

                    if checked_id == parent_id:
                        is_child = True
                        break
                if not is_child:
                    can_be_point.append(current_id)

            if len(can_be_point) > 0:
                #if self.can_print:
                #    pp.pprint(can_be_point)
                #    exit(0)

                point = can_be_point[0]

        return point

    def fuzzyCaseComparison(self, current_gnc, target_gnc):
        """
        Нечеткое сравнение падежей.
        """
        if not current_gnc or not target_gnc:
            return False

        is_connected = False

        combined_cases = [
            ['Acc', 'Gen'],
            ['Acc', 'Nom'],
            ['Loc', 'Ins'], # Unreliably!!!
        ]

        # Не различаем Вин/Род; Им/Вин
        for inaccurate in combined_cases:
            if current_gnc in inaccurate:
                is_connected = target_gnc in inaccurate
                if is_connected:
                    break

        return is_connected

    def findNoun4Part(self, morph, target_gnc, is_accurate = True):
        """
        Search noun for participle by GN(C)
        Search noun for which by Number and Gender
        Sample: Разрывной разъединитель[gn], ..., в котором[gn] используются разрушающие элементы
        """
        point = None
        if not target_gnc:
            return None

        #print("Accurancy: {}".format(str(is_accurate)))

        target_poses = ['NOUN', 'NUM']

        scope = reversed(range(0, len(morph)))
        for index in scope:
            token = morph[index]
            if token['pos'] in target_poses:
                current_gnc = self.seghelper.getGNC(token)

                if current_gnc:
                    # Число совпадает при любом случае
                    if (current_gnc['Number'] == target_gnc['Number']) or \
                    (target_gnc['Number'] == 'Plur' and not is_accurate):

                        #if self.can_print:
                        #print("\n#Checked '{}' on {}\n".format(token['text'], str(current_gnc)))

                        is_gend_similar = current_gnc['Gender'] == target_gnc['Gender']
                        # Cредний род глагола (можно привязать к мужскому)
                        if not is_gend_similar:
                            is_gend_similar = target_gnc['Gender'] == 'Neut' and current_gnc['Gender'] == 'Masc'
                        # Experimantal:
                        if not is_gend_similar and is_accurate:
                            is_gend_similar = target_gnc['Number'] == 'Plur' and target_gnc['Gender'] == None

                        is_case_similar = current_gnc['Case'] == target_gnc['Case']

                        # Допускается ли ошибка перепутывания Вин/Род --------------------------------\
                        is_connected = False

                        if is_accurate:
                            is_connected = is_case_similar and is_gend_similar
                        else:
                            # Гибкое сравнение по падежам при совпадающем роде
                            if is_gend_similar or target_gnc['Gender'] == None: # and target_gnc['Gender'] != None:
                                # Не различаем Вин/Род; Им/Вин
                                is_connected = self.fuzzyCaseComparison(current_gnc['Case'], target_gnc['Case'])

                            # При множественном числе допускается пересечение Case/Number (рода может не быть)
                            if not is_connected and current_gnc['Number'] == 'Plur':
                                is_connected = is_case_similar and target_gnc['Case'] != None

                            # У кратких форм может не быть падежа
                            # Experimental: Попытка привязать совпадающие Род/Падеж при Им.п. объекта...
                            if not is_connected and target_gnc['Case'] == None:
                                is_connected = current_gnc['Case'] == 'Nom' and is_gend_similar

                            # Прямое сравнение
                            if not is_connected:
                                is_connected = current_gnc['Case'] == target_gnc['Case']

                        if is_connected:
                            point = token['id']
                            break;

        return point

    def collectGaps(self, segments):
        """
        Reverse pass for N,...,V<F>_N collection
        """
        seg_len = len(segments)
        scope = reversed(range(0, seg_len))

        prev_part = segments[seg_len-1]['part']
        for index in scope:
            segment = segments[index]

            if segment['template'].startswith('V<F>') and \
            (segment['type'] == 'V_N' or segment['type'] == 'N_V_N' or segment['type'] == 'который_V_N'):


                # Drop after separator -------------------------------------\
                # Возможно нужна расширенная проверка, как в основном цикле
                before_index = index - 1
                if before_index >= 0:
                    if segments[before_index]['part'] != prev_part or \
                    segments[before_index]['type'] == 'SEPARATOR':
                        # Mark as 'self!'
                        segments[index]['link'] = {'type': 'self', 'parent': 0, 'point': None, 'child': None}
                        prev_part = segments[before_index]['part']
                        continue
                #----------------------------------------------------------/

                point_pair = self.findGapParent(segments, index)

                if point_pair != None:
                    # DEBUGGER ------------------------------------------------\
                    if False:
                        print("\nGAP from N(%s) to V<F>(%s)" % (id_pair, index))
                        print(segments[noun_index]['segm'])
                        print(segments[index]['segm'])
                        print("")
                    #----------------------------------------------------------/

                    # Mark parts of GAP-link
                    parent_index = point_pair[0]
                    segments[index]['link'] = {'type': 'gap', 'parent': segments[parent_index]['id'], 'point': point_pair[1], 'child': None}
                    segments[parent_index]['link'] = {'type': 'self', 'parent': 0, 'point': None, 'child': None}
                    segments[parent_index]['used'] = True
                else:
                    segments[index]['link'] = {'type': 'unkn', 'parent': 0, 'point': None, 'child': None}

            prev_part = segment['part']

        #exit(0)
        return segments

    def findGapParent(self, segments, base_index):
        """
        Find N in reversed segments (12 {11}(V<F>) 10 9 8(N)... 0)
        param: start_index: {11}
        return: None | (<seg_index>,<token_id>)
        """
        result = None
        allowed_segm_types = ['N', 'A0', 'SC']

        start_index = base_index - 1
        # Bordering segment cannot be part of gap
        if start_index - 1 < 0:
            return result

        scope = reversed(range(0, start_index))
        base_part = segments[base_index]['part']

        for segm_index in scope:
            segment = segments[segm_index]

            # Another part is depricated
            cur_part = segment['part']
            if cur_part != base_part:
                break

            # Find N or A0 with N
            if segment['type'] in allowed_segm_types:
                # В независимой части должен быть N<Nom>!
                token_id = self.seghelper.findCaseInSegment(segment, ['NOUN'], ['Nom'])
                if token_id != None:
                    result = (segm_index, token_id);
                    break

        return result

    def getFirstPOS(self, morph, pos, is_from_end = False):
        """
        Find first POS in morphology of segment
        """
        result = None
        scope = range(len(morph))

        if is_from_end:
            scope = reversed(scope)

        for index in scope:
            token = morph[index]
            if token['pos'] == pos:
                result = token
                break
        return result

    def getSecondPOS(self, morph, pos):
        result = None
        first_pos = False
        for token in morph:
            if token['pos'] == pos:
                if first_pos:
                    result = token
                    break
                else:
                    first_pos = True
        return result
