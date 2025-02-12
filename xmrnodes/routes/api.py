from flask import jsonify, Blueprint

from xmrnodes.models import Node


bp = Blueprint('api', 'api')

@bp.route("/nodes.json")
def nodes_json():
    nodes = Node.select().where(
        Node.validated==True,
        Node.available==True,
        Node.nettype=="mainnet"
    )
    xmr_nodes = [n for n in nodes if n.crypto == "monero"]
    wow_nodes = [n for n in nodes if n.crypto == "wownero"]
    return jsonify({
        "monero": {
            "clear": [n.url for n in xmr_nodes if n.is_tor == False and n.is_i2p == False],
            "onion": [n.url for n in xmr_nodes if n.is_tor == True],
            "i2p": [n.url for n in xmr_nodes if n.is_i2p == True],
            "web_compatible": [n.url for n in xmr_nodes if n.web_compatible == True],
        },
        "wownero": {
            "clear": [n.url for n in wow_nodes if n.is_tor == False and n.is_i2p == False],
            "onion": [n.url for n in wow_nodes if n.is_tor == True],
            "i2p": [n.url for n in wow_nodes if n.is_i2p == True],
            "web_compatible": [n.url for n in wow_nodes if n.web_compatible == True],
        }
    })

@bp.route("/health.json")
def health_json():
    data = {}
    nodes = Node.select().where(
        Node.validated == True
    )
    for node in nodes:
        if node.crypto not in data:
            data[node.crypto] = {}
        _d = {
            "available": node.available,
            "last_height": node.last_height,
            "datetime_entered": node.datetime_entered,
            "datetime_checked": node.datetime_checked,
            "datetime_failed": node.datetime_failed,
            "checks": [c.health for c in node.get_all_checks()]
        }
        nettype = "clear"
        if node.is_tor:
            nettype = "onion"
        elif node.web_compatible:
            if "web_compatible" not in data[node.crypto]:
                data[node.crypto]["web_compatible"] = {}
            data[node.crypto]["web_compatible"][node.url] = _d
        if nettype not in data[node.crypto]:
            data[node.crypto][nettype] = {}
        data[node.crypto][nettype][node.url] = _d
    return jsonify(data)

@bp.route("/wow_nodes.json")
def wow_nodes_json():
    nodes = Node.select().where(
        Node.validated==True
    ).where(
        Node.nettype=="mainnet"
    ).where(
        Node.crypto=="wownero"
    )
    nodes = [n for n in nodes]
    return jsonify({
        "clear": [n.url for n in nodes if n.is_tor == False],
        "onion": [n.url for n in nodes if n.is_tor == True]
    })
