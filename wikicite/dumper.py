from typing import *
import os
import math
from collections import defaultdict
try:
    import ujson as json
except ImportError:
    import json


class Dumper:
    def __init__(self, lines_per_file: int, dump_path: str, total: int):
        self.lines_per_file, self.dump_path, self.total = lines_per_file, dump_path, total
        self.total_files = math.ceil(total / lines_per_file)
        self.last_file_lines = total % lines_per_file
        self.processed = set()
        self.cached = defaultdict(dict)

    def check_processed(self):
        if not os.path.exists(self.dump_path):
            return
        for fn in os.listdir(self.dump_path):
            if fn.endswith('jsonl'):
                name = fn.split('.')[0]
                self.processed.add(int(name))
        return len(self.processed) * self.lines_per_file

    def get_todos(self) -> List[int]:
        ret = list()
        for i in range(self.total):
            if i // self.lines_per_file not in self.processed:
                ret.append(i)
        return ret

    def put(self, idx: int, items: list):
        file_idx = idx // self.lines_per_file
        list_idx = idx % self.lines_per_file
        self.cached[file_idx][list_idx] = [json.dumps(item) for item in items]

        if self.need_dump(file_idx):
            os.makedirs(self.dump_path, exist_ok=True)
            dikt = self.cached.pop(file_idx)
            lines = []
            for k in sorted(list(dikt.keys())):
                lines.extend(dikt[k])
            with open(os.path.join(self.dump_path, f'{file_idx:04}.jsonl'), 'w') as fp:
                fp.write('\n'.join(lines))

    def need_dump(self, file_idx: int) -> bool:
        if file_idx == self.total_files - 1:
            return len(self.cached[file_idx]) >= self.last_file_lines
        else:
            return len(self.cached[file_idx]) >= self.lines_per_file

    @property
    def empty(self) -> bool:
        return len(self.cached) == 0
