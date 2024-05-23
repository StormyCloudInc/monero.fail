import sys
import socket
import pickle
from os import path

import geoip2.database
from requests import get as r_get
from urllib.parse import urlparse
from levin.bucket import Bucket
from levin.ctypes import *
from levin.constants import LEVIN_SIGNATURE

from xmrnodes.models import Node
from xmrnodes import config


def make_request(url: str, path="/get_info", data=None):
    headers = {"Origin": "https://monero.fail"}
    if is_onion(url):
        _p = f"socks5h://{config.TOR_HOST}:{config.TOR_PORT}"
        proxies = {"http": _p, "https": _p}
        timeout = 30
    elif is_i2p(url):
        _p = f"http://{config.I2P_HOST}:{config.I2P_PORT}"
        proxies = {"http": _p, "https": _p}
        timeout = 30
    else:
        proxies = None
        timeout = 10
    r = r_get(
        url + path,
        timeout=timeout,
        proxies=proxies,
        json=data,
        headers=headers,
        verify=False,
    )
    r.raise_for_status()
    return r


def determine_crypto(url):
    data = {"method": "get_block_header_by_height", "params": {"height": 0}}
    hashes = {
        "monero": [
            "418015bb9ae982a1975da7d79277c2705727a56894ba0fb246adaabb1f4632e3",  # mainnet
            "48ca7cd3c8de5b6a4d53d2861fbdaedca141553559f9be9520068053cda8430b",  # testnet
            "76ee3cc98646292206cd3e86f74d88b4dcc1d937088645e9b0cbca84b7ce74eb",  # stagenet
        ],
        "wownero": [
            "a3fd635dd5cb55700317783469ba749b5259f0eeac2420ab2c27eb3ff5ffdc5c",  # mainnet
            "d81a24c7aad4628e5c9129f8f2ec85888885b28cf468597a9762c3945e9f29aa",  # testnet
        ],
    }
    try:
        r = make_request(url, "/json_rpc", data)
        assert "result" in r.json()
        hash = r.json()["result"]["block_header"]["hash"]
        crypto = "unknown"
        for c, h in hashes.items():
            if hash in h:
                crypto = c
                break
        return crypto
    except:
        return "unknown"

def is_i2p(url: str):
    _split = url.split(":")
    if len(_split) < 2:
        return False
    if _split[1].endswith(".i2p"):
        return True
    else:
        return False

def is_onion(url: str):
    _split = url.split(":")
    if len(_split) < 2:
        return False
    if _split[1].endswith(".onion"):
        return True
    else:
        return False

def retrieve_peers(host, port):
    try:
        sock = socket.socket()
        sock.settimeout(5)
        sock.connect((host, int(port)))
    except Exception as e:
        return None

    bucket = Bucket.create_handshake_request()

    sock.send(bucket.header())
    sock.send(bucket.payload())

    buckets = []
    peers = []

    while 1:
        buffer = sock.recv(8)
        if not buffer:
            break

        if not buffer.startswith(bytes(LEVIN_SIGNATURE)):
            break

        bucket = Bucket.from_buffer(signature=buffer, sock=sock)
        buckets.append(bucket)

        if bucket.command == 1001:
            _peers = bucket.get_peers() or []

            for peer in _peers:
                try:
                    peers.append("http://%s:%d" % (peer["ip"].ip, peer["port"].value))
                except:
                    pass

            sock.close()
            break

    if peers:
        return peers
    else:
        return None


def get_highest_block(nettype, crypto):
    highest = (
        Node.select()
        .where(Node.validated == True, Node.nettype == nettype, Node.crypto == crypto)
        .order_by(Node.last_height.desc())
        .limit(1)
        .first()
    )
    if highest:
        return highest.last_height
    else:
        return 0


def get_geoip(ip_or_dns):
    host = urlparse(ip_or_dns).netloc.split(':')[0]
    resolved = socket.gethostbyname(host)
    host = host if resolved == host else resolved
    with geoip2.database.Reader("./data/GeoLite2-City.mmdb") as reader:
        return reader.city(host)

def get_whois(ip_or_dns):
    pass

# asn
# asn_cidr
# asn_country_code
# asn_description
