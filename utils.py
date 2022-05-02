import collections


class Result(collections.namedtuple("Result", ("is_ok", "reason"))):
    def __bool__(self):
        return self.is_ok


def NotOk(reason):
    return Result(is_ok=False, reason=reason)


def Ok():
    return Result(is_ok=True, reason="")
