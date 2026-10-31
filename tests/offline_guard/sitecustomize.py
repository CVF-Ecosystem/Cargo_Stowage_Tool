"""Test-only process guard: prohibit Python server outbound non-loopback connections."""
import ipaddress
import socket
import sys

_original_getaddrinfo = socket.getaddrinfo
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex


def _allowed(host):
    if host is None or host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _getaddrinfo(host, *args, **kwargs):
    if not _allowed(host):
        raise OSError('offline test guard blocked DNS: ' + str(host))
    return _original_getaddrinfo(host, *args, **kwargs)


def _connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and not _allowed(address[0]):
        raise OSError('offline test guard blocked outbound: ' + str(address))
    return _original_connect(self, address)


def _connect_ex(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and not _allowed(address[0]):
        raise OSError('offline test guard blocked outbound: ' + str(address))
    return _original_connect_ex(self, address)


socket.getaddrinfo = _getaddrinfo
socket.socket.connect = _connect
socket.socket.connect_ex = _connect_ex
print('SCST_OFFLINE_GUARD_ACTIVE: Python non-loopback outbound blocked', file=sys.stderr, flush=True)
