from argparse import ArgumentParser
from collections import defaultdict
import random

from tqdm import tqdm

from wikicite.megawika_processor import MegaWika2Processor
from wikicite.stats import describe_data


def main():
    parser = ArgumentParser()
    parser.add_argument('--corpus', type=str)
    parser.add_argument('--sample', type=int, default=10_000, help='#samples/1000')
    args = parser.parse_args()

    mw = MegaWika2Processor(args.corpus, citation_keep_criterion='all')
    thousands = list(range(len(mw.corpus)//1000))
    random.shuffle(thousands)
    thousands = thousands[:args.sample]

    todos = []
    for thousand in thousands:
        for i in range(1000):
            article_idx = thousand*1000 + i
            if article_idx < len(mw.corpus):
                todos.append(article_idx)

    stats = defaultdict(list)
    for article_idx in tqdm(todos):
        article = mw.process_article(article_idx)
        n_total = n_long = n_short = n_both = 0
        for para in article:
            for cite in para['citations']:
                n_total += 1
                n_long += cite['long'] is not None
                n_short += cite['short'] is not None
                n_both += cite['long'] is not None and cite['short'] is not None
        stats['total cites'].append(n_total)
        stats['long cites'].append(n_long)
        stats['short cites'].append(n_short)
        stats['both_cites'].append(n_both)
    tabs = describe_data(stats)
    print(tabs[0])
    print('-----')
    print(tabs[1])


if __name__ == '__main__':
    main()
