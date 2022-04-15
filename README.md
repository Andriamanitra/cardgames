[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Andriamanitra/cardgames/main.svg)](https://results.pre-commit.ci/latest/github/Andriamanitra/cardgames/main)
![tests](https://github.com/andriamanitra/cardgames/actions/workflows/pytest.yml/badge.svg)

# Card games in Python

Goal of this repo is to implement various card games from scratch in Python.
For now the games are played through CLI, but eventually I would like to implement
a web interface to make them playable online (multiplayer with websockets). It would
be nice to have a trackerless and ad-free place to play some card games. A simple
desktop interface with tkinter is also something I might do at some point, because I
really enjoy working with tkinter.

The game implementations might be a bit scuffed but I would like to make the common deck part
as nice and reusable as possible, so feedback (or even contributions) would be very welcome!


## Planned games to implement:

* [Hearts](https://en.wikipedia.org/wiki/Hearts_(card_game)) (status: semi-functional in CLI)
* [Cassino](https://en.wikipedia.org/wiki/Cassino_(card_game)) (status: not started yet)
* Others?


## How to use

```python3.10 hearts.py```

The games themselves have no dependencies but for running the unit tests you must install pytest.
