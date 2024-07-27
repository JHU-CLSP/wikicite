from typing import *
from copy import deepcopy
import os
import random
import secrets

from tqdm import tqdm, trange
import numpy as np
from datetime import datetime
try:
    import ujson as json
except ImportError:
    import json

from .data_reader.jsonl_reader import JsonlCorpus


def unify_and_split(src: str, tgt: str):
    data = JsonlCorpus(src)
    # keep in memory
    revisions = []
    items = []
    for i in trange(len(data), desc='reading'):
        item = data[i]
        revisions.append(datetime.fromisoformat(item['last_revision']))
        items.append(item)

    # analyze revision timestamps
    revisions = np.array(revisions)
    dev_split = np.quantile(revisions, 0.96)
    test_split = np.quantile(revisions, 0.98)

    splits = ['train', 'dev', 'test']
    data = {split: [] for split in splits}
    for item in items:
        dt = datetime.fromisoformat(item['last_revision'])
        if dt < dev_split:
            data['train'].append(item)
        elif dt < test_split:
            data['dev'].append(item)
        else:
            data['test'].append(item)
    random.seed(299792458)
    os.makedirs(tgt, exist_ok=True)
    for split in splits:
        random.shuffle(data[split])
        tgt_path = os.path.join(tgt, f'{split}.jsonl')
        with open(tgt_path, 'w') as f:
            total = len(data[split])
            for i in trange(total, desc=f'writing {split}'):
                item = deepcopy(data[split][i])
                item['id'] = secrets.token_hex(16)
                f.write(json.dumps(data[split][i]))
                if i != total - 1:
                    f.write('\n')
