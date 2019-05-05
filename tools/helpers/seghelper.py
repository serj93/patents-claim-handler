import pprint as pp

# Вспомогательный класс обработки структур
class SegmentHelper(object):

    # Singleton
    __instance = None

    def __new__(cls):
        if SegmentHelper.__instance is None:
            SegmentHelper.__instance = object.__new__(cls)
        return SegmentHelper.__instance

    def findCaseInSegment(self, segment, poses = [], cases = []):
        '''
        Проверка наличия Pos<Case> в сегменте (проверка родителя GAP).
        return: None | <token_id>
        '''
        result = None
        if 'morph' in segment:
            for token in segment['morph']:
                if token['pos'] in poses:
                    case = self.getCase(token)
                    if case in cases:
                        result = token['id']
                        break
        return result

    def getCase(self, token):
        '''
        Падеж из морфологии segment['morph'].
        '''
        result = None
        if 'grammar' in token:
            if 'Case' in token['grammar']:
                result = token['grammar']['Case']
        return result

    def getGNC(self, token):
        """
        Dict of GNC from token
        :return: None | {'Gender', 'Number', 'Case'}
        """
        result = None
        if 'grammar' in token:
            result = {}
            if 'Case' in token['grammar']:
                result['Case'] = token['grammar']['Case']
            else:
                result['Case'] = None

            if 'Number' in token['grammar']:
                result['Number'] = token['grammar']['Number']
            else:
                result['Number'] = None

            if 'Gender' in token['grammar']:
                result['Gender'] = token['grammar']['Gender']
            else:
                result['Gender'] = None

        return result

    def getListIndexByVal(self, items, key, target_val):
        '''
        Индекс сегмента/морфологии по ИД; для корректного доступа по индексу.
        '''
        result = None
        for index in range(0, len(items)):
            if items[index][key] == target_val:
                result = index
                break
        return result

    def getListElementById(self, elements, target_id):
        '''
        Элемент сегмента/морфологии по ИД.
        '''
        result = None
        for element in elements:
            if element['id'] == target_id:
                result = element
                break
        return result
