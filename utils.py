from __future__ import division
from math import ceil, floor, isnan
from typing import List
import requests
from secret import (
    TELE_BOT_TOKEN,
    TELE_BOT_CHAT_ID,
)


def telegram_bot_sendtext(bot_message):
    url = (
        "https://api.telegram.org/bot"
        + TELE_BOT_TOKEN
        + "/sendMessage?chat_id="
        + TELE_BOT_CHAT_ID
        + "&parse_mode=Markdown&text="
        + bot_message
    )
    response = requests.get(url)
    return response.json()


__all__ = ["plot"]


def _isnum(n):
    return not isnan(n)


def plot(series, cfg=None):
    if len(series) == 0:
        return ""

    if not isinstance(series[0], list):
        if all(isnan(n) for n in series):
            return ""
        else:
            series = [series]

    cfg = cfg or {}

    minimum = cfg.get("min", min(filter(_isnum, [j for i in series for j in i])))
    maximum = cfg.get("max", max(filter(_isnum, [j for i in series for j in i])))

    default_symbols = ["┼", "┤", "╶", "╴", "─", "╰", "╭", "╮", "╯", "│"]
    symbols = cfg.get("symbols", default_symbols)

    if minimum > maximum:
        raise ValueError("The min value cannot exceed the max value.")

    interval = maximum - minimum
    offset = cfg.get("offset", 3)
    height = cfg.get("height", interval)
    ratio = height / interval if interval > 0 else 1

    min2 = int(floor(minimum * ratio))
    max2 = int(ceil(maximum * ratio))

    def clamp(n):
        return min(max(n, minimum), maximum)

    def scaled(y):
        return int(round(clamp(y) * ratio) - min2)

    rows = max2 - min2

    width = 0
    for i in range(0, len(series)):
        width = max(width, len(series[i]))
    width += offset

    placeholder = cfg.get("format", "{:8.2f} ")

    result = [[" "] * width for i in range(rows + 1)]

    # axis and labels
    for y in range(min2, max2 + 1):
        label = placeholder.format(
            maximum - ((y - min2) * interval / (rows if rows else 1))
        )
        result[y - min2][max(offset - len(label), 0)] = label
        result[y - min2][offset - 1] = (
            symbols[0] if y == 0 else symbols[1]
        )  # zero tick mark

    # first value is a tick mark across the y-axis
    d0 = series[0][0]
    if _isnum(d0):
        result[rows - scaled(d0)][offset - 1] = symbols[0]

    for i in range(0, len(series)):
        # plot the line
        for x in range(0, len(series[i]) - 1):
            d0 = series[i][x + 0]
            d1 = series[i][x + 1]

            if isnan(d0) and isnan(d1):
                continue

            if isnan(d0) and _isnum(d1):
                result[rows - scaled(d1)][x + offset] = symbols[2]
                continue

            if _isnum(d0) and isnan(d1):
                result[rows - scaled(d0)][x + offset] = symbols[3]
                continue

            y0 = scaled(d0)
            y1 = scaled(d1)
            if y0 == y1:
                result[rows - y0][x + offset] = symbols[4]
                continue

            result[rows - y1][x + offset] = symbols[5] if y0 > y1 else symbols[6]
            result[rows - y0][x + offset] = symbols[7] if y0 > y1 else symbols[8]

            start = min(y0, y1) + 1
            end = max(y0, y1)
            for y in range(start, end):
                result[rows - y][x + offset] = symbols[9]

    return "\n".join(["".join(row).rstrip() for row in result])


MAX_HEIGHT = 12


def gen_ascii_plot(points: List[float], height=MAX_HEIGHT) -> str:
    output = plot(
        series=points,
        cfg={
            "height": height,
            "offset": 1,
        },
    )
    x_axis = ""
    interval = 6
    n = len(points)
    for i in range(1, n // interval + 1):
        x_axis += "{: >{}}".format(str(i * interval)[::-1], interval)
    output += "\n" + "{: >{}}".format(x_axis[::-1], n)
    min_value = min(points)
    max_value = max(points)
    percentage_diff = (max_value - min_value) / min_value * 100
    output += f"\n${min_value:,.2f} - ${max_value:,.2f} ({percentage_diff:.2f}%)"
    return output
