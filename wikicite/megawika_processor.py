from typing import List, Any, Dict, Iterable, Tuple, Set
try:
    import usjon as json
except ImportError:
    import json
from collections import defaultdict

from spacy.lang.en import English

from .data_reader.jsonl_reader import JsonlCorpus
from .citation_utils import process_one_citation, Citation


class MegaWika2Processor:
    corpus_path: str
    sent_end_len: int = 7

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

        self.nlp_pipeline = English()
        config = {"punct_chars": None}
        self.nlp_pipeline.add_pipe(factory_name="sentencizer", config=config)

    def valid_citation(self, cite: Citation | None) -> bool:
        if cite is None:
            return False
        if self.citation_keep_criterion == 'all':
            return True
        if self.citation_keep_criterion == 'long':
            return cite.long is not None
        elif self.citation_keep_criterion == 'short':
            return cite.short is not None
        elif self.citation_keep_criterion == 'both':
            return cite.long is not None and cite.short is not None
        raise NotImplementedError

    def preprocess_paragraph(self, elements) -> List[Dict[str, Any]]:
        # filter unused citations
        filtered = []
        for ele in elements:
            if ele['type'] == 'citation':
                processed = process_one_citation(ele)
                if self.valid_citation(processed):
                    filtered.append({'type': 'citation', 'processed': processed})
            elif ele['type'] == 'text':
                filtered.append(ele)

        # group adjacent texts and citations
        i = 0
        grouped = []
        while i < len(filtered):
            j = i+1
            typ = filtered[i]['type']
            for k in range(i+1, len(filtered)):
                if filtered[k]['type'] == typ:
                    j = k+1
                else:
                    break

            if typ == 'text':
                content = ' '.join([ele['content'] for ele in filtered[i:j]])
                while '  ' in content:
                    content = content.replace('  ', ' ')
                grouped.append({'type': 'text', 'content': content + ' '})
            else:
                grouped.append({
                    'type': 'citation',
                    'citations': [filtered[k]['processed'] for k in range(i, j)]
                })
            i = j

        return grouped

    def gen_examples_from_paragraph(self, paragraph: List) -> Iterable[Dict[str, Any]]:
        text = ''.join([ele['content'] for ele in paragraph if ele['type'] == 'text'])
        doc = list(self.nlp_pipeline(text).sents)
        sent_ends = set()
        for sent in doc:
            sent_ends.add(sent.text.strip()[-self.sent_end_len:])
        previous_text = ''
        cached_citations = []
        for ele in paragraph:
            if ele['type'] == 'text':
                previous_text += ele['content']
            else:
                assert ele['type'] == 'citation'
                if not previous_text:
                    cached_citations.extend(ele['citations'])
                    continue
                cur_end = previous_text.strip()[-self.sent_end_len:]
                if cur_end not in sent_ends:
                    # not the end of a sentence
                    cached_citations.extend(ele['citations'])
                    continue
                citations = cached_citations + ele['citations']
                cached_citations = []
                # moving pointer left, until a sentence end is found
                ptr = len(previous_text) - int(self.sent_end_len * 0.5)
                while ptr >= 0 and previous_text[ptr-self.sent_end_len:ptr] not in sent_ends:
                    ptr -= 1
                sentence_start = ptr + 1 if ptr > 0 else 0
                yield {
                    'target_sentence': previous_text[sentence_start:].strip(),
                    'previous_text': previous_text[:sentence_start].strip(),
                    'citations': self.dedup_citations(citations),
                }

    def process_article(self, article_idx: int):
        dikt = self.corpus[article_idx]
        title = dikt['title']
        for ignore_type in ['File', 'Template', "Wikipedia", 'Portal']:
            # ignore some page types
            if title.startswith(f'{ignore_type}:'):
                return []
        prefix = ''
        ret = []
        for ele in dikt['elements']:
            if ele['type'] == 'heading':
                prefix += ele['content']+'\n'
            elif ele['type'] == 'paragraph':
                preprocessed_paragraph = self.preprocess_paragraph(ele['elements'])
                paragraph_text = ''.join([ele['content'] for ele in preprocessed_paragraph if ele['type'] == 'text'])
                if paragraph_text == '':
                    continue
                for item in self.gen_examples_from_paragraph(preprocessed_paragraph):
                    item['previous_text'] = prefix + ' ' + item['previous_text']
                    item['article_title'] = title
                    item['article_index'] = article_idx
                    item['last_revision'] = dikt['last_revision']
                    ret.append(item)
                prefix += paragraph_text+'\n'
        return ret

    def dedup_citations(self, citations: List[Citation]) -> List[Dict[str, str]]:
        # one citation could appear multiple times if it contains multiple urls
        # therefore we group them, using the content as the key
        groups = defaultdict(list)
        for cite in citations:
            groups[cite.key].append(cite)

        dedup = []
        for li in groups.values():
            # in each group, keep the one with the longest long citation
            li.sort(key=lambda c: len(str(c.long)))
            dedup.append(li[-1])

        # convert it back to dict items
        ret = []
        for item in dedup:
            if self.citation_keep_criterion == 'long':
                ret.append({'type': 'long', 'content': item.long})
            elif self.citation_keep_criterion == 'short':
                ret.append({'type': 'short', 'content': item.short})
            else:
                ret.append({'type': 'citations', 'short': item.short, 'long': item.long})
        return ret
