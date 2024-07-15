from typing import Dict, List

import numpy as np
from tabulate import tabulate


def describe_data(count: Dict[str, List[int | float]]):
    quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]

    def one_list(li):
        nums = [round(np.mean(li), 1)]
        for q in quantiles:
            nums.append(round(np.quantile(li, q)))
        return nums

    headers = ['name', 'mean'] + [f'{q=}' for q in quantiles]
    lines = [[k] + one_list(v) for k, v in count.items()]

    def md_line(li):
        return '|'.join([''] + list(map(str, li)) + [''])

    md = '\n'.join([md_line(headers), md_line(['-:' for _ in headers])] + [md_line(ln) for ln in lines])
    return tabulate(lines, headers=headers), md, (headers, lines)
