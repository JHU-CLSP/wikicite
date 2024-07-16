from argparse import ArgumentParser

from tqdm import tqdm

from wikicite.megawika_processor import MegaWika2Processor
from wikicite.dumper import Dumper


def main():
    parser = ArgumentParser()
    parser.add_argument('--corpus', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--cite', type=str, choices=['long', 'short', 'all', 'both'])
    args = parser.parse_args()

    processor = MegaWika2Processor(corpus_path=args.corpus, citation_keep_criterion=args.cite)
    dumper = Dumper(lines_per_file=1000, dump_path=args.output, total=len(processor.corpus))
    n_processed = dumper.check_processed()
    print(f'Found {n_processed} already processed items. Skipping them.')
    todos = dumper.get_todos()

    for article_idx in tqdm(todos):
        dumper.put(idx=article_idx, items=processor.process_article(article_idx))

    if dumper.empty:
        print('All done.')
    else:
        print('Warning: There might be files that are not dumped yet.')


if __name__ == '__main__':
    main()
