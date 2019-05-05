import matplotlib.pyplot as plt
import networkx as nx

import pprint as pp

# Построение графа текста
class GraphBuilder(object):

    def __init__(self):
        pass

    def printInventGraph(self, invent_data):

        # Словарь терминов invent_data['terms']:
        #{'0.0': 'рекурсивный цифровой фильтр' }
        # Fixed keys: '0.0' - Родовое понятие (РП)
        #---------------------------------------------------------
        # Словарь связей invent_data['verbs']:
        #{'1':
        #    {'text': 'соединять',
        #     'type': 'conn' | 'comp',
        #     'prep':
        #       {1: 'c'}}}
        # Fixed keys:
        #   '0.0' - Неявное отношения потомка к родителю
        #           Пример: статор..., полые цилиндры статора ...
        #---------------------------------------------------------
        # Карта связей invent_data['map']:
        #{<sbj_key>:
        #    {<obj_key>:
        #       (<verb_key>, <prefix_key>)}}

        # Define a graph
        G = nx.DiGraph()

        edges_have = []
        edges_comp = []
        edges_conn = []
        node_labels = {}
        edge_labels = {}
        color_map = []

        root_key = '0.0'

        # Add nodes with labels
        for key, value in invent_data['terms'].items():
            G.add_node(key)
            node_labels[key] = self.generateInventNodeLabel(invent_data['terms'], key)

            if key == root_key:
                color_map.append('red')
            elif root_key in invent_data['map'] and key in invent_data['map']['0.0']:
                color_map.append('yellow')
            else:
                color_map.append('lime')

        # Add edges
        for sbj_key, childs in invent_data['map'].items():
            for obj_key, verb in childs.items():
                verb_key = verb[0]

                #if verb_key == '0.0':
                #    continue

                couple = (sbj_key, obj_key)

                verb_text = invent_data['verbs'][verb_key]['text']
                verb_type = invent_data['verbs'][verb_key]['type']
                if verb_type == 'comp':
                    edges_comp.append(couple)
                elif verb_type == 'conn':
                    edges_conn.append(couple)
                elif verb_type == 'have':
                    edges_have.append(couple)

                G.add_edge(sbj_key, obj_key)
                edge_labels[couple] = verb_text #verb_type[0:3]

        # generate positions for the nodes
        pos = nx.spring_layout(G, weight=None, k=1.0, iterations=150)

        # create the dictionary with the formatted labels
        #edge_labels = {i[0:2]:'{}'.format(i[2]['label']) for i in G.edges(data=True)}

        # nodes
        nx.draw_networkx_nodes(G, pos, node_size=250, node_color = color_map, alpha=1.0)

        # compositional edges
        nx.draw_networkx_edges(G, pos, edgelist=edges_comp, width=1.5, alpha=0.9, edge_color='k', style='solid')
        # connection edges
        nx.draw_networkx_edges(G, pos, edgelist=edges_conn, width=1.0, alpha=0.9, edge_color='lime', style='dashed')
        # have edges
        nx.draw_networkx_edges(G, pos, edgelist=edges_have, width=1.5, alpha=0.9, edge_color='grey', style='dotted')

        # labels
        nx.draw_networkx_labels(G, pos, font_size=8, font_family='sans-serif')

        # draw the custom node labels
        shifted_pos = {k:[v[0],v[1]+.05] for k,v in pos.items()}
        node_label_handles = nx.draw_networkx_labels(G, pos=shifted_pos,labels=node_labels, font_size = 8, font_family='sans-serif')

        # add a white bounding box behind the node labels
        #[label.set_bbox(dict(facecolor='white', edgecolor='none')) for label in
        #        node_label_handles.values()]

        # add the custom egde labels
        nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels, font_size = 6, font_color = 'red')

        # Custom text
        x = 0
        y = -1.1
        plt.text(x,y, s=str(invent_data['terms']['0.0']), horizontalalignment='center')

        plt.axis('off')
        plt.show()

    def printSegmentGraph(self, segments):

        # Define a graph
        G = nx.DiGraph()

        edges = []
        node_labels = {0:'[ROOT]'}

        for segment in segments:
            n1 = int(segment['id'])
            n2 = int(segment['link']['parent'])

            """
            if segment['link']['child'] and segment['link']['point']:
                p1 = str(segment['link']['child'])
                p2 = str(segment['link']['point'])
                params = '{} ({}-{})'.format(segment['link']['type'], p1, p2)
            else:
                params = '{}'.format(segment['link']['type'])
            """

            params = '{}'.format(segment['link']['type'])

            edges.append((n1,n2,{'label':params}))

            # create some longer node labels
            node_labels[int(segment['id'])] = self.generateSegmNodeLabel(segment)

        G.add_edges_from(edges)

        # generate positions for the nodes
        pos = nx.spring_layout(G, weight=None, k=1.0, iterations=150)

        # create the dictionary with the formatted labels
        edge_labels = {i[0:2]:'{}'.format(i[2]['label']) for i in G.edges(data=True)}

        # draw the graph
        nx.draw_networkx(G, pos=pos, with_labels=False, edge_color='grey')

        # draw the custom node labels
        shifted_pos = {k:[v[0],v[1]+.05] for k,v in pos.items()}
        node_label_handles = nx.draw_networkx_labels(G, pos=shifted_pos,
                labels=node_labels, font_size = 10)

        # add a white bounding box behind the node labels
        #[label.set_bbox(dict(facecolor='white', edgecolor='none')) for label in
        #        node_label_handles.values()]

        # add the custom egde labels
        nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels, font_size = 6)

        plt.axis('off')
        plt.show()

    def generateSegmNodeLabel(self, segment, max_len = 100):
        text = ""
        """
        if 'morph' in segment:
            for token in segment['morph']:
                text += '{}({}) '.format(token['text'],token['id'])
        text = text.rstrip()
        if max_len:
            if len(text) > max_len:
                text = text[0:100] + '...'
        """

        result = '[{}:{}] {}'.format(segment['id'], segment['type'], text)

        return result

    def generateInventNodeLabel(self, terms, term_key, max_len = 20):
        text = terms[term_key]
        if max_len:
            if len(text) > max_len:
                text = text[0:max_len] + '...'
        result = '{}'.format(text)
        return result
