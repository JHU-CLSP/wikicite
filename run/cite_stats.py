from argparse import ArgumentParser
from collections import defaultdict

from tqdm import trange

from wikicite.megawika_processor import MegaWika2Processor
from wikicite.stats import describe_data


def main():
    parser = ArgumentParser()
    parser.add_argument('--corpus', type=str)
    parser.add_argument('--sample', type=int, default=10_000, help='#samples')
    args = parser.parse_args()

    mw = MegaWika2Processor(args.corpus, citation_keep_criterion='all')
    stats = defaultdict(list)
    n_article = min(len(mw.corpus), args.sample)
    for article_idx in trange(n_article):
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
