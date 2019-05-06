import pprint as pp
import re

from tools.preprocessor import TextPreprocessor
from tools.morphology.udpipetool import UdPipeTool

# Сегментатор
class ClaimSegmenter(object):

    def __init__(self):
        self.preproc = TextPreprocessor()
        # Segments counter (intervalue)
        self.s_counter = 0
        # Surrogat links Counter (intervalue)
        self.l_counter = 0
        # For s
        self.udpipe = UdPipeTool()
        # Replacements in general
        self.replacements = {}

    # Futute Work!!!
    def makeSurrogatLinks(self, text):
        replacements = {}

        patterns = [
            r"(об\s?/\s?с)",
            # λ/8 | 3/об.
            r"([A-Z<>\dλ]+\s?/([\d+],?\d{0,}|[а-я]+\.?))",
            # 1,4·10-5
            r"([±+-]?\d+,?\d+[·*]\d+-?\+?\d+)",
            # S=W=0,00042λ | α1=55-65° | LK/LД=0,22-1,1 | d2/d1=1,0-1,5
            r"([A-Za-zА-Яа-я/\dαλ=]+=\d,?\d*[-λ…]?\d[,λ]?\d*[°]?)",
            # 28b, 28′b
            r"(\d+[′']?[a-zфа-я]?(,\s\d+[′']?[a-zфа-я]?)+)",
            # 0,66…0,69 | ±0,05
            r"([±]?\d+,?\d*(\.{0,3}|…|-|\s-\s)\d+,?\d+[°%λ]?[CС]?)",
            # 0,66 | ±10° | ±0,05 | 0,5f (старая: r"([±]?\d+,?\d+[°f%λ]?)")
            r"([±]?\d+[,\.-]?\d*[°f%λ′']?([-ей]+|[CС]?))",
            # мас. % | мас.%
            r"([А-Яа-я]{1,4}\.\s?[%])",
            # Compare
            r"([A-Za-zА-Яа-я\d]+[<>=][A-Za-zА-Яа-я\d]+)",
        ]

        for pattern in patterns:
            result = re.findall(pattern, text)
            if result:
                for part in result:
                    if isinstance(part, tuple):
                        replace = part[0]
                    else:
                        replace = part

                    # Пропускаем просто числа
                    if replace.isdigit():
                        continue

                    self.l_counter += 1
                    label = "REP{} ".format(str(self.l_counter))

                    text = text.replace(replace, label, 1)
                    replacements[label] = replace

        if replacements:
            self.replacements.update(replacements)

        return text

    def wrapSegmentWithMorph(self, text_part, seg_part = 0):
        """
        Make segments from logical part of claim text, splitting on UdPipe
        :param: text_parts: Claim text (part)
        :param: type: 0 - general; 1 - distinctive part; 2 - restrictive part;
        :return: List of segments (dict)
        """
        if seg_part < 0 or seg_part > 2:
            seg_part = 0

        # Future work
        text_part = self.makeSurrogatLinks(text_part)

        if text_part.find(';') > 0:
            parts = text_part.split(';')
        else:
            parts = [text_part]

        segments = []
        for part in parts:

            seg_pairs = self.udpipe.analyzeTextAndSplit(part)
            for seg_pair in seg_pairs:
                # Start from 1 (0 is virtual root)
                self.s_counter += 1

                seg_text = seg_pair[0]
                seg_morph = seg_pair[1]

                seg_text = seg_text.strip(", ")
                if len(seg_text)==0:
                    continue

                # Create wrapper
                segment = {}
                segment['id'] = self.s_counter
                segment['text'] = seg_text
                segment['part'] = seg_part
                segment['morph'] = seg_morph
                segment['type'] = 'UNKNOWN'
                segments.append(segment)

        return segments

    def getSegments(self, text):
        """
        Split claim text by parts/;/,
        :param: text: Processed claim text
        :return: List of dict of each segment
        """
        segments = []
        self.s_counter = 0
        self.replacements = {}
        self.l_counter = 0
        text = text.rstrip('.')

        parts = self.preproc.splitByPattern(text)

        if len(parts)==1:
            segments = self.wrapSegmentWithMorph(parts[0])
        else:
            # Have two parts
            segments = self.wrapSegmentWithMorph(parts[0], seg_part = 1)
            segments += self.wrapSegmentWithMorph(parts[1], seg_part = 2)

        return segments, self.replacements
