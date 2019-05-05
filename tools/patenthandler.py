import pprint as pp
import pickle, os.path
import time, re, logging, traceback
import progressbar
from datetime import datetime

from tools.claimparser import ClaimParser
from tools.claimreader import ClaimReader
from tools.registry import DictRegistry
from tools.pytomita.tomita import TomitaParser
from tools.graphbuilder import GraphBuilder
from tools.appconfig import AppConfig
from tools.owlcollector import OWLCollector

# Агрегация обработки всего документа патента
# Пакетная обработка только XML!!!
class PatentHandler(object):

    PATTERN = re.compile("техническ[а-я]+ результа[а-я:]+", re.IGNORECASE)

    def __init__(self):
        self.parser = ClaimParser()
        self.reader = ClaimReader()
        self.config = AppConfig()
        self.tomita = TomitaParser(self.config.TOMITA_BIN_PATH, self.config.TOMITA_OUT_PATH)
        self.gbuilder = GraphBuilder()
        self.collector = OWLCollector()
        logging.basicConfig(filename='app.log', filemode='w')

    def patentBatchProcessing(self, input_dir, output_dir, limit = 10000, chunksize = 500):
        """
        Цикл обработки данных (с сохранением результатов)
        :param:input_dir: каталог с патентами (xml-документы)
        :param:output_dir: каталог сохранения owl-файлов (результат)
        :param:limit: ограничение обрабатываемых файлов
        :param:chunksize: сколько сохранять документов в выгрузку owl-файла за раз
        """
        files = self.reader.findFiles(input_dir, '.xml')
        files_count = len(files)
        if files_count > 0:
            print("Files found:\t{}".format(str(files_count)))
            print("Files limit:\t{}".format(str(limit)))
            print("Chunksize  :\t{}".format(str(chunksize)))

            widgets = [progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage(), ' ', progressbar.ETA()]
            bar = progressbar.ProgressBar(maxval=files_count, widgets=widgets)
            bar.start()

            doc_prefix = "onto_"
            doc_counter = 0
            path_counter = 0
            owl_file_num = 1

            docs_buffer = []

            # Main loop
            for fpath in files:

                patent_data = self.collectPatentData(fpath)

                bar.update(path_counter)
                path_counter += 1

                if patent_data:
                    doc_counter += 1
                    docs_buffer.append(patent_data)

                    # Upload buffer
                    if doc_counter % chunksize == 0:
                        filename = self.createOwlFileName(owl_file_num, output_dir)
                        self.collector.saveBatchPatentData(docs_buffer, filename)
                        docs_buffer = []
                        owl_file_num += 1

                if doc_counter >= limit:
                    time.sleep(0.02)
                    print("\nStopped by limit.")
                    break

            if len(docs_buffer) > 0:
                filename = self.createOwlFileName(owl_file_num, output_dir)
                owl_file_num += 1
                self.collector.saveBatchPatentData(docs_buffer, filename)
                docs_buffer = []

            print("\n\nTotal number of files:\t{}".format(str(files_count)))
            print("Documents viewed     :\t{}".format(str(path_counter)))
            print("Extracting data from :\t{}".format(str(doc_counter)))

        return None

    def createOwlFileName(self, owl_file_num, base_dir):
        """
        Генерация наименования файла онтологии.
        """
        now = datetime.now()
        date_time = now.strftime("%Y%m%d%H%M%S")
        filename = "patents_{}_{}.owl".format(date_time, str(owl_file_num))
        result = os.path.join(base_dir, filename)
        return result

    def collectPatentData(self, fpath):
        """
        Обработка одного документа.
        """
        result = {}
        try:
            xml_root = self.reader.getXMLRoot(fpath)
            if not xml_root:
                xml_root.clear()
                return None

            check = self.reader.isRuPatentXML(xml_root)
            if not check:
                xml_root.clear()
                return None

            patent_code = self.reader.getPatentCode(xml_root)
            if not patent_code:
                return None

            main_claim_text = self.reader.getMainClaim(xml_root)
            if main_claim_text:
                if main_claim_text.find('Способ') >= 0 or main_claim_text.find(':') > 0:
                    return None

                inv_graph = self.parser.run(main_claim_text)
                if inv_graph:
                    # Элементов должно быть больше, чем просто родовое понятие =)
                    if len(inv_graph['terms']) > 1:
                        result['graph'] = inv_graph

            line_buffer = []
            abstracts = self.reader.getAbstacts(xml_root)
            if abstracts:
                self.filterFactCandidates(line_buffer, abstracts)

            descriptions = self.reader.getDescriptions(xml_root)
            if descriptions:
                self.filterFactCandidates(line_buffer, descriptions)

            if len(line_buffer) > 0:
                facts = self.tomita.extractFacts(line_buffer)
                if facts:
                    result['facts'] = facts

            if result:
                inv_name = self.reader.getInventionName(xml_root)
                ipc_classes = self.reader.getPatentIPC(xml_root)
                org = self.reader.getGranteeOrg(xml_root)

                result['name'] = inv_name
                result['code'] = patent_code
                result['org'] = org

                if ipc_classes:
                    result['ipc'] = ipc_classes
                else:
                    result['ipc'] = []

                if 'facts' not in result:
                    result['facts'] = []


        except Exception as e:
            log_message = " FILE: '{}'".format(fpath)
            logging.warning(log_message)
            logging.error(traceback.format_exc())
            return None

        return result

    def filterFactCandidates(self, line_buffer, new_lines):
        # For all items
        for line in new_lines:
            search = self.PATTERN.search(line)
            if search:
                line_buffer.append(line)
                break

    def patentSingleProcessing(self, input, output, is_print_graph):
        """
        Обработка одного файла с выводом информации.
        """
        result = False
        patent_data = self.collectPatentData(input)

        if patent_data:
            result = True
            print("\nPATENT DATA:")
            pp.pprint(patent_data)

            if output:
                self.collector.saveSinglePatentData(patent_data, output)

            if is_print_graph:
                self.gbuilder.printInventGraph(patent_data['graph'])

        return result
