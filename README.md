# patents-claim-handler
Прототип системы извлечения структурированных данных из русскоязычных патентов

### Запуск системы
1. Собрать исходник Томита-парсер (git@github.com:yandex/tomita-parser.git); 
    указать абсолютный путь до исходника в классе ./tools/AppConfig (TOMITA_BIN_PATH);
2. Установить python-зависимости:
- pip install ufal.udpipe
- pip install pymorphy2
- pip install pymorphy2-dicts
- pip install pymystem3
- pip install python-crfsuite
- pip install Owlready2
- pip install progressbar2
- pip install matplotlib
- pip install networkx
