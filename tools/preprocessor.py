import pprint as pp
import re

# Предобработчик текста: грубая сегментация на предложения; удаление вводных конструкций и шума....
class TextPreprocessor(object):

    # Список вводных слов
    turnovers = [
        "по меньшей мере",
        "по крайней мере",
        "однако",
        "однако же",
        "например",
        "по существу",
        "наоборот",
        "в частности",
        "в свою очередь",
    ]

    special_chars = {
        '&nbsp;': ' ',
        '&shy;': '',
        '&lt;': '<',
        '&gt;': '>',
        '&laquo;': '«',
        '&raquo;': '»',
        '&lsaquo;': '‹',
        '&rsaquo;': '›',
        '&quot;': '"',
        '&prime;': '′',
        '&Prime;': '″',
        '&lsquo;': '‘',
        '&rsquo;': '’',
        '&sbquo;': '‚',
        '&ldquo;': '“',
        '&rdquo;': '”',
        '&bdquo;': '„',
        '&#10076;': '❜',
        '&#10075;': '❛',
        '&amp;': '&',
        '&apos;': '\'',
        '&sect;': '§',
        '&copy;': '©',
        '&not;': '¬',
        '&reg;': '®',
        '&macr;': '¯',
        '&deg;': '°',
        '&plusmn;': '±',
        '&sup1;': '¹',
        '&sup2;': '²',
        '&sup3;': '³',
        '&frac14;': '¼',
        '&frac12;': '½',
        '&frac34;': '¾',
        '&acute;': '´',
        '&micro;': 'µ',
        '&para;': '¶',
        '&middot;': '·',
        '&iquest;': '¿',
        '&fnof;': 'ƒ',
        '&trade;': '™',
        '&bull;': '•',
        '&hellip;': '…',
        '&oline;': '‾',
        '&ndash;': '–',
        '&mdash;': '—',
        '&permil;': '‰',
        '&#125;': '}',
        '&#123;': '{',
        '&#61;': '=',
        '&ne;': '≠',
        '&cong;': '≅',
        '&asymp;': '≈',
        '&le;': '≤',
        '&ge;': '≥',
        '&ang;': '∠',
        '&perp;': '⊥',
        '&radic;': '√',
        '&sum;': '∑',
        '&int;': '∫',
        '&#8251;': '※',
        '&divide;': '÷',
        '&infin;': '∞',
        '&#64;': '@',
        '&#91;': '[',
        '&#93;': ']',
    }

    #def __init__(self):

    # Запуск очистки по всем пунктам
    def startPreprocessing(self, text):
        text = text.strip()
        text = self.clearTurnovers(text)
        #text = self.clearReferenceBracket(text)
        text = self.clearAllBracket(text)
        text = self.clearFirstNum(text)
        text = self.cleanhtml(text)
        text = self.cleanDoubleCommas(text)
        text = self.claerAnotherSimbols(text)

        if text.find('/')>=0:
            text = self.correctSlashes(text)
        if text.find('-')>=0:
            text = self.correctDashes(text)
        if text.find('&')>=0:
            text = self.replaceHTMLSpecChars(text)

        # Experimental
        text = self.mergeConj(text)

        # Always last fixing
        text = self.clearDoubledSpaces(text)

        return text

    def claerAnotherSimbols(self, text):
        if text.find('\'') > 0:
            text = re.sub(r'([а-я])\' ', r'\1 ', text)
        return text

    def mergeConj(self, text):
        if text.find(', и,')>=0:
            text = text.replace(', и,', ', и')
        if text.find('а именно,')>=0:
            text = text.replace('а именно,', 'а именно')
        return text

    def replaceHTMLSpecChars(self, text):
        parts = re.findall(r'&#?[a-z0-9]+;', text)
        for part in parts:
            text = text.replace(part, self.special_chars[part])
        return text

    def cleanDoubleCommas(self, text):
        text = re.sub(r'(\s,)+', ',', text)
        text = re.sub(r',\s?\.', '.', text)
        return text

    # Fix и/или =>
    def correctDashes(self, text):
        return re.sub(r'(\d+) (-\d+)', r'\1\2', text)

    # Fix и/или =>
    def correctSlashes(self, text):
        text = re.sub(r'(\d+) (/)', r'\1\2', text)
        return re.sub(r'([а-я]+)/([а-я]+)', r'\1 / \2', text)

    def clearDoubledSpaces(self, text):
        return re.sub(r'\s{2,}', ' ', text)

    def cleanhtml(self, raw_html):
        # Accerate drop <br>
        #raw_html = re.sub(r'<\s?br\s?/\s?>', ' ', raw_html)
        # Any other tag
        raw_html = re.sub(r'<.*?>', ' ', raw_html)
        return raw_html

    # Очистка текста от вводных конструкций
    def clearTurnovers(self, text):
        for turnover in self.turnovers:
            if text.find(turnover)>=0:
                text = text.replace(', ' + turnover + ',', '')
                ### Refactoring required!!!
                text = text.replace(' ' + turnover + ' ', ' ')

        return text

    # Удаление ВСЕХ скобок
    def clearAllBracket(self, text):
        text = re.sub(r'\([^)]*\)(, \([^)]*\))*', '', text)
        return text

    # Удаление ссылочных скобок (1), (25)...
    def clearReferenceBracket(self, text):
        text = re.sub(r'\(\d+\)', '', text)
        return text

    def clearFirstNum(self, text):
        text = re.sub(r'^\d+\.?\s?', '', text)
        return text

    def splitByPattern(self, text, pattern=", отличающ[а-я]+ тем, что", is_doublecheck = True):
        parts = re.split(pattern, text, maxsplit=1)
        # Another pattern
        if is_doublecheck and len(parts) < 2:
            pattern = ", характеризующ[а-я]+ тем, что"
            parts = re.split(pattern, text, maxsplit=1)
        return parts

    # Отделяет пробелом пунктуацию
    def addSpacesBetweenPunct(self, text):
        return re.sub(r"([\w/'+$\s-]+|[^\w/'+$\s-]+)\s*", r"\1 ", text)
