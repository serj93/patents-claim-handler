# -*- coding: utf-8 -*-

import os
import os.path as path
from io import open
import subprocess
from collections import defaultdict
import xml.etree.ElementTree as ET


class TomitaParser(object):

    FACT_SCHEME = {'AOC': ['Action', 'Object', 'Condit']}

    def __init__(self, tomita_bin_path, directory='.'):
        self.binary_path = tomita_bin_path
        self.base_dir = directory
        self.documents_file = path.join(self.base_dir, 'documents_dlp.txt')
        self.output_file = path.join(self.base_dir, 'facts.xml')

    def __set_documents(self, documents):
        with open(self.documents_file, 'w', encoding='utf8') as fd:
            for doc in documents:
                doc = doc.replace('\n', ' ')
                fd.write(doc + '\n')

    def __run(self):
        """
        deletes output file and creates new
        :raises: subprocess.CalledProcessError if tomita parser failed
        :returns: True if run was successful
        """
        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)
        original_dir = os.getcwd()
        try:
            os.chdir(self.base_dir)
            config_path = os.path.join(self.base_dir, 'config.proto')
            try:
                output = subprocess.check_output(
                    self.binary_path + ' ' + 'config.proto',
                    shell=True,
                    universal_newlines=True,
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as e:
                print('Got exception {}'.format(e))
                print('Tomita output {}'.format(e.output))
                raise e
        finally:
            os.chdir(original_dir)
        success = 'End.  (Processing files.)' in output
        return success

    def __get_xml(self):
        """ :return: xml.etree.ElementTree root """
        return ET.parse(self.output_file).getroot()

    def __parse(self, fact_description):
        root = self.__get_xml()
        dupl_check = []
        doc_facts = []
        fact_name = str(list(fact_description.keys())[0])
        for document in root.findall('document'):
            facts = document.find('facts')
            attributes = facts.findall(fact_name)
            for attr in attributes:
                children = attr.getchildren()
                doc_fact = {}
                dupl_text = ''
                for attribute_name in fact_description[fact_name]:
                    value = None
                    for child in children:
                        if child.tag == attribute_name:
                            value = child.attrib.get('val').lower()
                            break
                    if value:
                        doc_fact[attribute_name] = value
                        dupl_text += value

                if doc_fact and dupl_text not in dupl_check:
                    doc_facts.append(doc_fact)
                    dupl_check.append(dupl_text)
        return doc_facts

    def __clean(self):
        """ Deletes all files from working directory. """
        files_to_delete = [
            self.documents_file,
            self.output_file,
            path.join(self.base_dir, 'requirements.bin'),
            path.join(self.base_dir, 'dict.gzt.bin'),
            path.join(self.base_dir, 'dict.gzt.bin'),
        ]

        for file in files_to_delete:
            try:
                os.unlink(file)
            except OSError:
                pass

    def extractFacts(self, documents):
        """
        Декоратор запуска обработки
        """
        self.__set_documents(documents)
        self.__run()
        result = self.__parse(self.FACT_SCHEME)
        self.__clean()
        return result
