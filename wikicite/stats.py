from typing import Dict, List
import math

import numpy as np
from tabulate import tabulate


def significant_figures(x, digits=3):
    if x == 0 or not math.isfinite(x):
        return x
    if math.log10(x) >= digits:
        return x
    digits -= math.ceil(math.log10(abs(x)))
    return round(x, digits)


def describe_data(count: Dict[str, List[int | float]]):
    quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]

    def one_list(li):
        nums = [significant_figures(float(np.mean(li)), 3)]
        for q in quantiles:
            nums.append(significant_figures(float(np.quantile(li, q)), 3))
        return nums

    headers = ['name', 'mean'] + [f'{q=}' for q in quantiles]
    lines = [[k] + one_list(v) for k, v in count.items()]

    def md_line(li):
        return '|'.join([''] + list(map(str, li)) + [''])

    md = '\n'.join([md_line(headers), md_line(['-:' for _ in headers])] + [md_line(ln) for ln in lines])
    return tabulate(lines, headers=headers), md, (headers, lines)
