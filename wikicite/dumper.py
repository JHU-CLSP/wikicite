import os
try:
    import ujson as json
except ImportError:
    import json


class Dumper:
    def __init__(self, lines_per_file: int, dump_path: str):
        self.lines_per_file, self.dump_path = lines_per_file, dump_path
        if os.path.exists(dump_path):
            raise ValueError('Dump path exists.')
        self.file_count = 0
        self.cached = list()

    def put(self, items: list):
        self.cached.extend(items)
        self.dump(False)

    def dump(self, force: bool):
        while len(self.cached) >= (self.lines_per_file if not force else 1):
            os.makedirs(self.dump_path, exist_ok=True)
            to_dump = list(map(json.dumps, self.cached[:self.lines_per_file]))
            self.cached = self.cached[self.lines_per_file:]
            with open(os.path.join(self.dump_path, f'{self.file_count:06}.jsonl'), 'w') as fp:
                fp.write('\n'.join(to_dump))
            self.file_count += 1
