import importlib

app = importlib.import_module("src.interfaces.app")

_fmt_cost = app._fmt_cost

def test_fmt_cost_numeric():
    assert _fmt_cost(0) == "$0.00"
    assert _fmt_cost(12.3456) == "$12.35"
    assert _fmt_cost(99.999) == "$100.00"

def test_fmt_cost_none():
    assert _fmt_cost(None) == "N/A"


def test_fmt_cost_invalid():
    class Foo:
        pass

    assert _fmt_cost(Foo()) == "N/A" 