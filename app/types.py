# Хотел реализовать но передумал

from enum import Enum, IntEnum


class ProxyVersion(IntEnum):
    IPv6 = 6
    IPv4 = 4
    IPv4_Shared = 3

class ProxyType(Enum):
    HTTPS = 'https'
    SOCKS5 = 'socks5'