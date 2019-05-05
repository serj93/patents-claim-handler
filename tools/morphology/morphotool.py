import pprint as pp
import re, sys

from tools.npchunker import NPChunker
from tools.morphology.udpipetool import UdPipeTool
from tools.morphology.mystemtool import MystemTool
from tools.registry import DictRegistry

# Агрегатор морфологической информации
class MorphoTool(object):

    # Singleton
    __instance = None

    def __new__(cls):
        if MorphoTool.__instance is None:
            MorphoTool.__instance = object.__new__(cls)

            MorphoTool.__instance.chunker = NPChunker()
            MorphoTool.__instance.tudpipe = UdPipeTool()
            MorphoTool.__instance.tmystem = MystemTool()
            MorphoTool.__instance.registry = DictRegistry()

        return MorphoTool.__instance

    def enrichSegments(self, segments):
        """
        Add morphology to each segment
        :param: segments: List of segments (dict)
        :return: The same list with mophology
        """

        for segment in segments:
            text = segment['text']
            # WARN: General morphological data from SEGMENTER
            data_udpipe = segment['morph']

            #pp.pprint(data_udpipe)
            #pp.pprint(text)
            #exit(0)

            # Drop separator segments only ----------------------------------\
            text_without_sep = self.dropSeparators(text, data_udpipe)
            if len(text_without_sep)==0:
                segment['type'] = 'SEPARATOR'
                segment['segm'] = text
                segment['numbered'] = self.getNumerableText(segment)
                continue
            #----------------------------------------------------------------/

            # Marked "purpose"-segments -------------------------------------\
            if self.isPurposeSegment(data_udpipe):
                segment['type'] = 'PURPOSE'
                segment['segm'] = text
                segment['numbered'] = self.getNumerableText(segment)
                continue
            #----------------------------------------------------------------/

            # Marked "named"-segments -------------------------------------\
            if self.isNamedSegment(data_udpipe):
                segment['type'] = 'NAMED'
                segment['segm'] = text
                segment['numbered'] = self.getNumerableText(segment)
                continue
            #----------------------------------------------------------------/

            # Decorator of Mystem!!!
            data_mystem = self.tmystem.analyze(text)
            data_mystem = self.cooperateSources(data_mystem, data_udpipe)

            #if segment['id'] == 13:
            #    pp.pprint(data_udpipe)
            #    pp.pprint(data_mystem)
            #    exit(0)

            self.fixWordsByMystem(data_mystem, data_udpipe, text)

            text_sentence, features = self.chunker.prepareFeatures(data_mystem)
            segmented, bio = self.chunker.makePrediction(text_sentence, features)

            self.insertBIO(data_udpipe, bio, data_mystem)

            # Print info -----------------------------\
            #self.printMarkedWords(data_udpipe)
            #print(segmented)
            #-----------------------------------------/

            # Add info to segment
            segment['segm'] = segmented
            segment['numbered'] = self.getNumerableText(segment)
            segment['morph'] = data_udpipe

            #pp.pprint(segment)
            #exit(0)

        # Fix VERBS after all (experimental)
        segments = self.fixWordsAfterAll(segments)

        return segments

    def getNumerableText(self, segment):
        result = ''
        if 'morph' in segment:
            for token in segment['morph']:
                result += '{} {}  '.format(token['text'],token['id'])
        result = result.rstrip()
        return result

    def isNamedSegment(self, data_udpipe):
        """
        Find marker of named segments
        by 'называемых' (begin) atc...
        """
        result = False
        for word in data_udpipe:
            lemma = word['lemma']
            if lemma == 'называть':
                result = True

        return result

    def isPurposeSegment(self, data_udpipe):
        """
        Find marker of purpose (technical function)
        by 'цель' or 'для' (begin) atc...
        """
        result = False
        isFirst = True
        for word in data_udpipe:
            lemma = word['lemma']

            if lemma == 'цель':
                result = True
                break

            if isFirst:
                isFirst = False

                if lemma == 'предназначать':
                    result = True
                    break

                if lemma == 'для' and not self.isThereTargetVerb(data_udpipe):
                    result = True
                    break

        return result

    def isThereTargetVerb(self, udpipe_data):
        """
        Проверка наличия целевых глаголов в предложении
        """
        result = False
        for token in udpipe_data:
            if token['pos'] == 'VERB':
                if self.registry.isLemmaInCompDict(token['lemma']) or \
                self.registry.isLemmaInConnDict(token['lemma']):
                    result = True
                    break

        return result

    def printMarkedWords(self, data_udpipe):
        printed = []
        for item in data_udpipe:
            append = item['text']
            #if item['mark'].isdigit():
            append += '('+item['mark']+')'
            printed.append(append)
        print(' '.join(printed))

    def insertBIO(self, data_udpipe, bio, data_mystem):
        #pp.pprint(data_udpipe)
        #pp.pprint(bio)
        #sys.exit(1)

        bio_len = len(bio)
        udpipe_len = len(data_udpipe)
        mystem_len = len(data_mystem)

        if udpipe_len != bio_len:
            #sys.stderr.write("Something went wrong: BIO len more then words.\n")

            # Default markers
            for token in data_udpipe:
                if 'mark' in token:
                    continue
                token['mark'] = 'O'
            return

            #pp.pprint(data_udpipe)
            #pp.pprint(bio)
            #sys.exit(1)

        bio_index = -1
        np_mum = 1
        saving = False
        for token in data_udpipe:
            bio_index += 1

            # only beginning!
            if 'mark' in token:
                continue
            try:
                bio_item = bio[bio_index]
            except:
                sys.stderr.write("Something went wrong: BIO index bad.\n")
                pp.pprint('udpipe_len: ' + str(udpipe_len))
                pp.pprint('mystem_len: ' + str(mystem_len))
                pp.pprint(bio)
                exit(1)

            if bio_item == 'O':
                token['mark'] = 'O'
                if saving:
                    np_mum += 1
                    saving = False
            elif bio_item == 'B':
                saving = True
                token['mark'] = str(np_mum)
            elif bio_item == 'I':
                token['mark'] = str(np_mum)

        #pp.pprint(data_udpipe)
        #sys.exit(0)

    def cooperateSources(self, data_mystem, data_udpipe):
        """
        Compress difference between data and fix mystem issues
        """
        to_delete = []
        indexes = range(0, len(data_mystem))
        ud_point = 0
        start_fix = -1
        buffer = ''

        for i in indexes:
            item = data_mystem[i]

            if item['text'] == ' ' or item['text'] == '\n':
                #to_delete.append(i)
                continue

            item['text'] = item['text'].strip()

            if item['text'] == data_udpipe[ud_point]['text']:
                if 'mark' in data_udpipe[ud_point]:
                    data_mystem[i]['mark'] = data_udpipe[ud_point]['mark']
                ud_point += 1
                continue

            # Else find difference
            if buffer == '':
                start_fix = i
            buffer += item['text']
            if not i == start_fix:
                to_delete.append(i)
            if buffer == data_udpipe[ud_point]['text']:
                data_mystem[start_fix]['text'] = buffer
                buffer = ''
                start_fix = -1
                ud_point += 1

        # Cleaning
        new_data_mystem = []
        for i in indexes:
            if i not in to_delete:
                new_data_mystem.append(data_mystem[i])
        return new_data_mystem

    def dropSeparators(self, text, data_udpipe):
        """
        Marked separators in segment beginning
        Sample: 'а[S] также[S] последовательно соединенные...'
        """
        sub_text = text
        for sep in self.registry.separators:
            if text.find(sep)==0:
                sub_text = text[len(sep)+1:]
                if sep.find(' ')>0:
                    index = 0
                    for part in sep.split(' '):
                        if part == data_udpipe[index]['text']:
                            data_udpipe[index]['mark'] = 'S'
                            index += 1
                else:
                    data_udpipe[0]['mark'] = 'S'
        return sub_text

    def fixWordsAfterAll(self, segments):
        """
        If VERB in NP and have Case => ADV
        """
        for segment in segments:
            if segment['type'] in self.registry.drop_segments:
                continue
            # WARN: General morphological data from SEGMENTER
            data_udpipe = segment['morph']

            for item in data_udpipe:
                if (item['pos'] == 'PART' or item['pos'] == 'ADJ') and 'can_be' in item:
                    if item['can_be'][0] == 'NOUN':
                        item['pos'] = 'NOUN'
                        item['altered'] = True
                        item['grammar'] = item['can_be'][1]
                    # Clear after all
                    del item['can_be']

                elif item['pos'] == 'VERB' or item['pos'] == 'ADV':
                    isParentForADV = self.isParentFor(data_udpipe, item['id'], 'ADV')

                    #print("{} for parent '{}'".format(isParentForADV, item['lemma']))

                    # Mandatory condition
                    if not isParentForADV:
                        if 'can_be' in item:
                            # For S only in NP!!!
                            if item['can_be'][0] == 'NOUN' and item['mark'].isdigit():
                                item['pos'] = 'NOUN'
                                item['altered'] = True
                                item['grammar'] = item['can_be'][1]

                            # Clear after all
                            del item['can_be']

                        # Case of ADJ in NP and
                        """
                        isChildOfNOUN = self.isChildOf(data_udpipe, item['parent'], 'NOUN')
                        if 'Case' in item['grammar'] and isChildOfNOUN and item['mark'].isdigit():
                            item['pos'] = 'ADJ'
                            item['altered'] = True
                            if 'VerbForm' in item['grammar']:
                                del item['grammar']['VerbForm']
                        """


            segment['morph'] = data_udpipe

        return segments

    def fixWordsByMystem(self, data_mystem, data_udpipe, segm_text):
        '''
        Set Mystem morph for VERB and ADJ form`s
        '''
        convert_matrix = {'A':'ADJ', 'V':'VERB', 'S':'NOUN'}

        mlen = len(data_udpipe)
        last_id = int(data_udpipe[mlen-1]['id'])
        first_id = int(data_udpipe[0]['id'])

        checked_pos = ['VERB', 'ADJ', 'ADV', 'PART']

        for item in data_udpipe:
            # Добавление морфлоги для "который" (нет GNC для привязки!)
            if item['lemma'] == 'который':
                fword, link = self.tmystem.findWordInMystemData(data_mystem, item['text'])
                # Warning! Rewrite with Case (will be from Mystem)
                if fword:
                    item['grammar'] = self.tmystem.convertM2UGrammar(fword)
            # Коррекция морфологии глагола (и другие)
            elif item['pos'] in checked_pos:
                fword, link = self.tmystem.findWordInMystemData(data_mystem, item['text'])
                if fword:
                    prefer_POS = self.tmystem.getMystemPOS(fword)
                    if prefer_POS in convert_matrix:
                        isParent = self.isParentFor(data_udpipe, item['id'], 'ADV')
                        parent_id = int(item['parent'])

                        # Check on Mystem error ---------------------------------\
                        if prefer_POS=='A':
                            # Correction - VERB with ADV ----------------------\
                            if isParent:
                                data_mystem[link]['analysis'][0]['gr'] = 'V'
                                if item['pos'] == 'ADJ':
                                    item['pos'] = 'VERB'
                                    item['altered'] = True
                                continue
                            # -------------------------------------------------/

                            # If VERB is root in himself in segment ----------------\
                            #print('Check ' + item['text'] + ' on ' + prefer_POS)
                            data_udpipe_2 = self.tudpipe.analyzeText(segm_text)

                            isRoot = self.isWordRoot(data_udpipe_2, item['text'])

                            #if item['lemma'] == 'соединять':
                            #    print(isRoot)
                            #    print(item['pos'])
                            #    pp.pprint(data_udpipe_2[0])
                                #exit(0)

                            # Clear
                            del data_udpipe_2

                            if isRoot and item['pos']=='VERB':
                                #print('FINISH!!!!')
                                #exit(0)
                                continue
                            #------------------------------------------------------/

                            # Noun (?) parent in previous segment
                            # Depricated
                        #--------------------------------------------------------/

                        # Labeled X->NOUN for future checking -------------------\
                        if prefer_POS=='S':
                            item['can_be'] = ('NOUN', self.tmystem.convertM2UGrammar(fword))
                            continue
                        #--------------------------------------------------------/

                        # Default ADJ with NOUN parent IN SEGMENT ------------------------\
                        if prefer_POS=='V' and item['pos'] == 'ADJ' and not isParent:
                            isChild = self.isChildOf(data_udpipe, item['parent'], 'NOUN')
                            if isChild and parent_id > first_id and parent_id < last_id \
                            and item['lemma'] not in self.registry.can_be_verb:
                                #print(item['lemma'])
                                continue
                        # ----------------------------------------------------------------/

                        prefer_POS = convert_matrix[prefer_POS]
                        if not prefer_POS == item['pos']:

                            # Exception: бывают краткие формы (root)
                            if item['pos'] == 'VERB':
                                if item['deprel'] == 'root': # or item['deprel'] == 'acl':
                                    continue

                            # DEBUGGER ---------------------------------------\
                            if False:
                                print(item['text'] + ' on ' + prefer_POS)
                                print("FROM "+item['pos']+" TO " + prefer_POS)
                                print(item['text'])
                                print(segm_text)
                                print("")
                            #-------------------------------------------------/

                            item['pos'] = prefer_POS
                            item['altered'] = True
                            item['grammar'] = self.tmystem.convertM2UGrammar(fword)

                            #pp.pprint(fword)
                            #print("----------------------------------------")

    def isWordRoot(self, data_udpipe, word):
        result = False
        for item in data_udpipe:
            if item['parent'] == '0':
                result = item['text'] == word
            break
        return result

    def isChildOf(self, data_udpipe, parent_id, target_pos):
        result = False
        for item in data_udpipe:
            if item['id'] == parent_id and item['pos'] == target_pos:
                result = True
                break
        return result

    def isParentFor(self, data_udpipe, parent_id, child_pos):
        """
        Check if parent word have child with target pos
        :return: True | False
        """
        result = False
        for item in data_udpipe:
            if item['id'] == parent_id:
                continue
            if item['parent']==parent_id and item['pos']==child_pos:
                result = True
                break
        return result
