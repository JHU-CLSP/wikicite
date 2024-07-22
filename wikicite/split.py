from typing import *
from collections import defaultdict

from spacy.lang.en import English
from spacy.tokens.span import Span


class DocumentSplit:
    def __init__(self):
        self.nlp = English()
        config = {"punct_chars": None}
        self.nlp.add_pipe("sentencizer", config=config)
        self.nlp.initialize()
        self.stats = defaultdict(list)

    def process_doc(self, text: str) -> List[str]:
        text = text[:self.truncate_length]
        doc = self.nlp(text)
        sentences: List[Span] = list(doc.sents)
        batches = []
        cur_batch = []
        for sent in sentences:
            cur_batch.append(sent)
            if sum(map(len, cur_batch)) >= self.segment_words:
                batches.append(cur_batch)
                cur_batch = []
        if cur_batch:
            batches.append(cur_batch)
        ret = []
        for batch in batches:
            n_word = [len(sent) for sent in batch]
            self.stats['word/sentence'].extend(n_word)
            self.stats['word/segment'].append(sum(n_word))
            self.stats['sentence/segment'].append(len(batch))
            ret.append(''.join([sent.text_with_ws for sent in batch]).strip())
        return ret
