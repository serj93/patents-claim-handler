import pprint as pp

from owlready2 import *
from tools.appconfig import AppConfig

# Конвертация внутреннего формата данных в OWL (шаблон схемы онтологии)
class OWLCollector(object):

    def __init__(self):
        self.config = AppConfig()

    def saveBatchPatentData(self, docs_buffer, filepath):
        """
        Выгрузка массива данных в онтологию.
        """
        result = True
        onto = get_ontology(self.config.ONTOLOGY_TEMPLATE).load()
        for patent_data in docs_buffer:
            onto = self.fillOntology(onto, patent_data)
        onto.save(filepath)
        #print("\nFile '{}' has been saved!".format(filepath))

        return result

    def saveSinglePatentData(self, patent_data, filepath):
        """
        Сохранение данных одного файла.
        Гарантируется корректность входного массива!
        """
        result = True
        onto = get_ontology(self.config.ONTOLOGY_TEMPLATE).load()
        onto = self.fillOntology(onto, patent_data)
        onto.save(filepath)
        print("\nFile '{}' has been saved!".format(filepath))

        return result

    def fillOntology(self, onto, patent_data):
        """
        Добавление данных патента в инициализированную онтологию.
        """
        doc_prefix = patent_data['code'] + '_'

        device = onto.Device(doc_prefix + 'dev_0')

        is_graph_data = 'graph' in patent_data

        if is_graph_data and patent_data['graph']['generic_term']:
            generic_term = patent_data['graph']['generic_term']
        else:
            generic_term = patent_data['name'].lower()

        device.concept_name = [generic_term]
        device.doc_name = patent_data['name']
        device.doc_num = patent_data['code']

        if patent_data['org']:
            device.doc_org = [patent_data['org']]

        if patent_data['ipc']:
            ipc = onto.IPC(doc_prefix + 'ipc_0')
            ipc.ipc_code = patent_data['ipc']
            device.has_ipc.append(ipc)

        if patent_data['facts']:
            fact_counter = 0
            for fact in patent_data['facts']:
                fact_counter += 1
                fact_name = fact['Action'] + ' ' + fact['Object']
                if 'Condit' in fact:
                    fact_name += ' ' + fact['Condit']

                problem_obj = onto.Problem(doc_prefix + 'pbl_' + str(fact_counter))
                problem_obj.problem_name.append(fact_name)
                device.solution_for.append(problem_obj)

        if is_graph_data:
            entity_adapter = {}
            entity_adapter['0.0'] = device

            # Add terms
            comp_counter = 0
            for key, term in patent_data['graph']['terms'].items():
                if key == '0.0':
                    continue
                comp_obj = onto.Component(doc_prefix + 'com_' + str(comp_counter))
                comp_counter += 1
                comp_obj.concept_name = [term]
                comp_obj.part_of.append(device)

                entity_adapter[key] = comp_obj

            # Add links
            for sbj_key, childs in patent_data['graph']['map'].items():
                for obj_key, link_pair in childs.items():
                    verb_key = link_pair[0]
                    link_type = patent_data['graph']['verbs'][verb_key]['type']

                    # Refactoring -------------------------------------------------\
                    if sbj_key not in entity_adapter:
                        maybe_key = self.lookAtRefs(patent_data['graph'], sbj_key)
                        if maybe_key and maybe_key in entity_adapter:
                            sbj_key = maybe_key
                        else:
                            continue

                    if  obj_key not in entity_adapter:
                        maybe_key = self.lookAtRefs(patent_data['graph'], obj_key)
                        if maybe_key and maybe_key in entity_adapter:
                            obj_key = maybe_key
                        else:
                            continue
                    #--------------------------------------------------------------/

                    master = entity_adapter[sbj_key]
                    slave = entity_adapter[obj_key]

                    if link_type == 'comp':
                        master.contains.append(slave)
                    elif link_type == 'conn':
                        master.connected_to.append(slave)
                    elif link_type == 'have':
                        master.parent_for.append(slave)

        return onto

    def lookAtRefs(self, graph_data, desired_key):
        """
        Поиск родителя задублированного ключа (карты) в ссылках.
        """
        result = None
        if 'refs' in graph_data:
            refs_keys = list(graph_data['refs'].keys())
            for ref_key in refs_keys:
                if desired_key in graph_data['refs'][ref_key]:
                    result = ref_key
                    break
        return result
