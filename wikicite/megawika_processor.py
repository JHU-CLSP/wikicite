import os
from typing import *
from collections import defaultdict
import traceback
try:
    import usjon as json
except ImportError:
    import json

from tqdm import tqdm, trange
from datetime import datetime
import numpy as np

from .data_reader.jsonl_reader import JsonlCorpus
from .citation_utils import process_citations


class MegaWika2Processor:
    corpus_path: str

    def __init__(self, corpus_path: str):
        """
        :param corpus_path: path to the megawika v2 data "/path/to/megawika/v2.0/en/data"
        """
        self.corpus_path = corpus_path
        self.corpus = JsonlCorpus(self.corpus_path)

    def process_article(self, article_idx: int):
        article = self.corpus[article_idx]
        ret, previous_texts = list(), list()
        for element_idx, paragraph in enumerate(article['elements']):
            if paragraph['type'] == 'heading':
                previous_texts.append(paragraph['content'])
                previous_texts.append('\n')
                continue
            if paragraph['type'] != 'paragraph':
                continue

            citations = []
            for item_idx, item in enumerate(paragraph['elements']):
                if item['type'] == 'citation':
                    item['article_idx'], item['element_idx'] = article_idx, element_idx
                    citations.append(item)
                elif item['type'] == 'text':
                    valid_citations = process_citations(citations)
                    if valid_citations:
                        # if citations exist, an example will be generated
                        ret.append({
                            'previous_text': ' '.join(previous_texts),
                            'citations': [cite.to_dict() for cite in valid_citations],
                            'target_sentence': item['content'],
                            'article_idx': article_idx,
                            'element_idx': element_idx,
                        })
                    previous_texts.append(item['content'])
                    citations = []
            previous_texts.append('\n')
        return ret

    def iterate_over_articles(self):
        # collect idx
        todos = list(range(len(self.corpus)))
        for article_idx in tqdm(todos, desc='Processing articles', leave=True):
            try:
                yield self.process_article(article_idx)
            except Exception as e:
                print(f'Error when processing corpus {article_idx}: {e}')
                print(traceback.format_exc())
