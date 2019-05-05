import xml.etree.ElementTree as ET
import sys, codecs, re, os
import pprint as pp

# Чтение файлов
class ClaimReader(object):

    def __init__(self):
        self.pattern = re.compile('<claim-text>(.*)</claim-text>')

    def readFromFile(self, file_path):
        try:
            with codecs.open(file_path, "r", "utf-8") as file:
                text = file.read()
        except:
            sys.stderr.write("[%s] Unexpected error: '%s'\n" % (self.__class__.__name__, sys.exc_info()[0]) )
            exit(1)

        return text

    def findFiles(self, catalog, ext_filter = '.xml'):
        """
        Поиск файлов по фильтру во всех подкаталогах catalog.
        :return: список найденных путей.
        """
        found_files = []
        if len(ext_filter) <= 0:
            ext_filter = '.xml'

        for root, dirs, files in os.walk(catalog):
            for name in files:
                if name.lower().endswith(ext_filter) > 0:
                    found_files.append(os.path.join(root, name))

        return found_files

    def getSimpleClaims(self, xml_path):
        """
        Функция чтения одного простого файла ХМЛ
        """
        result = []

        with codecs.open(xml_path, "r", "utf-8") as xml_file:
            xml_text = xml_file.read()

        result = self.pattern.findall(xml_text)

        return result

    def isRuPatentXML(self, xml_root):
        """
        Проверка заголовка документа (целевая разметка XML)
        :return: True | False
        """
        result = False
        if ET.iselement(xml_root):
            result = xml_root.tag == 'ru-patent-document'
        return result

    def getXMLRoot(self, xml_path):
        """
        Получение корня дерева XML.
        Точка входа в парсинг!
        """
        result = None
        if os.path.exists(xml_path):
            tree = ET.parse(xml_path)
            result = tree.getroot()
        return result

    def getMainClaim(self, xml_root):
        """
        Получение первого клейма (точно первого).
        """
        result = None
        first_claim = xml_root.find(".//claims[@lang='ru']/claim[@num='1']")
        if first_claim:
            result = str(first_claim[0].text)
        return result

    def getPatentIPC(self, xml_root):
        """
        Собрать класс патента.
        :return: список классов
        """
        result = []
        b510ep = xml_root.find(".//B510EP")
        if b510ep:
            for ipcr in b510ep.iter('classification-ipcr'):
                ipc_class = ''
                pc_section = ipcr.find('.//section').text
                if not pc_section:
                    continue

                pc_class = ipcr.find('.//class').text
                if not pc_class:
                    continue

                pc_subclass = ipcr.find('.//subclass').text
                if not pc_subclass:
                    continue

                ipc_class += pc_section.strip() + pc_class.strip() + pc_subclass.strip()

                pc_group = ipcr.find('.//main-group').text
                if pc_group:
                    ipc_class += pc_group.strip()
                    pc_subgroup = ipcr.find('.//subgroup').text
                    if pc_subgroup:
                        ipc_class += '/' + pc_subgroup.strip()

                result.append(str(ipc_class))

        return result

    def getGranteeOrg(self, xml_root):
        """
        Наименование организации-получателя патента.
        """
        result = None
        organization = xml_root.find(".//SDOBI[@lang='ru']//B731")
        if organization:
            result = str(organization[0].text)
        return result

    def getPatentCode(self, xml_root):
        """
        Собрать код патента.
        :return: Строка комбинированного кода.
        Sample:
        <ru-patent-document lang="ru" dtd-version="ru-patent-document-v1-3" doc-number="02251268" country="RU" kind="C9" date-publ="20121220" correction-code="W1" status="N">
        """
        result = ''
        if ET.iselement(xml_root):
            if xml_root.tag == 'ru-patent-document':
                delimeter = '_'
                required_tags = ['country','doc-number','kind','date-publ']
                for tag in required_tags:
                    if tag in xml_root.attrib:
                        result += xml_root.attrib.get(tag) + delimeter
                    else:
                        return None
                result = result.strip(delimeter)

        return result

    def getClaims(self, xml_root):
        """
        Получение всех клеймов
        """
        result = []
        if ET.iselement(xml_root):
            claims = xml_root.find(".//claims[@lang='ru']")
            if ET.iselement(claims):
                for claim in claims:
                    result.append(str(claim[0].text))

        return result

    def getDescriptions(self, xml_root):
        """
        Получение описаний на русском
        """
        result = []
        if ET.iselement(xml_root):
            description = xml_root.find(".//description[@lang='ru']")
            if description:
                for item in description.getchildren():
                    result.append(str(item.text))

        return result

    def getAbstacts(self, xml_root):
        """
        Получение рефератов на русском.
        """
        result = []
        if ET.iselement(xml_root):
            abstract = xml_root.find(".//abstract[@lang='ru']")
            if abstract:
                for item in abstract.getchildren():
                    result.append(str(item.text))
        return result

    def getInventionName(self, xml_root):
        """
        Наименование устройства на русском.
        """
        result = ''
        if ET.iselement(xml_root):
            name = xml_root.find(".//ru-b542")
            if ET.iselement(name):
                result = str(name.text)
        return result
