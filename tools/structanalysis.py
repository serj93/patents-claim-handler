import pprint as pp
import copy

from tools.registry import DictRegistry
from tools.helpers.seghelper import SegmentHelper
from tools.morphology.pymorphytool import PymorphyTool
from tools.idpostproc import IDPostProcessor
from tools.extractor import SAOExtractor
from tools.pluginmaster import PluginMaster

# Генератор элементов графа
class StructuralAnalysis(object):

    def __init__(self):
        self.registry = DictRegistry()
        self.shelper = SegmentHelper()
        self.pmtool = PymorphyTool()
        self.postproc = IDPostProcessor()
        self.extractor = SAOExtractor()
        self.plmaster = PluginMaster()

    def getDesignFeatures(self, segments, replacements, generic_term, triplets):
        """
        Запуск постобработки первичных клеймов
        """

        # Промежуточная форма обработки триплетов
        self.p_triplets = []

        counter = 0
        for triplet in triplets:
            counter += 1

            self.labelCorrection(triplet, segments, 'SBJ')
            self.labelCorrection(triplet, segments, 'OBJ')

            p_triplet = self.prepareTriplet(triplet, segments)
            if p_triplet:
                self.p_triplets.append(p_triplet)

        invent_data = None
        if self.p_triplets:
            invent_data = self.pTripletsConvolution(
                self.p_triplets,
                segments,
                replacements,
                generic_term
            )

            invent_data = self.postproc.dataPostProcessing(invent_data)

        return invent_data

    def pTripletsConvolution(self, p_triplets, segments, replacements, generic_term):
        """
        Глобальная свертка триплетов
        """
        # Результат работы
        invent_data = {}

        # Словарь терминов:
        #{'0.0': 'рекурсивный цифровой фильтр' }
        # Fixed keys: '0.0' - Родовое понятие (РП)
        invent_data['terms'] = self.generateRoot(generic_term, segments)
        invent_data['generic_term'] = generic_term

        # Словарь связей:
        #{'1':
        #    {'text': 'соединять',
        #     'type': 'conn' | 'comp',
        #     'prep':
        #       {1: 'c'}}}
        # Fixed keys:
        #   '0.0' - Неявное отношения потомка к родителю
        #           Пример: статор..., полые цилиндры статора ...
        invent_data['verbs'] = {
            '0.0': {'text': 'have', 'type': 'have', 'prep': {}}
        }

        # Карта связей:
        #{<sbj_key>:
        #    {<obj_key>:
        #       (<verb_key>, <prefix_key>)}}
        invent_data['map'] = {}

        # Служебный словарь ссылок на глобальные индексы термов
        invent_data['refs'] = {}

        self.can_print = False
        self.counter = 0

        p_range = range(0, len(p_triplets))
        for i in p_range:
            # Добавление термов и связей в буфер;
            # Обновление после успешного прохождения всех частей.

            pre_data_sbj = self.prepareConcepts(segments, invent_data, p_triplets, i, 'SBJ')
            if pre_data_sbj['points'] or pre_data_sbj['terms']:
                # + Проверка на replacements
                self.updateInventTermsAndMap(invent_data, pre_data_sbj)
                del pre_data_sbj['terms']

                pre_data_obj = self.prepareConcepts(segments, invent_data, p_triplets, i, 'OBJ')
                if pre_data_obj['points'] or pre_data_obj['terms']:
                    p_triplet = p_triplets[i]
                    # Инвертировать ли направление sbj->obj
                    is_reversed = 'reversed' in p_triplet['ACT']

                    # + Проверка на replacements
                    self.updateInventTermsAndMap(invent_data, pre_data_obj)
                    del pre_data_obj['terms']

                    # Должен вернуть "координаты" слова couple(<verb_index>, <prep_index>)
                    verb_key = self.updateInventVerbs(invent_data, p_triplet['ACT'])
                    verb_type = invent_data['verbs'][verb_key[0]]['type']

                    # Проверка ref и необходимости генерации связок
                    # между obj на соединенные

                    # Генерация связей между точками
                    for sbj_point in pre_data_sbj['points']:
                        for obj_point in pre_data_obj['points']:

                            # Reverse links
                            if (obj_point == '0.0' and verb_type == 'comp') or is_reversed:
                                point1 = obj_point
                                point2 = sbj_point
                            else:
                                point1 = sbj_point
                                point2 = obj_point

                            # Create item
                            if point1 not in invent_data['map']:
                                invent_data['map'][point1] = {}

                            invent_data['map'][point1][point2] = verb_key

        return invent_data

    def updateInventVerbs(self, invent_data, verb):
        """
        Обновление словаря глаголов с буфера.
        Нормализация словоформы и выяснение типа глагола!
        """
        # Словарь связей:
        #{'2.3':
        #    {'text': 'соединять',
        #     'type': 'conn' | 'comp',
        #     'prep':
        #       {0: None,
        #        1: 'c'}}}

        verb_text = verb['text']

        if verb_text in self.registry.verbs_synonyms:
            verb_text = self.registry.verbs_synonyms[verb_text]

        # Проверка наличия глагола в словаре
        verb_key = self.checkVerbInDict(invent_data['verbs'], verb_text)
        prep_key = 0
        # Просмотр префикса
        if verb_key:
            if verb['prep']:
                if verb['prep'] in self.registry.univers_preps:
                    verb['prep'] = self.registry.univers_preps[verb['prep']]

                prep_key = self.checkPrepInVerb(
                    invent_data['verbs'][verb_key]['prep'],
                    verb['prep']
                )

                if not prep_key:
                    keys_list = list(invent_data['verbs'][verb_key]['prep'].keys())
                    if len(keys_list) >= 1:
                        prep_key = keys_list[-1] + 1
                    else:
                        prep_key = 1

                    invent_data['verbs'][verb_key]['prep'][prep_key] = verb['prep']

        # Вставка глагола с нуля
        else:
            verb_key = verb['key']

            if self.registry.isLemmaInCompDict(verb_text):
                verb_type = 'comp'
            else:
                verb_type = 'conn'

            insert = {}
            insert['text'] = verb_text
            insert['type'] = verb_type
            insert['prep'] = {}

            if verb['prep']:
                if verb['prep'] in self.registry.univers_preps:
                    verb['prep'] = self.registry.univers_preps[verb['prep']]
                prep_key = 1
                insert['prep'][prep_key] = verb['prep']

            invent_data['verbs'][verb_key] = insert

        return (verb_key, prep_key)

    def checkPrepInVerb(self, preps, prep_text):
        """
        Проверка наличия предлога в структуре.
        """
        result = None
        for key, item in preps.items():
            if item == prep_text:
                result = key
                break

        return result

    def checkVerbInDict(self, verbs, verb_text):
        """
        Обход словаря на поиск глагола.
        """
        result = None
        for key, item in verbs.items():
            if item['text'] == verb_text:
                result = key
                break
        return result

    def updateInventTermsAndMap(self, invent_data, pre_data):
        """
        Обновление словарей понятий с буферов.
        Обновление карты свзей (псевдосвязи have).
        """
        if pre_data['terms']:
            for root_key, term in pre_data['terms'].items():
                pre_data['points'].append(root_key)
                invent_data['terms'][root_key] = copy.copy(term)

        if pre_data['map']:
            #{<sbj_key>:
            #    {<obj_key>:
            #       (<verb_key>, <prefix_key>)}}
            for sbj_key, links in pre_data['map'].items():
                if sbj_key not in invent_data['map']:
                    invent_data['map'][sbj_key] = {}

                for obj_key, couple  in links.items():
                    invent_data['map'][sbj_key][obj_key] = copy.copy(couple)

        return

    def prepareConcepts(self, segments, invent_data, p_triplets, p_index, xkey):
        """
        Выделение концептов и возвращение предварительных связок.
        Поиск в глобальном хранилище.
        """
        pre_data = {}
        pre_data['terms'] = {}      # Аналог термов (для новых неподтвержденных)
        pre_data['map'] = {}        # Точки привязки, для порождения всевдосвязей (have)
        pre_data['points'] = []     # Точки привязки, которые есть в глобальном хранилище

        pseudo_verb_key = '0.0'

        concepts = p_triplets[p_index][xkey]
        for concept in concepts:
            concept_type = self.detectConcepType(concept)

            # For add new concept
            root_key = concept['root']

            # Concept 1 (simple)
            if concept_type == 1:

                if self.isDepricatedConcept(concept):
                    continue

                self.counter += 1
                parents = []

                #print("\n#" + str(self.counter))
                #print(">> START: '{}'".format(concept['text']))
                #print("1) Init text: " + concept['init_text'])
                #print("2) Root key : " + str(concept['root']))

                global_point = self.searchConceptInGlobal(concept, invent_data)

                #print("3) Global pt: " + str(global_point))

                if global_point:
                    # Update references ---------------------------------------\
                    if global_point != root_key:
                        if global_point not in invent_data['refs']:
                            invent_data['refs'][global_point] = []
                        if root_key not in invent_data['refs'][global_point]:
                            invent_data['refs'][global_point].append(root_key)
                    #----------------------------------------------------------/
                    pre_data['points'].append(global_point)
                    continue

                #print("4) Gent tail: " + str(concept['gent_tail']))
                #print("   Gent form: " + str(concept['gent_form']))

                # Есть хвост - искать родителя
                if concept['gent_tail']:

                    parents, gent_tail = self.searchGentTail(concept['gent_tail'], p_triplets, p_index)

                    # Refrash gent_tail
                    concept['gent_tail'] = gent_tail

                # Добавление во временной словарь (хвоста нет?)
                norm_form = concept['norm_form']

                #print("5) Normal 1 : " + str(norm_form))

                # Могут быть остатки даже без true gent_tail
                if concept['gent_tail']:
                    norm_form += ' ' + concept['gent_tail']

                #print("6) Normal 2 : " + str(norm_form))

                # Добавление терма в любом случае (был родитель или нет);
                # Точка независимая; дубликаты устанятся позже!
                pre_data['terms'][root_key] = norm_form

                # Порождение новых связей (псевдосвязей)
                if parents:
                    # Карта связей:
                    #{<sbj_key>:
                    #    {<obj_key>:
                    #       (<verb_key>, <prefix_key>)}}
                    for p_key in parents:
                        ### Проверка ключа на глобальность!!!
                        if p_key not in invent_data['terms']:
                            p_key = self.getGlobalPoint(p_key, invent_data['refs'])

                        if p_key:
                            if p_key not in pre_data['map']:
                                pre_data['map'][p_key] = {}

                            pre_data['map'][p_key][root_key] = (pseudo_verb_key, 0)

                #print("FINISH.\n")

            # Concept 2 (pron)
            elif concept_type == 2:
                # Привязка к родовому понятию
                global_point = '0.0'

                # Depricated
                #if 'after_sep' in concept:
                #    pre_data['points'].append(global_point)
                #    continue

                # Проверка совпадения Числа и Рода PRON с РП
                if invent_data['generic_term']:
                    parent_gnc = invent_data['generic_term']['parent_gnc']
                    if parent_gnc:

                        token = self.getRootToken(concept)
                        if token['pos'] != 'PRON':
                            # Additional PRON check ------------------------\
                            p = self.pmtool.analyzeWord(token['text'])
                            try:
                                if 'NPRO' not in p.tag:
                                    continue
                            except:
                                continue
                            #-----------------------------------------------/

                        anafor_gnc = self.shelper.getGNC(token)

                        if parent_gnc['Gender'] == anafor_gnc['Gender'] and \
                        parent_gnc['Number'] == anafor_gnc['Number']:
                            pre_data['points'].append(global_point)

                        continue

            # Concept 3 (which 1: N_которого)
            elif concept_type == 3:

                if self.isDepricatedConcept(concept):
                    continue

                # Добавить основную связку в набор (gent_tail нет)
                pre_data['terms'][root_key] = concept['norm_form']

                if not concept['which1']['parent'] or not concept['which1']['point']:
                    continue

                # Найти родителя связки (которого)
                p_key = str(concept['which1']['parent']) + '.' + concept['which1']['point']

                # Может быть в ссылках
                maybe_p_key = self.getGlobalPoint(p_key, invent_data['refs'])
                if maybe_p_key:
                    p_key = maybe_p_key

                # Уровень 1: глобальный словарь терминов
                if p_key in invent_data['terms']:

                    # Порождение новых связей (псевдосвязей)
                    if p_key not in pre_data['map']:
                        pre_data['map'][p_key] = {}

                    pre_data['map'][p_key][root_key] = (pseudo_verb_key, 0)

                # Уровень 2: поиск по триплетам и перенос точки на вершину ИГ
                else:
                    parent_concept = self.searchConceptOfPoint(p_key, p_triplets, p_index)
                    if parent_concept:
                        # Проверка попадания в родительскую ссылку
                        # Sample:
                        # 'к первому и второму выходам делителя мощности'
                        # ['I-OBJ', 'I-OBJ', 'I-OBJ', 'N-OBJ', 'I-GEN', 'I-GEN']
                        # ['6.43', '6.44', '6.45', '6.46', '6.47', '6.48']
                        # p_key = 6.47
                        p_index = parent_concept['nums'].index(p_key)
                        if parent_concept['labels'][p_index] == 'I-GEN':
                            parts = []
                            t_range = range(0, len(parent_concept['tokens']))
                            for i in t_range:
                                if parent_concept['labels'][i] == 'I-GEN':
                                    parts.append(parent_concept['tokens'][i]['text'])

                            # Есть хвост - искать родителя
                            if parts:
                                full_gent = " ".join(parts)
                                parents, gent_tail = self.searchGentTail(full_gent, p_triplets, p_index)
                                # Хвост полностью съеден и найден родитель
                                if parents and not gent_tail:
                                    # Порождение новых связей (псевдосвязей)
                                    for parent_key in parents:
                                        if parent_key not in pre_data['map']:
                                            pre_data['map'][parent_key] = {}

                                        pre_data['map'][parent_key][root_key] = (pseudo_verb_key, 0)

                                    # Necessarily drop
                                    continue

                        # Перенос на вершину ИГ (implicit ELSE branch)
                        ref_p_key = parent_concept['root']
                        if ref_p_key not in invent_data['terms']:
                            # Добавление во временной словарь
                            norm_form = concept['norm_form']
                            if concept['gent_tail']:
                                norm_form += ' ' + concept['gent_tail']
                            #WARN!!! Без поиска gent_tail.
                            pre_data['terms'][ref_p_key] = norm_form

                        # Порождение новых связей (псевдосвязей)
                        if ref_p_key not in pre_data['map']:
                            pre_data['map'][ref_p_key] = {}

                        pre_data['map'][ref_p_key][root_key] = (pseudo_verb_key, 0)

                    # Уровень 3: поиск ИГ во внешнем хранилище (сегменты)
                    else:
                        #print("### Can`t find which 1 point. Break.\n")
                        #pp.pprint(concept['init_text'])
                        #pp.pprint(p_key)

                        seg_id = concept['which1']['parent']
                        parent_segm = self.shelper.getListElementById(segments, seg_id)

                        if not parent_segm:
                            continue

                        parent_point_id = concept['which1']['point']
                        concept_data = self.extractor.getParentNP(parent_segm['morph'], parent_point_id)
                        if not concept_data:
                            continue

                        norm_form = self.prepareNP4Concept(concept_data, parent_segm)
                        if norm_form:
                            # Добавление терма;
                            # Точка независимая; дубликаты НЕ устанятся позже!
                            pre_data['terms'][p_key] = norm_form

                            # Порождение новых связей (псевдосвязей)
                            if p_key not in pre_data['map']:
                                pre_data['map'][p_key] = {}

                            pre_data['map'][p_key][root_key] = (pseudo_verb_key, 0)

            # Concept 4 (which 2: которого)
            elif concept_type == 4:
                # Найти анцендент и подставить в качестве родителя

                if not concept['which2']['parent'] or not concept['which2']['point']:
                    continue

                # Найти родителя связки (которого)
                p_key = str(concept['which2']['parent']) + '.' + concept['which2']['point']

                # Может быть в ссылках
                maybe_p_key = self.getGlobalPoint(p_key, invent_data['refs'])
                if maybe_p_key:
                    p_key = maybe_p_key

                # Уровень 1: поиск по триплетам и перенос точки на вершину ИГ
                parent_concept = self.searchConceptOfPoint(p_key, p_triplets, p_index)

                if parent_concept:
                    ref_p_key = parent_concept['root']

                    # Может быть в ссылках
                    maybe_p_key = self.getGlobalPoint(ref_p_key, invent_data['refs'])
                    if maybe_p_key:
                        ref_p_key = maybe_p_key

                    # Добавление родителя во временной словарь
                    if ref_p_key not in invent_data['terms']:
                        norm_form = concept['norm_form']
                        if concept['gent_tail']:
                            norm_form += ' ' + concept['gent_tail']
                        #WARN!!! Без поиска gent_tail.
                        pre_data['terms'][ref_p_key] = norm_form
                    else:
                        pre_data['points'].append(ref_p_key)

                # Уровень 2: поиск ИГ во внешнем хранилище (сегменты)
                else:
                    seg_id = concept['which2']['parent']
                    parent_segm = self.shelper.getListElementById(segments, seg_id)

                    if not parent_segm:
                        continue

                    parent_point_id = concept['which2']['point']
                    concept_data = self.extractor.getParentNP(parent_segm['morph'], parent_point_id)
                    if not concept_data:
                        continue

                    norm_form = self.prepareNP4Concept(concept_data, parent_segm)
                    if norm_form:
                        # Добавление терма;
                        # Точка независимая; дубликаты НЕ устанятся позже!
                        pre_data['terms'][p_key] = norm_form

        return pre_data

    def isDepricatedConcept(self, concept):
        result = False
        if self.plmaster.canUseModule():
            root_token = self.getRootToken(concept)
            if root_token:
                result = self.plmaster.schecker.isDeprecatedWord(root_token['lemma'])
        return result

    def getRootToken(self, concept):
        result = None
        if not concept['root']:
            return None

        if len(concept['tokens']) == 1:
            result = concept['tokens'][0]
        else:
            index = concept['nums'].index(concept['root'])
            result = concept['tokens'][index]
        return result

    def prepareNP4Concept(self, concept_data, parent_segm):
        '''
        Сквозная подготовка ИГ из сегмента в нормальную форму.
        Обрезка по ИГ корню; маркировка идет как N-SBJ.
        Sample:
            {'labels': ['', '', 'I-SBJ', 'I-SBJ', 'N-SBJ', 'I-SBJ', 'I-SBJ', 'I-SBJ'],
             'range': range(0, 8),
             'seg_id': -1,
             'text': 'вторым оптическим кабелем со вторым фотодиодом'}
        :return: None | 'второй оптический кабель'
        '''
        result = None

        # For inflect
        p_labels = []
        p_tokens = []
        p_nums = []
        p_root = None
        target_case = 'Nom'

        labels = concept_data['labels']
        shift = concept_data['range'][0]
        for i in concept_data['range']:
            label_index = i - shift
            label = labels[label_index]
            if label == '':
                continue
            elif label == 'I-SBJ' or label == 'N-SBJ':
                token_id = str(parent_segm['id']) + parent_segm['morph'][i]['id']

                p_labels.append(label)
                p_tokens.append(parent_segm['morph'][i])
                p_nums.append(token_id)

                if label == 'N-SBJ':
                    p_root = token_id
                    break

        result = self.inflectRootNP(p_labels, p_tokens, p_nums, p_root, target_case)

        return result

    def getGlobalPoint(self, verify_key, refs):
        """
        Поиск в глобальном вспомогательном массиве ссылочного ключа.
        Sample: trems['0.0'] = 'рекурсивный цифровой фильтр'
                refs = {'0.0': ['1.3']}
                verify_key = '1.3'
        :return: global_key = '0.0'
        """
        global_key = None
        if verify_key in refs:
            global_key = verify_key
        else:
            for g_key, refs_list in refs.items():
                if verify_key in refs_list:
                    global_key = g_key
                    break
        return global_key

    def searchConceptOfPoint(self, p_key, p_triplets, p_index):
        """
        Поиск родительской связки по ключу слова (может быть не рут).
        Sample: p_key = '12.13'
                блок коррекции частного и остатка
                ['12.9', '12.10', '12.11', '12.12', '12.13']
                real_root = '12.9'
        :return: parent_concept
        """
        parent_concept = None

        # Перебор всех триплетов (до дочернего)
        p_range = reversed(range(0, p_index))
        full_break = False
        xkeys = ['SBJ','OBJ']
        for i in p_range:
            # All sides
            for xkey in xkeys:
                # Перебор всех концептов
                for concept in p_triplets[i][xkey]:
                    # Наличие ключа в последовательности
                    if p_key in concept['nums']:
                        parent_concept = concept
                        full_break = True
                        break

                if full_break:
                    break
            if full_break:
                break

        return parent_concept

    def searchGentTail(self, gent_tail, p_triplets, p_index):
        """
        Поиск вхождений родительского описания.
        """
        parents = []

        p_len = len(p_triplets)

        if p_len == 0 or p_index == 0:
            return parents, gent_tail

        # Перебор всех триплетов (до дочернего)
        p_range = list(reversed(range(0, p_len)))

        full_break = False
        xkeys = ['SBJ','OBJ']
        for i in p_range:
            # Shift
            if i >= p_index:
                continue
            # All sides
            for xkey in xkeys:
                for concept in p_triplets[i][xkey]:
                    # Полный родительский кусок текста
                    gent_form = concept['gent_form']
                    if concept['gent_tail']:
                        gent_form += ' ' + concept['gent_tail']

                    #if self.can_print:
                    #    print("//")
                    #    print(gent_form)

                    if gent_tail == concept['gent_form'] or gent_form.startswith(gent_tail):
                        parents.append(concept['root'])
                        gent_tail = None
                        full_break = True
                        break

                    elif gent_tail.startswith(gent_form):
                        gent_tail = gent_tail[len(gent_form):].strip(' и')
                        parents.append(concept['root'])
                        if not gent_tail:
                            gent_tail = None
                            full_break = True
                            break

                    elif gent_tail.endswith(gent_form):
                        gent_tail = gent_tail[:-len(gent_form)].strip(' и')
                        parents.append(concept['root'])
                        if not gent_tail:
                            gent_tail = None
                            full_break = True
                            break

                if full_break:
                    break
            if full_break:
                break

        return parents, gent_tail

    def searchConceptInGlobal(self, concept, invent_data):
        """
        Поиск концепта в глобальном массиве по ключу и по нормальной форме.
        :return: None | <term_key> from invent_data['terms']
        """
        result = None
        root_key = concept['root']
        # Внешние ключи совпадают
        if root_key in invent_data['terms']:
            result = root_key
        # Поиск внешнего ключа по словоформе
        else:
            normal_form = concept['norm_form']
            if concept['gent_tail']:
                normal_form += ' ' + concept['gent_tail']

            for key, term in invent_data['terms'].items():
                if normal_form == term:
                    result = key
                    break

        return result

    def detectConcepType(self, concept):
        """
        Определение условного типа концепта:
        types:
            1 - Concept 1 (простой без ссылок и анафоры)
            2 - Concept 2 (анафора)
            3 - Concept 3 (с which1 = N_который)
            4 - Concept 4 (с which2 = который)
        """
        concept_type = 1

        if 'which1' in concept:
            concept_type = 3
        elif 'which2' in concept:
            concept_type = 4
        else:
            token_index = concept['nums'].index(concept['root'])
            if concept['tokens'][token_index]['pos'] == 'PRON':
                concept_type = 2

        return concept_type

    def prepareTriplet(self, triplet, segments):
        """
        Разбиение однородных триплетов и преобразование в промежуточную форму для извлечения.
        """
        # New form of (points)-triplet
        p_triplet = {}

        parent_ptrip = self.searchPtripletInStorage(triplet['ACT']['key'])
        if parent_ptrip:

            # SBJ already done; complete XBJ!!!

            # Учет того, с какой стороны располагалиьс субъект и объект
            if triplet['ACT']['side'] == 'r':
                xkey = 'OBJ'
            else:
                xkey = 'SBJ'

            sub_triplets, prep = self.splitXbj(triplet, segments, xkey)
            if sub_triplets:
                for triplet in sub_triplets:
                    #WARN!!! Adding by link
                    parent_ptrip[xkey].append(triplet)

        # Полная обработка структуры
        else:
            # Копирование готовых конструкций по первоначальному тексту
            xkey = 'SBJ'
            result = self.splitXbj(triplet, segments, xkey)
            p_triplet[xkey] = result[0]

            xkey = 'OBJ'
            result = self.splitXbj(triplet, segments, xkey)
            p_triplet[xkey] = result[0]
            prep = result[1]

            # Добавление в новый триплет инф. о глаголе и предлоге ----------------\
            p_triplet['ACT'] = copy.deepcopy(triplet['ACT'])
            if 'side' in p_triplet['ACT']:
                del p_triplet['ACT']['side']

            if prep:
                p_triplet['ACT']['prep'] = " ".join(prep)
            else:
                p_triplet['ACT']['prep'] = None
            #----------------------------------------------------------------------/

        return p_triplet

    def searchPtripletInStorage(self, verb_key):
        """
        Поиск связки по ключу глалога (для наполнения с других триплетов)
        :result: None | <p_triplet_link>
        """
        result = None

        if not self.p_triplets:
            return None

        for p_triplet in self.p_triplets:
            if p_triplet['ACT']['key'] == verb_key:
                result = p_triplet
                break

        return result

    def splitXbj(self, triplet, segments, xkey):
        """
        Обработка отдельной ветки триплета
        """
        p_xbj = []

        # Supporting (актуально для OBJ)
        prep_mark = 'P-OBJ'
        prep = []    # Накопление предлога/слов;
        is_prep_catched = None

        seg_id = triplet[xkey]['seg_id']
        segment = self.shelper.getListElementById(segments, seg_id)
        if segment:

            dict_xbj_key = 'np_' + xkey.lower()
            dict_root_key = dict_xbj_key + '_roots'

            np_roots_lbl = self.registry.label_points[dict_root_key]
            np_xbj_lbl = self.registry.label_points[dict_xbj_key]

            # To bypass the old structure
            x_range = triplet[xkey]['range']
            x_labels = triplet[xkey]['labels']
            shift = x_range[0]
            morph = segment['morph']
            inside_mark = 'I-' + xkey

            # New placeholders
            p_labels = []           # Перенос меток N-Xbj и I-Xbj
            p_tokens = []           # Морфология (токены слов)
            p_text = []             # Накопление токенов для join
            p_nums = []             # Универсальная нумерация привязки <seg_id>.<token_id>
            p_root = None           # Вершина ИГ (первая N-Xbj): номер <seg_id>.<token_id>

            # For whitch references
            whitch = None
            if 'which1' in triplet[xkey]:
                whitch = 'which1'
            elif 'which2' in triplet[xkey]:
                whitch = 'which2'

            # Механизм предпросмотра позиций корневых токенов (для разделения однородных)
            np_indexes = self.getLabelsIndexes(x_labels, np_roots_lbl)

            for i in x_range:
                label_index = i - shift
                label = x_labels[label_index]

                if label == '':
                    continue

                token = morph[i]

                # Catch prepositions --------------------------------------\
                if label == prep_mark and not is_prep_catched:
                    prep.append(token['text'])
                    if is_prep_catched == None:
                        is_prep_catched = False
                    continue
                elif is_prep_catched == False:
                    is_prep_catched = True
                #----------------------------------------------------------/

                # Пропуск предлога после drop (V с ... и с ...)
                if label == prep_mark and is_prep_catched and not p_labels:
                    continue

                if label in np_xbj_lbl:
                    token_num = str(seg_id) + '.' + token['id']

                    if p_root == None and label in np_roots_lbl:
                        p_root = token_num

                # Сброс в хранилище ---------------------------------------\

                # Проверка попадания между индексов И (Н И Н = 0 3 5)
                is_between = False
                if token['lemma'] == 'и' and label == inside_mark:
                    is_between = self.isBetweenN(np_indexes, label_index)

                if p_root and (is_between or label == prep_mark):
                    tmp = {}
                    tmp['labels'] = p_labels
                    tmp['tokens'] = p_tokens
                    tmp['text'] = " ".join(p_text).lower()
                    tmp['init_text'] = triplet[xkey]['text']
                    tmp['gent_tail'] = self.markGentTails(p_labels, p_tokens, p_nums, p_root)
                    tmp['norm_form'] = self.inflectRootNP(p_labels, p_tokens, p_nums, p_root, 'Nom')
                    tmp['gent_form'] = self.inflectRootNP(p_labels, p_tokens, p_nums, p_root, 'Gen')
                    tmp['nums'] = p_nums
                    tmp['root'] = p_root
                    # Service marks ---------------------------\
                    if whitch:
                        tmp[whitch] = triplet[xkey][whitch]
                    if 'after_sep' in triplet[xkey]:
                        tmp['after_sep'] = True
                    #-----------------------------------------/
                    p_xbj.append(copy.deepcopy(tmp))

                    # Clear
                    p_labels = []           # Перенос меток N-Xbj и I-Xbj
                    p_tokens = []           # Морфология (токены слов)
                    p_text = []             # Накопление токенов для join
                    p_nums = []             # Универсальная нумерация привязки <seg_id>.<token_id>
                    p_root = None           # Вершина ИГ (первая N-Xbj): номер <seg_id>.<token_id>

                #----------------------------------------------------------/

                # Наполнение буфера
                if not is_between and label != prep_mark and label in np_xbj_lbl:
                    p_labels.append(label)
                    p_tokens.append(token)
                    p_text.append(token['text'])
                    p_nums.append(token_num)

            # Add last buffer
            if p_labels and p_root:
                tmp = {}
                tmp['labels'] = p_labels
                tmp['tokens'] = p_tokens
                tmp['text'] = " ".join(p_text).lower()
                tmp['init_text'] = triplet[xkey]['text']
                tmp['gent_tail'] = self.markGentTails(p_labels, p_tokens, p_nums, p_root)
                tmp['norm_form'] = self.inflectRootNP(p_labels, p_tokens, p_nums, p_root, 'Nom')
                tmp['gent_form'] = self.inflectRootNP(p_labels, p_tokens, p_nums, p_root, 'Gen')
                tmp['nums'] = p_nums
                tmp['root'] = p_root
                # Service marks ---------------------------\
                if whitch:
                    tmp[whitch] = triplet[xkey][whitch]
                if 'after_sep' in triplet[xkey]:
                    tmp['after_sep'] = True
                #-----------------------------------------/
                p_xbj.append(copy.deepcopy(tmp))

        return p_xbj, prep

    def inflectRootNP(self, p_labels, p_tokens, p_nums, p_root, target_case):
        """
        Возврат ИГ корня в нужном падеже
        """
        labels_len = len(p_labels)
        index_range = range(0, labels_len)
        missing_poses = ['ADP', 'CCONJ']

        # Индекс корня
        root_index = 0
        # Поиск корневого элемента
        for i in index_range:
            if p_nums[i] == p_root:
                root_index = i
                break

        # Нужно ли добавлять хвост (не РОД. П.)
        add_after_root = False
        after_root_index = root_index + 1
        if after_root_index in index_range:
            add_after_root = p_labels[after_root_index] != 'I-GEN'

        root_gnc = self.shelper.getGNC(p_tokens[root_index])
        #is_need_convert = root_gnc['Case'] != target_case
        is_need_convert = True
        inflected = []
        for i in index_range:
            word = p_tokens[i]['text'][:].lower()

            if p_tokens[i]['pos'] in missing_poses:
                inflected.append(word)
                continue

            if is_need_convert:
                word = self.pmtool.inflectWord(word, target_case, root_gnc)
                if not word:
                    word = p_tokens[i]['lemma'][:]

            if i > root_index and p_tokens[i]['lemma'] == 'который':
                continue

            inflected.append(word)

            if i == root_index:
                if add_after_root:
                    is_need_convert = False
                else:
                    break

        return " ".join(inflected)

    def markGentTails(self, p_labels, p_tokens, p_nums, p_root):
        """
        Маркировка хвостов РОД.П.
        """
        result = None
        labels_len = len(p_labels)
        # Одно слово не маркируется
        if labels_len <= 1:
            return result

        index_range = range(0, labels_len)
        missing_poses = ['ADP', 'CCONJ']

        # Флаг разрешения поиска (после корня)
        can_search = False
        # Флаг разрешения маркировки, на будующий проход
        can_mark = True
        # Индекс начала маркировки
        start_index = 0

        for i in index_range:

            if p_nums[i] == p_root:
                can_search = True
                start_index = i
                continue

            if can_search:
                if p_tokens[i]['pos'] in missing_poses:
                    continue

                case = self.shelper.getCase(p_tokens[i])
                if case == 'Gen' or case == 'Acc':
                    continue
                else:
                    can_mark = False
                    break

        if can_mark:
            gent_tail = []
            for i in index_range:
                if i <= start_index or p_tokens[i]['lemma'] == 'который':
                    continue

                p_labels[i] = 'I-GEN'
                gent_tail.append(p_tokens[i]['text'])

            if gent_tail:
                result = " ".join(gent_tail)

        return result

    def isBetweenN(self, np_indexes, cconj_index):
        """
        Проверка попадания между индексов И (N И N = 0 3 5)
        """
        result = False

        if len(np_indexes) <= 1:
            return False

        left_catch = False
        for np_index in np_indexes:
            if left_catch:
                if np_index > cconj_index:
                    result = True
                    break
                else:
                    left_catch = True
                    continue
            else:
                left_catch = np_index < cconj_index
                continue

            left_catch = False

        return result

    def getLabelsIndexes(self, x_labels, np_roots):
        """
        Подсчет количество рутовых меток
        """
        indexes = []
        counter = -1
        for x_label in x_labels:
            counter += 1
            if x_label in np_roots:
                indexes.append(counter)
        return indexes

    def labelCorrection(self, triplet, segments, xkey):
        """
        Коррекция заполнения маркировки (зависимые N-Xbj и CCONJ)
        """
        seg_id = triplet[xkey]['seg_id']

        segment = self.shelper.getListElementById(segments, seg_id)
        if segment:
            x_range = triplet[xkey]['range']
            x_labels = triplet[xkey]['labels']
            shift = x_range[0]

            morph = segment['morph']
            first_index = None
            last_index = None

            # Механизм сброса лишней маркировки
            # Sample: 'затворы первого и второго полевых транзисторов с барьером шоттки'
            # ['','','N-SBJ','I-SBJ','I-SBJ','I-SBJ','I-SBJ','I-SBJ','I-SBJ','I-SBJ','N-SBJ',...]
            # Задача: сбросить корневые метки после предлогов (с.. шоттки (N-SBJ -> I-SBJ))
            # ...

            dict_key = 'np_' + xkey.lower() + '_roots'
            np_roots = self.registry.label_points[dict_key]

            n_dict = {}
            inside_mark = 'I-' + xkey

            for i in x_range:
                label_index = i - shift
                label = x_labels[label_index]

                if label != '':
                    # Rewrite indexes
                    if label.endswith(xkey):
                        if first_index == None:
                            first_index = i
                        last_index = i
                    # Root label
                    if label in np_roots:
                        # Add in dict
                        token_id = morph[i]['id']
                        deprel = morph[i]['deprel']
                        n_dict[token_id] = (morph[i]['parent'], label_index, deprel)

            # Fix N-Xbj labels
            if len(n_dict) > 1:
                # Stage 2: By n_dict
                n_dict_keys = n_dict.keys()
                for key, val in n_dict.items():
                    # Parent is N-Xbj, but not CCONJ
                    if val[0] in n_dict_keys and not val[2] == 'conj':
                        label_index = val[1]
                        triplet[xkey]['labels'][label_index] = inside_mark

            # Fix first CCONJ
            if first_index != None:
                if morph[first_index]['pos'] == "CCONJ":
                    label_index = first_index - shift
                    triplet[xkey]['labels'][label_index] = ''

            # Fix las CCONJ
            if last_index != None:
                if morph[last_index]['pos'] == "CCONJ":
                    label_index = last_index - shift
                    triplet[xkey]['labels'][label_index] = ''


        return

    def generateRoot(self, generic_term, segments):
        """
        Формирование вершины дерева (родовое понятие)
        """
        invent_terms = {}
        # Default
        root_key = '0.0'
        root_value = '<UNKNOWN>'

        if generic_term:
            root_value = generic_term['text']

            seg_id = generic_term['seg_id']
            x_range = generic_term['range']
            x_labels = generic_term['labels']
            shift = x_range[0]

            root_token = None
            segment = None

            for i in x_range:
                label_index = i - shift
                if x_labels[label_index] in self.registry.label_points['np_sbj_roots']:
                    segment = self.shelper.getListElementById(segments, seg_id)
                    root_token = segment['morph'][i]
                    break

            if segment and root_token:
                # Additional information
                generic_term['parent_gnc'] = self.shelper.getGNC(root_token)

                # For inflect
                p_labels = x_labels
                p_tokens = []
                p_nums = []
                p_root = str(seg_id) + '.' + root_token['id']
                target_case = 'Nom'

                for i in x_range:
                    label_index = i - shift
                    token = segment['morph'][i]
                    p_key = str(seg_id) + '.' + token['id']
                    p_tokens.append(token)
                    p_nums.append(p_key)

                root_value = self.inflectRootNP(p_labels, p_tokens, p_nums, p_root, target_case)

            else:
                generic_term['parent_gnc'] = None

        invent_terms[root_key] = root_value

        return invent_terms
