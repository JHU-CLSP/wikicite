from argparse import ArgumentParser
import traceback

from tqdm import trange

from wikicite.megawika_processor import MegaWika2Processor
from wikicite.dumper import Dumper


def main():
    parser = ArgumentParser()
    parser.add_argument('--corpus', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--cite', type=str, choices=['long', 'short', 'all', 'both'])
    args = parser.parse_args()

    processor = MegaWika2Processor(corpus_path=args.corpus, citation_keep_criterion=args.cite)
    dumper = Dumper(lines_per_file=1000, dump_path=args.output)

    for article_idx in trange(len(processor.corpus)):
        try:
            a_list = processor.process_article(article_idx)
        except Exception as e:
            print(traceback.format_exc())
            print('Error:', e)
            a_list = []
        dumper.put(a_list)

    dumper.dump(True)

    print('All done.')


if __name__ == '__main__':
    main()
