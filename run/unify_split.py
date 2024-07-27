from argparse import ArgumentParser

from wikicite.unify import unify_and_split


def main():
    parser = ArgumentParser()
    parser.add_argument('--src', type=str)
    parser.add_argument('--tgt', type=str)
    args = parser.parse_args()
    unify_and_split(args.src, args.tgt)


if __name__ == '__main__':
    main()
