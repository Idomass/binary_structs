from buffer import Buffer, MaxSizeExceededError


def test_valid_init():
    a = Buffer(int, 50, [1, 2, 3])

    assert a == [1, 2, 3]

def test_invalid_init_type():
    try:
        Buffer(int, 5, ['Noder'])
        assert False

    except TypeError:
        pass

def test_invalid_init_size():
    try:
        Buffer(int, 3, range(4))
        assert False

    except MaxSizeExceededError:
        pass

def test_valid_append_size():
    a = Buffer(int, 5)

    a.append(17)
    a.append(18)

    assert a == [17, 18]

def test_invalid_append_size():
    a = Buffer(int, 0)

    try:
        a.append(5)
        assert False

    except MaxSizeExceededError:
        pass

def test_valid_extend_size():
    a = Buffer(int, 9)

    a.extend(range(9))

    assert a == list(range(9))

def test_invalid_extend_size():
    a = Buffer(str, 2)

    try:
        a.extend(['Noder', 'Neder', 'Nadir'])
        assert False

    except MaxSizeExceededError:
        pass

def test_invalid_append_type():
    a = Buffer(int, 5)

    try:
        a.append('Noder')
        assert False

    except TypeError:
        pass

def test_invalid_extend_type():
    a = Buffer(str, 3)

    try:
        a.extend(['Nice', 'But', 5])
        assert False

    except TypeError:
        pass

def test_valid_insert():
    a = Buffer(int, 7, range(6))

    a.insert(0, 8)

    assert a == [8] + list(range(6))

def test_invalid_insert_size():
    a = Buffer(str, 2, ['Hi', 'There'])

    try:
        a.insert(1, 'Bruh')
        assert False

    except MaxSizeExceededError:
        pass

def test_invalid_insert_type():
    a = Buffer(int, 10, range(5))

    try:
        a.insert(1, 'Ahi')
        assert False

    except TypeError:
        pass

def test_valid_iadd():
    a = Buffer(int, 10, range(5))

    a += [5, 6, 7]

    assert a == list(range(8))

def test_invalid_iadd_size():
    a = Buffer(int, 3, range(2))

    try:
        a += [1, 2]
        assert False

    except MaxSizeExceededError:
        pass

def test_invalid_iadd_type():
    a = Buffer(str, 4, ['a', 'b', 'c'])

    try:
        a += [4]
        assert False

    except TypeError:
        pass

def test_valid_imul():
    a = Buffer(int, 10, [1, 2])

    a *= 3

    assert a == [1, 2] * 3

def test_invalid_imul_size():
    a = Buffer(int, 4, [1, 2])

    try:
        a *= 3
        assert False

    except MaxSizeExceededError:
        pass
