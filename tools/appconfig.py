import pprint as pp

# Реестр системных переменных
class AppConfig(object):

    # Директория файлов обработки (грамматика, результат и т.д.)
    TOMITA_OUT_PATH = './tools/pytomita/'
    # Абсолютный путь до бинарника Томита-парсера
    TOMITA_BIN_PATH = '/home/serj/NLP/segmenter/external/tomita-linux64'
    # Модель чанкера именных групп (относительный путь от скрипта запуска)
    CHUNKER_MODEL_PATH = './models/rus-chunker.crfsuite'
    # Шаблон онтологии (для заполнения)
    ONTOLOGY_TEMPLATE = './external/ood_template_v2.0.owl'
    # Модель синтаксического анализатора
    UDPIPE_MODEL = './models/russian-syntagrus-ud-2.3-181115.udpipe'

    # Singleton
    __instance = None

    def __new__(cls):
        if AppConfig.__instance is None:
            AppConfig.__instance = object.__new__(cls)

        return AppConfig.__instance
