# patents-claim-handler
Прототип системы извлечения структурированных данных из русскоязычных патентов.

### Описание системы
Система извлечения морфологических признаков технических объектов (элементов конструкций и части технического результата) из русскоязычных патентов в рамках задачи автоматизированного изобретательства. Извлеченные данные сохраняются в виде онтолгии предметной области (формат RDF/XML).

### Настройка окружения
1. Собрать исходник Томита-парсер ([git@github.com:yandex/tomita-parser.git](url)); 
    указать абсолютный путь до исходника в классе ./tools/AppConfig (TOMITA_BIN_PATH);
2. Установить зависимости python (3.5+):
- pip install ufal.udpipe
- pip install pymorphy2
- pip install pymorphy2-dicts
- pip install pymystem3
- pip install python-crfsuite
- pip install Owlready2
- pip install progressbar2
- pip install matplotlib
- pip install networkx

### Запуск системы
Пример пакетной обработки:
$ python3 run.py batch --input ./data/ --output ./data/ --limit 10000 --chunksize 1000

Пример обработки одного файла:
$ python3 run.py single --patent ./data/doc1.xml --owl ./data/result.owl --print_graph

### Входные и выходные данные
Входные файлы - русскоязычные патенты в xml-разметке (логическая структура соответствует объявлению типа документа (DTD) «ru-patent-document-v1-3.dtd»).

Выходные файлы - концептуализированные данные об изобретении и элементах его конструкции, сохраненные в файлах выгрузки онтологии (owl).

