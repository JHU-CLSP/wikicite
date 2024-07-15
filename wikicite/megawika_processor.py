import traceback
from typing import List
try:
    import usjon as json
except ImportError:
    import json
from collections import defaultdict

from tqdm import tqdm

from .data_reader.jsonl_reader import JsonlCorpus
from .citation_utils import process_one_citation, Citation


class MegaWika2Processor:
    corpus_path: str

    def __init__(self, corpus_path: str, citation_keep_criterion: str):
        """
        :param corpus_path: path to the megawika v2 data "/path/to/megawika/v2.0/en/data"
        :param citation_keep_criterion: The criterion to keep citations
        `long`: Items with long citations
        `short`: Items with short citations
        `both`: Items with both long and short citations
        `all`: All items
        """
        self.corpus_path, self.citation_keep_criterion = corpus_path, citation_keep_criterion
        self.corpus = JsonlCorpus(self.corpus_path)

    def valid_citation(self, cite: Citation) -> bool:
        if self.citation_keep_criterion == 'all':
            return True
        cite_bits = (cite.long is not None) * 2 + (cite.short is not None) * 1
        keep_bits = {'long': 2, 'short': 1, 'both': 3}[self.citation_keep_criterion]
        return bool(keep_bits & cite_bits)

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
                    valid_citations = self.process_citations(citations)
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

    def process_citations(self, citations: List[dict]) -> List[Citation]:
        # one citation could appear multiple times if it contains multiple urls
        # therefore we group them, using the content as the key
        groups = defaultdict(list)
        for cite_dict in citations:
            cite = process_one_citation(cite_dict)
            if cite is None or not self.valid_citation(cite):
                continue
            groups[cite.key].append(cite)

        ret = []
        for li in groups.values():
            # in each group, keep the one with the longest long citation
            li.sort(key=lambda c: len(str(c.long)))
            ret.append(li[-1])
        return ret
