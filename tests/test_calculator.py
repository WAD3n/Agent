from tools.calculator import calculate


def test_basic_expression():
    assert calculate("2 + 2 * 3") == "8"


def test_parentheses_and_functions():
    assert calculate("sqrt(16)") == "4.0"


def test_division_by_zero():
    result = calculate("1 / 0")
    assert "Error" in result


def test_invalid_expression():
    result = calculate("2 + * 3")
    assert "Error" in result


def test_undefined_name():
    result = calculate("foo + 1")
    assert "Error" in result


def test_blocks_attribute_injection():
    result = calculate("().__class__.__bases__[0].__subclasses__()")
    assert "Error" in result


def test_blocks_import():
    result = calculate("__import__('os').system('echo hacked')")
    assert "Error" in result
