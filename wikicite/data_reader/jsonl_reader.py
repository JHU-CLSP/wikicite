from typing import Dict, Any
try:
    import ujson as json
except ImportError:
    import json
import os

from torch.utils import data
from functools import lru_cache


class JsonlCorpus(data.Dataset):
    """
    This reader reads a list of jsonl files. Suppose a folder contains multiple jsonl files:
    - 000001.jsonl contains the 1st 1000 data examples
    - 000002.jsonl contains the 2nd 1000 data examples
    - ...
    - 000312.jsonl contains the 312-th 1000 data examples
    - 000313.jsonl contains the last 99 data examples.
    Then we have 312 x 1000 + 99 = 312099 examples. This dataset reader parses this format of data
    by iterating over these files.
    """
    def __init__(self, path: str):
        self.path = path

        self.jsonl_files = list()
        for fn in os.listdir(path):
            if fn.endswith('.jsonl'):
                self.jsonl_files.append(fn)
        self.jsonl_files.sort()
        assert len(self.jsonl_files) > 0, "no file is found under " + self.path
        with open(os.path.join(self.path, self.jsonl_files[0])) as fp:
            self.lines_per_file = len(fp.readlines())
        with open(os.path.join(self.path, self.jsonl_files[-1])) as fp:
            self.lines_last_file = len(fp.readlines())

    def __len__(self):
        return self.lines_per_file * (len(self.jsonl_files) - 1) + self.lines_last_file

    @lru_cache(maxsize=3)
    def get_file(self, idx: int):
        # the content of the most recent opened files is cached
        with open(os.path.join(self.path, self.jsonl_files[idx])) as fp:
            return fp.readlines()

    def __getitem__(self, idx) -> Dict[str, Any]:
        file_idx, item_idx = idx // self.lines_per_file, idx % self.lines_per_file
        assert file_idx < len(self.jsonl_files), "index out of range"
        file_lines = self.get_file(file_idx)
        assert len(file_lines) > item_idx, "index out of range"
        line = file_lines[item_idx]
        return json.loads(line.strip())
