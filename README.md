# The World Dispatch

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/konnitiwawa3/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/konnitiwawa3/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

Monday, 23 November 2026. A world-news front page with 37 reports from seven regions, a numbered story map, a UTC chronology, and a market strip. The lead illustration focuses on Benghazi harbor. Astryx Stone Light informs the editorial palette.

Run the renderer with Python 3.13.

```sh
MAKEFUN_OUTPUT_DIR=./preview python3.13 -P -s main.py
```

It writes a 1024 × 1024 RGB PNG named `entry.png` under `MAKEFUN_OUTPUT_DIR` (default `/output`). It uses the Python standard library and bundled assets and runs offline. The source links and chronology are in `edition.json`. Newsreader and Source Sans 3 are used under the font licenses in `fonts/`.
