import pytest

from parser_2gis.common import wait_until_finished


def test_wait_timeout_has_readable_message():
    @wait_until_finished(timeout=0, poll_interval=0)
    def never_finishes():
        return False

    with pytest.raises(TimeoutError, match=r'never_finishes.*0 с'):
        never_finishes()
