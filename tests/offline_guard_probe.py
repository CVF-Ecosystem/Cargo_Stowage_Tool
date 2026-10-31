"""Verify the test-only offline guard blocks an external destination."""
import socket
try:
    socket.create_connection(('example.com', 80), 1)
except OSError as exc:
    assert 'offline test guard blocked' in str(exc)
    print('EXPECTED BLOCK:', exc)
else:
    raise AssertionError('external network was not blocked')
