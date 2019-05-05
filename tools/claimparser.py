import pprint as pp
import sys

from tools.preprocessor import TextPreprocessor
from tools.segmenter import ClaimSegmenter
from tools.morphology.morphotool import MorphoTool
from tools.templatehandler import TemplaterHandler
from tools.convhandler import ConvHandler
from tools.graphbuilder import GraphBuilder
from tools.extractor import SAOExtractor
from tools.structanalysis import StructuralAnalysis

# Парсер клеймов
class ClaimParser(object):

    MIN_TEXT_LENGTH = 100

    def __init__(self):
        self.preproc = TextPreprocessor()
        self.segmenter = ClaimSegmenter()
        self.morph = MorphoTool()
        self.thandler = TemplaterHandler()
        self.chandler = ConvHandler()
        self.gbuilder = GraphBuilder()
        self.extractor = SAOExtractor()
        self.sanalyzer = StructuralAnalysis()

    def run(self, text, fpath = ''):
        """
        Start claim processing
        :input: Text of one claim
        :output: List of extracted entities
        """

        # DEBUGGER
        if fpath:
            print('{}\n'.format(fpath))

        data = self.generateSegments(text)
        segments = data[0]
        replacements = data[1]

        if False and replacements:
            print("Replacements:")
            pp.pprint(replacements)

        #self.gbuilder.printSegmentGraph(segments)
        #exit(0)

        # DEBUGGER ----------------------------------------\
        if False:
            scope = range(0, len(segments))
            for i in scope:
                segment = segments[i]
                #if 'morph' in segment:
                #    del segments[i]['morph']
                #    pp.pprint(segment)
                #    exit(0)
                #continue

                print(segment['id'])
                print(segment['segm'])
                print(segment['numbered'])
                #continue

                pp.pprint(segment['template'])
                pp.pprint(segment['type'])
                pp.pprint(segment['link'])
                #if 'tracking' in segment:
                #    pp.pprint(segment['tracking'])
                if segment['id'] == 444:
                    pp.pprint(segment['morph'])
                    exit(0)
                    break
                tmp, is_legal = self.thandler.extractTemplate(segment, is_ext_verb=True)
                if not is_legal:
                    tmp = '###: ' + str(tmp)
                print('')
                continue
        # -------------------------------------------------/

        # Extract triplets
        generic_term, triplets = self.extractor.startExtraction(segments)

        if False:
            for triplet in triplets:
                print('S:: {}\nA:: {}\nO:: {}\n'.format(triplet['SBJ'], triplet['ACT'], triplet['OBJ']))
            print('\nTotal retrieved SAO: {}.\n'.format(len(triplets)))

        invent_data = self.sanalyzer.getDesignFeatures(segments, replacements, generic_term, triplets)

        if invent_data:
            #self.gbuilder.printInventGraph(invent_data)
            pass

        return invent_data

    def generateSegments(self, text):
        # Preprocessing
        text = self.preproc.startPreprocessing(text)
        # Separate text
        segments, replacements = self.segmenter.getSegments(text)
        # Add morphology
        segments = self.morph.enrichSegments(segments)
        # Calculate template & reduction
        segments = self.thandler.addTemplateToSegments(segments)
        # Get hierarchy
        segments = self.chandler.startConvolution(segments)

        return (segments, replacements)
