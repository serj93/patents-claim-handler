from ufal.udpipe import Model, Pipeline, ProcessingError
from tools.morphology.mystemtool import MystemTool
from tools.appconfig import AppConfig

import string, os, re, sys, time
import pprint as pp

# Usage: input_format(tokenize|conllu|horizontal|vertical) output_format(conllu) model_file
class UdPipeTool(object):

    # Preparing
    symbol_filter = ['°','%','=']
    exclude = set(string.punctuation)

    # Singleton
    __instance = None

    def __new__(cls, modelname = "", input_format = "tokenize", output_format = "conllu"):
        # russian-syntagrus-ud-2.3-181115.udpipe
        # russian-syntagrus-ud-2.0-170801.udpipe
        if UdPipeTool.__instance is None:
            UdPipeTool.__instance = object.__new__(cls)

            # Load model
            start_time = time.time()

            if not modelname:
                UdPipeTool.config = AppConfig()
                modelname = UdPipeTool.config.UDPIPE_MODEL

            sys.stdout.write('Loading model ...\n')
            UdPipeTool.__instance.model = Model.load(modelname)
            if not UdPipeTool.__instance.model:
                sys.stderr.write("Cannot load model from file '%s'\n" % modelname)
                sys.exit(1)
            #sys.stdout.write('done.\n')

            # Prepare pipeline
            UdPipeTool.__instance.pipeline = Pipeline(UdPipeTool.__instance.model, input_format, Pipeline.DEFAULT, Pipeline.DEFAULT, output_format)
            UdPipeTool.__instance.error = ProcessingError()
            if UdPipeTool.__instance.error.occurred():
                sys.stderr.write("An error occurred when running run_udpipe: ")
                sys.stderr.write(error.message)
                sys.stderr.write("\n")
                sys.exit(1)

            UdPipeTool.__instance.tmystem = MystemTool()

            sys.stdout.write("UdPipe model was initiated %s sec.\n" % (time.time() - start_time))

        return UdPipeTool.__instance

    def loadPipeline(self, input_format, output_format):
        #sys.stdout.write('Loading pipeline: \n')
        self.pipeline = Pipeline(self.model, input_format, Pipeline.DEFAULT, Pipeline.DEFAULT, output_format)
        self.error = ProcessingError()
        if self.error.occurred():
            sys.stderr.write("An error occurred when running run_udpipe: ")
            sys.stderr.write(error.message)
            sys.stderr.write("\n")
            sys.exit(1)
        #sys.stdout.write('done.\n')

    def getMorphology(self, text):
        # Process data
        processed = self.pipeline.process(text, self.error)
        if self.error.occurred():
            sys.stderr.write("An error occurred when running run_udpipe: ")
            sys.stderr.write(self.error.message)
            sys.stderr.write("\n")
            sys.exit(1)
        return processed

    def analyzeText(self, text):
        processed = self.getMorphology(text)
        #pp.pprint(processed)
        #exit(0)

        processed = processed.split(os.linesep)
        #pp.pprint(processed)
        #exit(0)

        # Fix problems with '-'
        if text.find('-') > 0:
            processed = self.dashCorrection(processed)

        tokens = []
        for line in processed:
            if len(line)==0 or line[0]=='#':
                continue

            token_parts = line.split('\t')

            token = {}
            token['id'] = token_parts[0]
            token['text'] = token_parts[1]
            token['lemma'] = self.tmystem.lemmatize(token_parts[1].rstrip(os.linesep))[0].rstrip(os.linesep)
            #token['lemma'] = token_parts[2]


            # Fix symbol reaction
            if token['lemma'] in self.symbol_filter:
                token['pos'] = 'SYM'
            else:
                token['pos'] = token_parts[3]

            grammar = {}
            grammar_parts = token_parts[5].split('|')
            for grammema in grammar_parts:
                if grammema.find('=')>0:
                    key, value = grammema.split('=')
                    grammar[key] = value

            if token['lemma'] not in self.exclude:
                token['grammar'] = grammar

            token['parent'] = token_parts[6]
            token['deprel'] = token_parts[7]
            tokens.append(token)

        return tokens

    def analyzeTextAndSplit(self, text):
        """
        Get Morphology and split it by comma
        (for segmentation preparing)
        :return: list of pairs of (text, morph:[])
        """
        processed = self.getMorphology(text)
        #pp.pprint(processed)
        #exit(0)

        processed = processed.split('\n')

        # Fix problems with '-'
        if text.find('-') > 0:
            processed = self.dashCorrection(processed)

        presegments = []
        tokens = []
        sub_text = ""

        #pp.pprint(processed)
        #exit(0)

        for line in processed:
            if len(line)==0 or line[0]=='#':
                continue

            token_parts = line.split('\t')

            # Splitter!
            if token_parts[2] == ',' and len(sub_text) > 0:
                presegments.append((sub_text, tokens))
                tokens = []
                sub_text = ""
                continue

            token = {}
            token['id'] = token_parts[0]
            token['text'] = token_parts[1]

            word = token_parts[1].rstrip(os.linesep)
            token['lemma'] = self.tmystem.lemmatize(word)[0].rstrip(os.linesep)
            #token['lemma'] = token_parts[2]

            # Fix symbol reaction
            if token['lemma'] in self.symbol_filter:
                token['pos'] = 'SYM'
            else:
                token['pos'] = token_parts[3]

            # Fix replaces
            if token['lemma'].find('REP')==0:
                token['pos'] = 'X'
                token['grammar'] = {}

            grammar = {}
            grammar_parts = token_parts[5].split('|')
            for grammema in grammar_parts:
                if grammema.find('=')>0:
                    key, value = grammema.split('=')
                    grammar[key] = value

            if token['lemma'] not in self.exclude:
                token['grammar'] = grammar

            token['parent'] = token_parts[6]
            token['deprel'] = token_parts[7]

            sub_text += token['text']

            space = token_parts[9]
            if not space=='SpaceAfter=No':
                sub_text += ' '

            tokens.append(token)

        # Splitter - last part!
        if len(sub_text) > 0:
            presegments.append((sub_text, tokens))

        #pp.pprint(presegments)
        #exit(0)

        return presegments

    def dashCorrection(self, processed):
        """
        Convolution of words throught '-' (like 'объемно' '-' 'упругий' => 'объемно-упругий')
        Available 'SpaceAfter=No' at '-' required
        """
        processed_len = len(processed)
        ex_lines = []
        replaces = {}

        for index in range(0, processed_len):
            line = processed[index]

            if len(line)==0 or line[0]=='#':
                continue

            token_parts = line.split('\t')
            text = token_parts[1]
            pos = token_parts[3]
            space = token_parts[9]

            # Need remember
            if text[-1:]=='-' and space=='SpaceAfter=No':
                # Connect right border
                next_index = index + 1
                if next_index < processed_len:
                    line2 = processed[next_index]
                    token_parts = line2.split('\t')
                    token_parts[1] = text + token_parts[1]

                    if text=='-':
                        # Check previouse border
                        prev_index = index - 1
                        if prev_index > 0:
                            line0 = processed[prev_index]
                            if not (len(line0)==0 or line0[0]=='#'):
                                prev_parts = line0.split('\t')
                                text = prev_parts[1]
                                token_parts[1] = text + token_parts[1]
                                ex_lines.append(prev_index)

                    ex_lines.append(index)
                    replaces.update({next_index:'\t'.join(token_parts)})
                    continue

            elif text[0]=='-' and pos == 'ADJ':
                # Check previouse border
                prev_index = index - 1
                if prev_index > 0:
                    line0 = processed[prev_index]
                    if not (len(line0)==0 or line0[0]=='#'):
                        prev_parts = line0.split('\t')
                        text = prev_parts[1]
                        token_parts[1] = text + token_parts[1]
                        ex_lines.append(prev_index)

                    replaces.update({index:'\t'.join(token_parts)})
                    continue

            elif text[0]=='-' and pos == 'NOUN':
                # Check previouse border
                prev_index = index - 1
                if prev_index > 0:
                    line0 = processed[prev_index]
                    if not (len(line0)==0 or line0[0]=='#'):
                        prev_parts = line0.split('\t')
                        text0 = prev_parts[1]
                        token_parts[1] = text0 + token_parts[1]
                        ex_lines.append(prev_index)

                # Lemma correction
                token_parts[2] = self.tmystem.lemmatize(text[1:].rstrip(os.linesep))[0].rstrip(os.linesep)
                replaces.update({index:'\t'.join(token_parts)})
                continue

            elif text[0]=='-' and pos == 'VERB':
                # Check previouse border
                prev_index = index - 1
                if prev_index > 0:
                    line0 = processed[prev_index]
                    if not (len(line0)==0 or line0[0]=='#'):
                        prev_parts = line0.split('\t')
                        text0 = prev_parts[1]
                        token_parts[1] = text0 + token_parts[1]
                        ex_lines.append(prev_index)

                # Lemma correction
                token_parts[2] = self.tmystem.lemmatize(text[1:].rstrip(os.linesep))[0].rstrip(os.linesep)

                replaces.update({index:'\t'.join(token_parts)})
                continue

            elif text[0]=='-' and pos == 'ADP':
                # Check previouse border
                prev_index = index - 1
                if prev_index > 0:
                    line0 = processed[prev_index]
                    if not (len(line0)==0 or line0[0]=='#'):
                        prev_parts = line0.split('\t')
                        text0 = prev_parts[1]
                        token_parts[1] = text0 + token_parts[1]
                        ex_lines.append(prev_index)

                # Root word (СВЧ-диод => диод)
                word = text[1:]

                # Lemma correction
                token_parts[2] = self.tmystem.lemmatize(word.rstrip(os.linesep))[0].rstrip(os.linesep)

                data_mystem = self.tmystem.analyze(text)
                fword, link = self.tmystem.findWordInMystemData(data_mystem, word)
                pref_pos = self.tmystem.getMystemPOS(fword)
                if pref_pos == 'S':
                    grammar = self.tmystem.convertM2UGrammar(fword)
                    token_parts[3] = 'NOUN'

                    new_str_grammar = ''
                    for gram_id in grammar:
                        gram_val = grammar[gram_id]
                        new_str_grammar += '{}={}|'.format(gram_id, gram_val)
                    new_str_grammar = new_str_grammar.rstrip('|')

                    if new_str_grammar:
                        token_parts[5] = new_str_grammar

                replaces.update({index:'\t'.join(token_parts)})
                continue


        new_processed = []
        for index in range(0, processed_len):
            line = processed[index]
            if index in ex_lines or len(line)==0 or line[0]=='#':
                continue
            if index in replaces:
                line = replaces[index]
            new_processed.append(line)

        return new_processed
