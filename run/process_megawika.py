from argparse import ArgumentParser

from wikicite.megawika_processor import MegaWika2Processor


def main():
    parser = ArgumentParser()
    parser.add_argument('--corpus')
    args = parser.parse_args()

    processor = MegaWika2Processor(args.corpus)
    list(processor.iterate_over_articles())


if __name__ == '__main__':
    main()
