"""Utils test."""

import os
from pathlib import Path

import pytest

from appbundler.utils import check_path, cd


def test_check_path():
    good_path = '.'
    bad_path = './placeholder'

    check_path(good_path)
    check_path(Path(good_path))

    with pytest.raises(ValueError):
        check_path(bad_path)


def test_cd():
    origin = Path(os.getcwd())
    with cd('..'):
        assert os.getcwd() == str(origin.parent)
    assert os.getcwd() == str(origin)
