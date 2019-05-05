import pprint as pp
import copy

# Постобработка структуры invent_data
class IDPostProcessor(object):

    def __init__(self):
        pass

    def dataPostProcessing(self, invent_data):
        '''
        Инициализация постобработки данных
        '''
        invent_data = self.mergeSimilar(invent_data)
        invent_data = self.mergeSynonims(invent_data)
        invent_data = self.clearServiceInfo(invent_data)

        return invent_data

    def clearServiceInfo(self, invent_data):
        """
        Очистка данных
        """

        if 'generic_term' in invent_data:
            if invent_data['generic_term']:
                invent_data['generic_term'] = invent_data['generic_term']['text']

        # Saved for owlcollector!
        #if 'refs' in invent_data:
        #    del invent_data['refs']

        return invent_data

    def mergeSimilar(self, invent_data):
        '''
        Слияние однородных вершин (урезанных названий)
        Пример: генератор переменного тока === генератор
            1. Вершина должна быть подвешена (нет родителя с comp)
            2. Только одно вхождение по словоформе в терм другой вершины
        '''
        allowed_verb_types = ['have', 'comp']
        sbj_keys = list(invent_data['map'].keys())
        # Without duplicates!
        all_keys = list(invent_data['terms'].keys())
        # Root dropped
        all_keys.remove('0.0')

        for sbj_key in sbj_keys:
            sub_keys = list(invent_data['map'][sbj_key].keys())
            for sub_key in sub_keys:
                # (verb_key, verb_prefix)
                verb_key = invent_data['map'][sbj_key][sub_key][0]
                verb_type = invent_data['verbs'][verb_key]['type']
                # Оставляем слабые линки (типа связи)
                if verb_type in allowed_verb_types and sub_key in all_keys:
                    all_keys.remove(sub_key)

        if all_keys:
            for dif_key in all_keys:
                #print("Float point: {} | {}".format(dif_key, invent_data['terms'][dif_key]))
                sim_keys = self.findSimilarTerms(invent_data, dif_key)
                # Должна быть только 1 включающая в себя текст запись
                if len(sim_keys) == 1:
                    #print("Parent: " + invent_data['terms'][sim_keys[0]])
                    tar_key = sim_keys[0]
                    self.replaceMapKey(invent_data, dif_key, tar_key)

        return invent_data

    def replaceMapKey(self, invent_data, repl_key, targ_key):
        '''
        Замена всех вхождений ключа в карте на указанный.
        :param:repl_key: заменяемый ключ
        :param:targ_key: целевой ключ
        '''
        sbj_keys = list(invent_data['map'].keys())

        # Замена во внутренних словарях
        for sbj_key in sbj_keys:
            if repl_key in invent_data['map'][sbj_key]:
                if targ_key in invent_data['map'][sbj_key]:
                    invent_data['map'][sbj_key].pop(repl_key)
                else:
                    invent_data['map'][sbj_key][targ_key] = invent_data['map'][sbj_key].pop(repl_key)

        # Замена внешнего ключа
        if repl_key in sbj_keys:
            if targ_key not in invent_data['map']:
                invent_data['map'][targ_key] = {}
            invent_data['map'][targ_key].update(invent_data['map'].pop(repl_key))

        # Удаление термина
        if repl_key in invent_data['terms']:
            del invent_data['terms'][repl_key]

        return

    def findSimilarTerms(self, invent_data, search_key):
        '''
        Пример: генератор переменного тока === генератор
        '''
        result = []
        search_term = invent_data['terms'][search_key]
        for key, term in invent_data['terms'].items():
            if key == search_key:
                continue
            if term.find(search_term) >= 0:
                result.append(key)
        return result

    def mergeSynonims(self, invent_data):
        '''
        Устранение возможных синонимов у одного узла:
        * зависимые узлы одного родителя имеют одинаковые термы при разных номерах
        Пример: 'terms': {'2.3': 'выход', ...,'5.2':'выход'}
                'map': {'1.1': { '2.3': (verb1), '5.2': (verb2)}}
        Нужно сделать: удалить второй ключ ('5.2') из термов и заменить его на первый ('2.3') в мапе
        '''

        if not invent_data['map'] or not invent_data['terms']:
            return invent_data

        replaced = {}
        for sbj_key, childs in invent_data['map'].items():
            buffer = {}
            for obj_key, verb in childs.items():
                # Глагол должен быть типа comp!!!
                verb_key = verb[0]
                verb_type = invent_data['verbs'][verb_key]['type']
                if verb_type == 'conn':
                    continue

                searched_term = invent_data['terms'][obj_key]

                if searched_term not in buffer.values():
                    buffer[obj_key] = invent_data['terms'][obj_key]
                else:
                    main_key = self.getDictKeyByValue(buffer, searched_term)
                    if main_key:
                        repl_key = obj_key
                        # Add to repl. dict
                        if main_key not in replaced:
                            replaced[main_key] = []
                        replaced[main_key].append(repl_key)

        if replaced:
            #DEBUGGER ------------------------------------------\
            if False:
                print("### mergeSynonims is done!!! Break.\n")
                pp.pprint(replaced)
                pp.pprint(invent_data['terms'])
                pp.pprint(invent_data['map'])
                exit(0)
            #--------------------------------------------------/

            for main_key, repl_keys in replaced.items():
                for repl_key in repl_keys:
                    self.replaceMapKey(invent_data, repl_key, main_key)

        return invent_data

    def getDictKeyByValue(self, dictionary, searched_value):
        result = None
        for key, value in dictionary.items():
            if value == searched_value:
                result = key
                break
        return result
