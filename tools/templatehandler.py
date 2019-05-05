import pprint as pp
from tools.registry import DictRegistry

# Обработчик структуры сегмента
class TemplaterHandler(object):

    # State Machine Dict
    state_map = {
        'P0': {
            'CC': 'P0',
            'X': 'P0',

            'N': 'P1',
            'N0': 'P1',
            'PR': 'P1',
            'PR0': 'P1',

            'V': 'P2',
            'V<I>': 'P2',
            'V<P>': 'P2',
            'V<F>': 'P14',
            'V<U>': 'P2',

            'A': 'P6',
            'A0': 'P6',

            '-': 'P9',
            'который': 'P13',
            'V<C>': 'P12',
            'AV': 'P10',
            'SC': 'P11',

            # Result
            '#': 'X',
        },

        'P1': {
            'CC': 'P1',
            'SC': 'P1',
            'N': 'P1',
            'N0': 'P1',
            'PR': 'P1',
            'PR0': 'P1',
            'X': 'P1',

            '#': 'N',
            '-': 'P9',

            'A': 'P5',
            'A0': 'P5',

            'который': 'P7',

            'V': 'P3',
            'V<I>': 'P3',
            'V<P>': 'P3',
            'V<F>': 'P3',
            'V<C>': 'P3',
            'V<U>': 'P3',
        },

        'P2': {
            'N': 'P8',
            'N0': 'P8',

            # Any
            'X': 'P2',
            'PR': 'P2',
            'PR0': 'P2',
            'CC': 'P2',
            'SC': 'P2',
            'V': 'P2',
            'V<I>': 'P2',
            'V<P>': 'P2',
            'V<F>': 'P2',
            'V<C>': 'P2',
            'V<U>': 'P2',

            # Redirect
            '-': 'P9',
            'который': 'P7',

            '#': 'V_N',
        },

        'P3': {
            # Any
            'CC': 'P3',
            'SC': 'P3',
            'V': 'P3',
            'V<I>': 'P3',
            'V<P>': 'P3',
            'V<F>': 'P3',
            'V<C>': 'P3',
            'V<U>': 'P3',
            'X': 'P3',

            # Redirect
            'N': 'P4',
            'N0': 'P4',
            'PR': 'P4',
            'PR0': 'P4',
            'который': 'P7',

            '-': 'P9',

            '#': 'N_V',
        },

        'P4': {
            # Any
            'CC': 'P4',
            'SC': 'P4',
            'V': 'P4',
            'V<I>': 'P4',
            'V<P>': 'P4',
            'V<F>': 'P4',
            'V<C>': 'P4',
            'V<U>': 'P4',
            'N': 'P4',
            'N0': 'P4',
            'PR': 'P4',
            'PR0': 'P4',
            '-': 'P4',
            'X': 'P4',
            'который': 'P4',
            # Result
            '#': 'N_V_N',
        },

        'P5': {
            'V': 'P3',
            'V<I>': 'P3',
            'V<P>': 'P3',
            'V<F>': 'P3',
            'V<C>': 'P3',
            'V<U>': 'P3',

            # Any
            'X': 'P5',
            'AV': 'P5',
            'N': 'P5',
            'N0': 'P5',
            'CC': 'P5',
            # Result
            '#': 'A0',
        },

        'P6': {
            'V': 'P3',
            'V<I>': 'P3',
            'V<P>': 'P3',
            'V<F>': 'P3',
            'V<C>': 'P3',
            'V<U>': 'P3',

            # Any
            'X': 'P6',
            'AV': 'P6',
            'N': 'P6',
            'N0': 'P6',
            'PR': 'P6',
            'PR0': 'P6',
            'CC': 'P6',
            'SC': 'P6',

            # Redirect!
            '-': 'P9',
            'который': 'P7',

            '#': 'A0',
        },

        'P7': {
            # Any
            'X': 'P7',
            'CC': 'P7',
            'V': 'P7',
            'V<I>': 'P7',
            'V<P>': 'P7',
            'V<F>': 'P7',
            'V<C>': 'P7',
            'V<U>': 'P7',
            'который': 'P7',
            '-': 'P7',


            'N': 'P7',
            'N0': 'P7',
            'PR': 'P7',
            'PR0': 'P7',

            '#': 'N_который_V_N',
        },

        'P8': {
            # Any
            'PR': 'P8',
            'PR0': 'P8',
            'N': 'P8',
            'N0': 'P8',
            'X': 'P8',
            # Redirect
            'CC': 'P2',
            'SC': 'P2',
            # Redirect (sometimes error of N_V_N detected)
            'V': 'P4',
            'V<I>': 'P4',
            'V<P>': 'P4',
            'V<F>': 'P4',
            'V<C>': 'P4',
            'V<U>': 'P4',
            # Redirect
            '-': 'P9',
            'который': 'P13',

            # Result
            '#': 'V_N',
        },

        'P9': {
            'CC': 'P9',
            'SC': 'P9',
            'N': 'P9',
            'N0': 'P9',
            'PR': 'P9',
            'PR0': 'P9',
            'X': 'P9',

            'A': 'P9',
            'A0': 'P9',

            'V': 'P9',
            'V<I>': 'P9',
            'V<P>': 'P9',
            'V<F>': 'P9',
            'V<C>': 'P9',
            'V<U>': 'P9',

            'AV': 'P9',
            '-': 'P9',

            # Result
            '#': 'N_-_N',
        },

        'P10': {
            # Any
            'X': 'P10',
            'AV': 'P10',
            'CC': 'P10',
            # Result
            '#': 'AV',
        },

        'P11': {
            # Any
            'X': 'P11',
            'PR': 'P11',
            'PR0': 'P11',
            'N': 'P11',
            'N0': 'P11',
            'CC': 'P11',
            'SC': 'P11',
            'V': 'P11',
            'V<I>': 'P11',
            'V<P>': 'P11',
            'V<F>': 'P11',
            'V<C>': 'P11',
            'V<U>': 'P11',
            'AV': 'P11',
            'A': 'P11',
            'A0': 'P11',
            # Different (?)
            '-': 'P9',
            'который': 'P7',
            # Result
            '#': 'SC',
        },

        'P12': {
            # Any
            'PR': 'P12',
            'PR0': 'P12',
            'N': 'P12',
            'N0': 'P12',
            'CC': 'P12',
            'V': 'P12',
            'V<I>': 'P12',
            'V<P>': 'P12',
            'V<F>': 'P12',
            'V<C>': 'P12',
            'V<U>': 'P12',
            'AV': 'P12',
            'A': 'P12',
            'A0': 'P12',
            'X': 'P12',

            # Result
            '#': 'V<C>',
        },

        'P13': {
            # Any
            'PR': 'P13',
            'PR0': 'P13',
            'N': 'P13',
            'N0': 'P13',
            'CC': 'P13',
            'SC': 'P13',
            'V': 'P13',
            'V<I>': 'P13',
            'V<P>': 'P13',
            'V<F>': 'P13',
            'V<C>': 'P13',
            'V<U>': 'P13',
            'AV': 'P13',
            'A': 'P13',
            'A0': 'P13',
            'X': 'P13',
            'который': 'P13',
            '-': 'P13',

            # Result
            '#': 'который_V_N'
        },

        'P14': {
            # Any
            'PR': 'P14',
            'PR0': 'P14',
            'N': 'P14',
            'N0': 'P14',
            'CC': 'P14',
            'SC': 'P14',
            'V': 'P14',
            'V<I>': 'P14',
            'V<P>': 'P14',
            'V<F>': 'P14',
            'V<C>': 'P14',
            'V<U>': 'P14',
            'AV': 'P14',
            'A': 'P14',
            'A0': 'P14',
            'X': 'P14',
            'который': 'P14',
            '-': 'P14',

            # Result
            '#': 'V_N'
        },
    }

    # For Debug buffering of State Machine
    tracking = ""

    def __init__(self):
        self.registry = DictRegistry()
        self.can_print = False

    def addTemplateToSegments(self, segments):

        #pp.pprint(segments)
        #exit(0)

        for segment in segments:

            # DEBUGGER -----------------------------------\
            self.can_print = segment['id'] == 222

            if False and segment['text'].find('-')>=0:
                pp.pprint(segment['morph'])
                exit(0)
            #---------------------------------------------/

            tmp, is_legal = self.extractTemplate(segment, True)

            if self.can_print and False:
                pp.pprint(segment['morph'])
                exit(0)

            if not is_legal and tmp != "DROPPED":
                #print("DEBUGGER addTemplate\n")
                #print("###: '{}'".format(str(tmp)))
                #pp.pprint(segment['morph'])
                #exit(0)

                segment['template'] = 'UNKNOWN'
                continue

            segment['template'] = tmp
            if segment['type'] == 'UNKNOWN':
                tmp += '_#'

                self.tracking = tmp + " => "
                segment['type'] = self.templateReduction(tmp, 'P0')
                segment['tracking'] = self.tracking

        return segments

    def extractTemplate(self, segment, is_ext_verb=False):
        # (template)
        template = (segment['text'], False)
        is_legal = True

        if segment['type'] in self.registry.drop_segments:
            return ("DROPPED", False)

        data_udpipe = segment['morph']
        is_collect_adj = not self.havePOS(data_udpipe, 'VERB')
        is_collect_adv = (not self.havePOS(data_udpipe, 'NOUN')) and is_collect_adj
        is_collect_x = segment['text'].find('-') > 0;

        is_first = True
        is_last = False

        series = []
        last_token = None

        counter = 0
        mlen = len(data_udpipe)
        last_id = int(data_udpipe[mlen-1]['id'])

        for item in data_udpipe:
            counter += 1
            is_last = counter == mlen
            pos = item['pos']

            #if pos == "DET" and counter == 1:
            #    pos = "NOUN"

            is_append = False

            # Drop separators
            if item['mark'] == 'S':
                is_first = False
                continue
            elif pos=='NOUN':
                # For 'n' (unknown) tokens
                if 'grammar' not in item:
                    continue

                if 'Case' not in item['grammar'] or len(item['grammar'])==0:
                    continue

                addon = 'N'
                if item['grammar']['Case'] == 'Nom' or item['grammar']['Case'] == 'Acc':
                    addon = 'N0'
                if last_token != addon and (last_token != 'PR0' and last_token != 'PR'):
                    # Replace N by Main Noun
                    if addon == 'N0' and last_token == 'N':
                        series = series[:-1]
                    if addon == 'N' and last_token == 'N0':
                        continue
                    is_append = True
            elif pos=='PRON':
                addon = 'PR'
                if item['lemma']=='который':
                    addon = item['lemma']
                if addon == 'PR' and (last_token == 'N0' or last_token == 'N'):
                    continue
                if addon != 'который' and 'Case' in item['grammar']:
                    if item['grammar']['Case'] == 'Nom':
                        addon = 'PR0'

                is_append = last_token != addon
            # WARN: Ignore VERB in NP!!!
            elif pos=='VERB': # and item['mark']=='O':
                addon = 'V'
                if 'grammar' not in item:
                    continue

                # Experimental --------------------------\
                if 'VerbForm' in item['grammar']:
                    addon += '<' + item['grammar']['VerbForm'][0] + '>'
                else:
                    addon += '<U>'
                #---------------------------------------/

                is_append = True

                # DEBUGGER
                if False:
                    mess = '> ' + item['text']
                    if 'altered' in item:
                        mess += ' (ALTERED)'
                    print(mess)
                    #pp.pprint(item['grammar'])

            elif item['lemma']=='-': # item['lemma']=='который' or
                addon = item['lemma']
                is_append = True
            # Only outside from NP
            elif (pos=='CCONJ' or pos=='SCONJ') and item['mark']=='O':
                addon = pos[:2]
                is_append = last_token != addon
            elif is_collect_adv and (pos=='ADV' or pos=='NUM'):
                addon = 'AV'
                is_append = True
            elif is_collect_x and pos=='X':
                addon = 'X'
                is_append = True
            # Last check!!!
            elif is_collect_adj and pos=='ADJ':
                # ПРОПИСАТЬ ЛОГИКУ КОМБИНАЦИЙ
                # - is_last/si_first / ids / ...
                # Цель: вычленить рутовый прилагательные
                parent_id = int(item['parent'])
                self_id = int(item['id'])

                # (self_id > parent_id or 'altered' in item)
                if (is_first and (self_id > parent_id)) or (is_last and parent_id >= last_id):
                    addon = 'A0'
                    is_append = True

            # Add symbol
            if is_append:
                series.append(addon)
                last_token = addon

            if is_first:
                is_first = False

        insert = '_'.join(series)

        if len(insert)==0 or insert == 'CC':
            if self.havePOS(segment['morph'], 'ADJ'):
                insert = 'A'
            elif self.havePOS(segment['morph'], 'SCONJ'):
                insert = 'SC'
            elif self.havePOS(segment['morph'], 'X'):
                insert = 'X'
            else:
                is_legal = False
                insert = segment['text']
                #print(segment['morph'])

        template = (insert, is_legal)

        return template

    def havePOS(self, morph, target_pos):
        result = False
        for item in morph:
            if item['pos'] == target_pos:
                result = True
                break
        return result

    def templateReduction(self, template, start_state = 'P0'):
        inputs = template.split('_')
        state = start_state
        for input in inputs:
            self.tracking += ' ' + state
            state = self.getState(state, input)
        return state

    def getState(self, state, input):

        # Guard
        if state not in self.state_map:
            print("Unrecognized state: '%s' on '%s'\n" % (input, state))
            exit(0)

        if input not in self.state_map[state]:
            #print("Unrecognized link: '%s' on '%s'\n" % (input, state))
            return state

        return self.state_map[state][input]
