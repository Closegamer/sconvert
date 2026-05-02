import hashlib
import html
import hmac
import importlib
import json
import os
import unicodedata
from decimal import Decimal, getcontext
from typing import Any

import streamlit as st
import requests
import streamlit.components.v1 as components

from .clipboard_iframe import render_clipboard_iframe_button


_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _base58_encode(raw: bytes) -> str:
    num = int.from_bytes(raw, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = _B58_ALPHABET[rem] + encoded
    leading_zeroes = len(raw) - len(raw.lstrip(b"\x00"))
    return ("1" * leading_zeroes) + (encoded or "1")

def _hash160(raw: bytes) -> bytes:
    sha = hashlib.sha256(raw).digest()
    return hashlib.new("ripemd160", sha).digest()

def _pubkey_from_private_int(private_key_int: int, compressed: bool = True) -> bytes:
    from ecdsa import SECP256k1, SigningKey

    signing_key = SigningKey.from_secret_exponent(private_key_int, curve=SECP256k1)
    verifying_key = signing_key.verifying_key
    pub = verifying_key.to_string()
    x = pub[:32]
    y = pub[32:]
    if compressed:
        prefix = b"\x02" if (y[-1] % 2 == 0) else b"\x03"
        return prefix + x
    return b"\x04" + pub

def _btc_address_from_pubkey(pubkey: bytes) -> str:
    versioned_payload = b"\x00" + _hash160(pubkey)
    checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
    return _base58_encode(versioned_payload + checksum)

def _base58_decode(value: str) -> bytes:
    num = 0
    for char in value:
        idx = _B58_ALPHABET.find(char)
        if idx == -1:
            raise ValueError("invalid base58 character")
        num = num * 58 + idx
    raw = num.to_bytes((num.bit_length() + 7) // 8, "big") if num > 0 else b""
    leading_ones = len(value) - len(value.lstrip("1"))
    return (b"\x00" * leading_ones) + raw

def _private_int_to_wif(private_key_int: int, compressed: bool = True) -> str:
    key_bytes = private_key_int.to_bytes(32, "big")
    payload = b"\x80" + key_bytes + (b"\x01" if compressed else b"")
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return _base58_encode(payload + checksum)

def _wif_to_private_int(wif: str) -> int:
    raw = _base58_decode(wif.strip())
    if len(raw) not in (37, 38):
        raise ValueError("invalid wif length")
    payload = raw[:-4]
    checksum = raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise ValueError("invalid checksum")
    if payload[0] != 0x80:
        raise ValueError("unsupported network")
    if len(payload) == 34 and payload[-1] != 0x01:
        raise ValueError("invalid compressed marker")
    key_bytes = payload[1:33]
    return int.from_bytes(key_bytes, "big")

def _hmac_sha512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()

def _ckd_priv(parent_key: bytes, parent_chain_code: bytes, index: int) -> tuple[bytes, bytes]:
    if index >= 0x80000000:
        data = b"\x00" + parent_key + index.to_bytes(4, "big")
    else:
        pubkey = _pubkey_from_private_int(int.from_bytes(parent_key, "big"), compressed=True)
        data = pubkey + index.to_bytes(4, "big")
    i64 = _hmac_sha512(parent_chain_code, data)
    il, ir = i64[:32], i64[32:]
    child_int = (int.from_bytes(il, "big") + int.from_bytes(parent_key, "big")) % int.from_bytes(
        b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xba\xae\xdc\xe6\xaf\x48\xa0\x3b\xbf\xd2\x5e\x8c\xd0\x36\x41\x41",
        "big",
    )
    if child_int == 0:
        raise ValueError("invalid child key")
    return child_int.to_bytes(32, "big"), ir

def _private_int_from_seed_phrase(seed_phrase: str) -> int:
    phrase = " ".join(seed_phrase.strip().split())
    words = phrase.split(" ")
    if len(words) not in (12, 24):
        raise ValueError("invalid seed phrase length")
    normalized_phrase = unicodedata.normalize("NFKD", phrase)
    seed = hashlib.pbkdf2_hmac(
        "sha512",
        normalized_phrase.encode("utf-8"),
        b"mnemonic",
        2048,
        dklen=64,
    )
    master = _hmac_sha512(b"Bitcoin seed", seed)
    key, chain_code = master[:32], master[32:]
    for index in (44 + 0x80000000, 0 + 0x80000000, 0 + 0x80000000, 0, 0):
        key, chain_code = _ckd_priv(key, chain_code, index)
    return int.from_bytes(key, "big")

def _hash160_to_p2pkh(hash160: bytes) -> str:
    versioned_payload = b"\x00" + hash160
    checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
    return _base58_encode(versioned_payload + checksum)

def _hash160_to_p2sh_p2wpkh(hash160: bytes) -> str:
    redeem_script = b"\x00\x14" + hash160
    script_hash = _hash160(redeem_script)
    versioned_payload = b"\x05" + script_hash
    checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
    return _base58_encode(versioned_payload + checksum)

def _convertbits(data: list[int], from_bits: int, to_bits: int, pad: bool = True) -> list[int]:
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << to_bits) - 1
    for value in data:
        if value < 0 or (value >> from_bits):
            raise ValueError("invalid data range")
        acc = (acc << from_bits) | value
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & maxv)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & maxv):
        raise ValueError("invalid padding")
    return ret

def _bech32_polymod(values: list[int]) -> int:
    generator = [0x3b6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= generator[i]
    return chk

def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def _bech32_create_checksum(hrp: str, data: list[int]) -> list[int]:
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

def _bech32_encode(hrp: str, data: list[int]) -> str:
    combined = data + _bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join([_BECH32_CHARSET[d] for d in combined])

def _bech32_verify_checksum(hrp: str, data: list[int]) -> bool:
    return _bech32_polymod(_bech32_hrp_expand(hrp) + data) == 1

def _bech32_decode(addr: str) -> tuple[str, list[int]]:
    if not addr or addr.lower() != addr:
        raise ValueError("invalid bech32 format")
    pos = addr.rfind("1")
    if pos < 1 or pos + 7 > len(addr):
        raise ValueError("invalid bech32 separator")
    hrp = addr[:pos]
    data_part = addr[pos + 1 :]
    data = []
    for c in data_part:
        idx = _BECH32_CHARSET.find(c)
        if idx == -1:
            raise ValueError("invalid bech32 character")
        data.append(idx)
    if not _bech32_verify_checksum(hrp, data):
        raise ValueError("invalid bech32 checksum")
    return hrp, data[:-6]

def _hash160_to_p2wpkh(hash160: bytes, hrp: str = "bc") -> str:
    data = [0] + _convertbits(list(hash160), 8, 5, True)
    return _bech32_encode(hrp, data)

def _hash160_from_p2pkh(address: str) -> bytes:
    raw = _base58_decode(address.strip())
    if len(raw) != 25:
        raise ValueError("invalid address length")
    payload = raw[:-4]
    checksum = raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise ValueError("invalid checksum")
    if payload[0] != 0x00:
        raise ValueError("unsupported network")
    return payload[1:]

def _hash160_from_p2sh_p2wpkh(address: str) -> bytes:
    raw = _base58_decode(address.strip())
    if len(raw) != 25:
        raise ValueError("invalid address length")
    payload = raw[:-4]
    checksum = raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise ValueError("invalid checksum")
    if payload[0] != 0x05:
        raise ValueError("unsupported network")
    script_hash = payload[1:]
    # For P2SH-P2WPKH we cannot recover key hash from script-hash only.
    # This field is accepted as input for consistency but cannot fan out.
    raise ValueError("p2sh hash cannot be reversed to key hash")

def _hash160_from_p2wpkh(address: str) -> bytes:
    hrp, data = _bech32_decode(address.strip().lower())
    if hrp != "bc":
        raise ValueError("unsupported hrp")
    if not data or data[0] != 0:
        raise ValueError("unsupported witness version")
    decoded = bytes(_convertbits(data[1:], 5, 8, False))
    if len(decoded) != 20:
        raise ValueError("invalid witness program length")
    return decoded

def _describe_address_type_network(address: str, texts: dict[str, str]) -> str:
    candidate = address.strip()
    if not candidate:
        return ""
    lower = candidate.lower()
    if lower.startswith("bc1"):
        return f"{texts['btc.address_info.type']}: Bech32 (P2WPKH), {texts['btc.address_info.network']}: mainnet"
    if lower.startswith("tb1"):
        return f"{texts['btc.address_info.type']}: Bech32 (P2WPKH), {texts['btc.address_info.network']}: testnet"
    try:
        raw = _base58_decode(candidate)
    except ValueError:
        return texts["btc.address_info.unknown"]
    if len(raw) < 1:
        return texts["btc.address_info.unknown"]
    version = raw[0]
    mapping = {
        0x00: ("P2PKH", "mainnet"),
        0x05: ("P2SH", "mainnet"),
        0x6F: ("P2PKH", "testnet"),
        0xC4: ("P2SH", "testnet"),
    }
    if version not in mapping:
        return texts["btc.address_info.unknown"]
    addr_type, network = mapping[version]
    return f"{texts['btc.address_info.type']}: {addr_type}, {texts['btc.address_info.network']}: {network}"

def _compress_uncompressed_pubkey(uncompressed: bytes) -> bytes:
    if len(uncompressed) != 65 or uncompressed[0] != 0x04:
        raise ValueError("invalid uncompressed key")
    x = uncompressed[1:33]
    y = uncompressed[33:]
    prefix = b"\x02" if (y[-1] % 2 == 0) else b"\x03"
    return prefix + x

def _decompress_compressed_pubkey(compressed: bytes) -> bytes:
    from ecdsa import SECP256k1
    from ecdsa.ellipticcurve import Point

    if len(compressed) != 33 or compressed[0] not in (2, 3):
        raise ValueError("invalid compressed key")
    x = int.from_bytes(compressed[1:], "big")
    p = SECP256k1.curve.p()
    alpha = (pow(x, 3, p) + 7) % p
    beta = pow(alpha, (p + 1) // 4, p)
    y_even = beta if beta % 2 == 0 else p - beta
    y_odd = p - y_even
    y = y_even if compressed[0] == 2 else y_odd
    try:
        _ = Point(SECP256k1.curve, x, y)
    except AssertionError as exc:
        raise ValueError("point is not on secp256k1") from exc
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")

def _is_pubkey_hex(token: str) -> bool:
    if len(token) not in (66, 130):
        return False
    if not token.startswith(("02", "03", "04")):
        return False
    try:
        bytes.fromhex(token)
    except ValueError:
        return False
    return True

def _extract_pubkey_from_vin(vin: dict) -> str | None:
    witness = vin.get("witness")
    if isinstance(witness, list):
        for item in witness:
            if isinstance(item, str):
                token = item.lower()
                if _is_pubkey_hex(token):
                    return token
    scriptsig_asm = vin.get("scriptsig_asm")
    if isinstance(scriptsig_asm, str):
        for token in scriptsig_asm.lower().split():
            if _is_pubkey_hex(token):
                return token
    return None

def _pubkey_pair_from_hex(found_pubkey_hex: str) -> tuple[bytes, bytes]:
    from ecdsa import SECP256k1, VerifyingKey

    found_pubkey = bytes.fromhex(found_pubkey_hex.strip().lower())
    if len(found_pubkey) == 33 and found_pubkey[0] in (2, 3):
        pubkey_compressed = found_pubkey
        # ecdsa expects full compressed encoding (33 bytes), not raw X-only (32 bytes).
        VerifyingKey.from_string(pubkey_compressed, curve=SECP256k1)
        pubkey_uncompressed = _decompress_compressed_pubkey(found_pubkey)
        return pubkey_compressed, pubkey_uncompressed
    if len(found_pubkey) == 65 and found_pubkey[0] == 0x04:
        VerifyingKey.from_string(found_pubkey[1:], curve=SECP256k1)
        pubkey_uncompressed = found_pubkey
        pubkey_compressed = _compress_uncompressed_pubkey(found_pubkey)
        return pubkey_compressed, pubkey_uncompressed
    raise ValueError("unexpected pubkey length")

def _lookup_pubkey_by_address(address: str) -> str | None:
    url = f"https://blockstream.info/api/address/{address}/txs"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    txs = response.json()
    if not isinstance(txs, list):
        return None
    for tx in txs:
        vin_list = tx.get("vin", [])
        if not isinstance(vin_list, list):
            continue
        for vin in vin_list:
            if not isinstance(vin, dict):
                continue
            prevout = vin.get("prevout")
            if not isinstance(prevout, dict):
                continue
            if prevout.get("scriptpubkey_address") != address:
                continue
            pubkey = _extract_pubkey_from_vin(vin)
            if pubkey:
                return pubkey
    return None

def _lookup_balance_sats(address: str) -> int:
    url = f"https://blockstream.info/api/address/{address}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("invalid balance payload")
    chain = payload.get("chain_stats", {}) if isinstance(payload.get("chain_stats"), dict) else {}
    mempool = payload.get("mempool_stats", {}) if isinstance(payload.get("mempool_stats"), dict) else {}
    funded = int(chain.get("funded_txo_sum", 0)) + int(mempool.get("funded_txo_sum", 0))
    spent = int(chain.get("spent_txo_sum", 0)) + int(mempool.get("spent_txo_sum", 0))
    return funded - spent

def _lookup_address_summary(address: str) -> dict[str, int]:
    url = f"https://blockstream.info/api/address/{address}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("invalid address summary payload")
    chain = payload.get("chain_stats", {}) if isinstance(payload.get("chain_stats"), dict) else {}
    mempool = payload.get("mempool_stats", {}) if isinstance(payload.get("mempool_stats"), dict) else {}
    funded = int(chain.get("funded_txo_sum", 0)) + int(mempool.get("funded_txo_sum", 0))
    spent = int(chain.get("spent_txo_sum", 0)) + int(mempool.get("spent_txo_sum", 0))
    return {
        "received": funded,
        "sent": spent,
        "balance": funded - spent,
    }

def _lookup_tip_height() -> int:
    response = requests.get("https://blockstream.info/api/blocks/tip/height", timeout=10)
    response.raise_for_status()
    return int(str(response.text).strip())

def _lookup_transactions(address: str) -> list[dict]:
    url = f"https://blockstream.info/api/address/{address}/txs"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("invalid tx payload")
    return [tx for tx in payload if isinstance(tx, dict)]

def _lookup_utxos(address: str) -> list[dict]:
    url = f"https://blockstream.info/api/address/{address}/utxo"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("invalid utxo payload")
    return [utxo for utxo in payload if isinstance(utxo, dict)]

def _format_utxos_for_view(utxos: list[dict], texts: dict[str, str]) -> str:
    lines: list[str] = []
    for i, utxo in enumerate(utxos, start=1):
        txid = str(utxo.get("txid", ""))
        vout = utxo.get("vout")
        value = utxo.get("value")
        status = utxo.get("status", {}) if isinstance(utxo.get("status"), dict) else {}
        confirmed = bool(status.get("confirmed", False))
        block_height = status.get("block_height")
        lines.append(f"{i}. txid: {txid}")
        lines.append(f"   vout: {vout}")
        if value is not None:
            try:
                value_int = int(value)
                lines.append(f"   value: {value_int} sats ({value_int / 100_000_000:.8f} BTC)")
            except (TypeError, ValueError):
                lines.append(f"   value: {value}")
        lines.append(f"   confirmed: {texts['universal_yes_word'] if confirmed else texts['universal_no_word']}")
        if block_height is not None:
            lines.append(f"   block: {block_height}")
        lines.append("")
    return "\n".join(lines).strip()

def _render_pubkey_curve_visualization(pubkey_uncompressed_hex: str, texts: dict[str, str]) -> None:
    try:
        from ecdsa import SECP256k1
    except ModuleNotFoundError:
        return

    raw = bytes.fromhex(pubkey_uncompressed_hex)
    if len(raw) != 65 or raw[0] != 0x04:
        return

    x = int.from_bytes(raw[1:33], "big")
    y = int.from_bytes(raw[33:], "big")
    p = SECP256k1.curve.p()

    on_curve = (pow(y, 2, p) - (pow(x, 3, p) + 7)) % p == 0
    x_norm = x / p

    svg_w = 520
    svg_h = 300
    pad = 36
    plot_w = svg_w - pad * 2
    plot_h = svg_h - pad * 2

    # Educational projection over real numbers: y^2 = x^3 + 7.
    # This is used only for visual intuition.
    x_min = -4.0
    x_max = 4.0
    # Keep full plotted curve visible for the selected X-range.
    y_abs_max = ((x_max * x_max * x_max) + 7.0) ** 0.5
    y_padding = max(0.6, y_abs_max * 0.08)
    y_min = -(y_abs_max + y_padding)
    y_max = y_abs_max + y_padding

    def _to_svg(xr: float, yr: float) -> tuple[float, float]:
        nx = (xr - x_min) / (x_max - x_min)
        ny = (yr - y_min) / (y_max - y_min)
        return (pad + nx * plot_w, pad + (1 - ny) * plot_h)

    curve_top: list[str] = []
    curve_bottom: list[str] = []
    samples = 360
    for i in range(samples + 1):
        xr = x_min + (x_max - x_min) * (i / samples)
        val = xr * xr * xr + 7.0
        if val <= 0:
            continue
        yr = val ** 0.5
        tx, ty = _to_svg(xr, yr)
        bx, by = _to_svg(xr, -yr)
        curve_top.append(f"{tx:.2f},{ty:.2f}")
        curve_bottom.append(f"{bx:.2f},{by:.2f}")

    polyline_top = " ".join(curve_top)
    polyline_bottom = " ".join(curve_bottom)

    # Project key point onto displayed real-number curve using x derived from field x.
    xr_point = x_min + x_norm * (x_max - x_min)
    val_point = xr_point * xr_point * xr_point + 7.0
    if val_point <= 0:
        xr_point = 2.0
        val_point = xr_point * xr_point * xr_point + 7.0
    yr_point = val_point ** 0.5
    if y % 2 == 1:
        yr_point = -yr_point
    px, py = _to_svg(xr_point, yr_point)

    axis_x1, axis_y0 = _to_svg(x_min, 0.0)
    axis_x2, _ = _to_svg(x_max, 0.0)
    axis_yx, axis_y1 = _to_svg(0.0, y_max)
    _, axis_y2 = _to_svg(0.0, y_min)

    st.markdown(f"**{texts['btc.curve.title']}**")
    st.markdown(
        "<br>".join(
            [
                texts["btc.curve.subtitle"],
                f"{texts['btc.curve.x']}: 0x{raw[1:33].hex()}",
                f"{texts['btc.curve.y']}: 0x{raw[33:].hex()}",
                f"{texts['btc.curve.on_curve']}: {texts['universal_yes_word'] if on_curve else texts['universal_no_word']}",
            ]
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <svg width="100%" viewBox="0 0 {svg_w} {svg_h}" preserveAspectRatio="xMidYMid meet">
          <rect x="{pad}" y="{pad}" width="{plot_w}" height="{plot_h}" fill="#07110b" stroke="#1d3324" stroke-width="2"/>
          <line x1="{axis_x1}" y1="{axis_y0}" x2="{axis_x2}" y2="{axis_y0}" stroke="#6f7f77" stroke-width="1.2"/>
          <line x1="{axis_yx}" y1="{axis_y1}" x2="{axis_yx}" y2="{axis_y2}" stroke="#6f7f77" stroke-width="1.2"/>
          <polyline points="{polyline_top}" fill="none" stroke="#f05a5a" stroke-width="1.6" opacity="0.95"/>
          <polyline points="{polyline_bottom}" fill="none" stroke="#f05a5a" stroke-width="1.6" opacity="0.95"/>
          <text x="{pad + plot_w - 6}" y="{pad + plot_h + 22}" fill="#86b593" font-size="12" text-anchor="end">x / p</text>
          <text x="{pad - 10}" y="{pad + 14}" fill="#86b593" font-size="12" text-anchor="end">y / p</text>
          <circle cx="{px}" cy="{py}" r="6" fill="#1fcf62" stroke="#d9ffe3" stroke-width="1.5"/>
          <text x="{px + 10}" y="{py - 10}" fill="#d9ffe3" font-size="12">P(x, y)</text>
        </svg>
        """,
        unsafe_allow_html=True,
    )

def _render_private_key_line_visualization(private_key_int: int, curve_order: int, texts: dict[str, str]) -> None:
    if private_key_int <= 0 or private_key_int >= curve_order:
        return
    svg_w = 520
    svg_h = 96
    pad_x = 28
    y = 48
    x1 = pad_x
    x2 = svg_w - pad_x
    span = x2 - x1
    # High-precision mapping keeps smooth sub-pixel movement for huge integers.
    getcontext().prec = 80
    ratio = Decimal(private_key_int - 1) / Decimal(curve_order - 2)
    px = Decimal(x1) + (Decimal(span) * ratio)
    position_percent = ratio * Decimal(100)
    st.markdown(f"**{texts['btc.keyline.title']}**")
    st.markdown(
        (
            f"{texts['btc.keyline.subtitle']}<br>"
            f"{texts['btc.keyline.current']}: {private_key_int}<br>"
            f"{texts['btc.keyline.position']}: {position_percent:.12f}%"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <svg width="100%" viewBox="0 0 {svg_w} {svg_h}" preserveAspectRatio="xMidYMid meet">
          <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#4e6b57" stroke-width="3"/>
          <line x1="{x1}" y1="{y - 9}" x2="{x1}" y2="{y + 9}" stroke="#86b593" stroke-width="1.3"/>
          <line x1="{x2}" y1="{y - 9}" x2="{x2}" y2="{y + 9}" stroke="#86b593" stroke-width="1.3"/>
          <circle cx="{px:.3f}" cy="{y}" r="6" fill="#1fcf62" stroke="#d9ffe3" stroke-width="1.5"/>
          <text x="{x1}" y="{y + 25}" fill="#86b593" font-size="11" text-anchor="start">1</text>
          <text x="{x2}" y="{y + 25}" fill="#86b593" font-size="11" text-anchor="end">n-1</text>
        </svg>
        """,
        unsafe_allow_html=True,
    )

def _tx_amounts_for_address(tx: dict, address: str) -> tuple[int, int]:
    received = 0
    sent = 0

    vout_list = tx.get("vout", [])
    if isinstance(vout_list, list):
        for vout in vout_list:
            if not isinstance(vout, dict):
                continue
            if vout.get("scriptpubkey_address") == address:
                try:
                    received += int(vout.get("value", 0))
                except (TypeError, ValueError):
                    pass

    vin_list = tx.get("vin", [])
    if isinstance(vin_list, list):
        for vin in vin_list:
            if not isinstance(vin, dict):
                continue
            prevout = vin.get("prevout")
            if not isinstance(prevout, dict):
                continue
            if prevout.get("scriptpubkey_address") == address:
                try:
                    sent += int(prevout.get("value", 0))
                except (TypeError, ValueError):
                    pass

    return received, sent

def _format_transactions_for_view(txs: list[dict], address: str, tip_height: int | None = None) -> str:
    lines: list[str] = []
    for i, tx in enumerate(txs, start=1):
        txid = str(tx.get("txid", ""))
        fee = tx.get("fee")
        status = tx.get("status", {}) if isinstance(tx.get("status"), dict) else {}
        confirmed = bool(status.get("confirmed", False))
        block_height = status.get("block_height")
        confirmations = 0
        if confirmed and isinstance(block_height, int) and isinstance(tip_height, int):
            confirmations = max(0, tip_height - block_height + 1)
        received_sats, sent_sats = _tx_amounts_for_address(tx, address)
        net_sats = received_sats - sent_sats
        lines.append(f"{i}. txid: {txid}")
        lines.append(f"   confirmed: {'yes' if confirmed else 'no'}")
        lines.append(f"   confirmations: {confirmations}")
        if block_height is not None:
            lines.append(f"   block: {block_height}")
        lines.append(f"   received: {received_sats} sats ({received_sats / 100_000_000:.8f} BTC)")
        lines.append(f"   sent: {sent_sats} sats ({sent_sats / 100_000_000:.8f} BTC)")
        lines.append(f"   net: {net_sats:+d} sats ({net_sats / 100_000_000:+.8f} BTC)")
        if fee is not None:
            lines.append(f"   fee: {fee} sats")
        lines.append("")
    return "\n".join(lines).strip()

def _is_valid_p2sh_address(address: str) -> bool:
    raw = _base58_decode(address.strip())
    if len(raw) != 25:
        return False
    payload = raw[:-4]
    checksum = raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return checksum == expected and payload[0] in (0x05, 0xC4)

def _address_validation_status(field_name: str, value: str, texts: dict[str, str]) -> str:
    candidate = value.strip()
    if not candidate:
        return ""
    try:
        if field_name in {"address", "address_uncompressed"}:
            _hash160_from_p2pkh(candidate)
        elif field_name == "address_p2wpkh":
            _hash160_from_p2wpkh(candidate)
        elif field_name == "address_p2sh":
            if not _is_valid_p2sh_address(candidate):
                raise ValueError("invalid p2sh")
        else:
            return ""
        return texts["btc.validation.valid"]
    except ValueError:
        return texts["btc.validation.invalid"]

def _render_copy_button(texts: dict[str, str], value: str, key: str) -> None:
    render_clipboard_iframe_button(
        label=texts["btc.copy"].lower(),
        value=value,
        element_key=key,
        height=32,
    )

def _normalize_signature_value(field_name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    if field_name in {
        "private_hex",
        "public_key",
        "public_key_uncompressed",
        "ripemd160",
        "ripemd160_uncompressed",
    }:
        return normalized.lower().removeprefix("0x")
    return normalized

def _build_request_signature(entry_point_field: str, entry_value: str) -> str:
    normalized_value = _normalize_signature_value(entry_point_field, entry_value)
    payload = {
        "entry_point_field": entry_point_field,
        "entry_value": normalized_value,
        "cache_version": 1,
    }
    body = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()

@st.cache_resource
def _get_redis_client():
    try:
        redis_module = importlib.import_module("redis")
    except ModuleNotFoundError:
        return None
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        return redis_module.Redis.from_url(redis_url, decode_responses=True)
    except Exception:
        return None

def _db_dsn() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://sconvert:dev_only_change_me@db:5432/sconvert",
    )

def _load_conversion_record_by_signature(request_signature: str) -> dict[str, Any] | None:
    try:
        psycopg_module = importlib.import_module("psycopg")
    except ModuleNotFoundError:
        return None
    query = """
        SELECT
            request_signature,
            entry_point_field,
            in_private_dec,
            in_private_hex,
            in_private_wif,
            in_private_wif_u,
            in_seed_phrase,
            in_public_key_c,
            in_public_key_u,
            in_ripemd160_c,
            in_ripemd160_u,
            in_address_c,
            in_address_u,
            in_address_p2sh,
            in_address_p2wpkh,
            out_private_dec,
            out_private_hex,
            out_private_hex_normalized,
            out_private_wif,
            out_private_wif_u,
            out_public_key_c,
            out_public_key_u,
            out_ripemd160_c,
            out_ripemd160_u,
            out_address_c,
            out_address_u,
            out_address_p2sh,
            out_address_p2wpkh,
            out_address_info,
            out_balance_text,
            out_address_summary_text,
            out_utxos_text,
            out_txs_text,
            out_private_key_position_percent,
            out_pubkey_on_curve,
            out_pubkey_curve_error
        FROM btc_conversion_log
        WHERE request_signature = %s
        LIMIT 1
    """
    try:
        with psycopg_module.connect(_db_dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (request_signature,))
                row = cur.fetchone()
                if not row:
                    return None
                columns = [desc.name for desc in cur.description]
                return dict(zip(columns, row))
    except Exception:
        return None

def _insert_conversion_record(record: dict[str, Any]) -> None:
    try:
        psycopg_module = importlib.import_module("psycopg")
    except ModuleNotFoundError:
        return
    columns = list(record.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"""
        INSERT INTO btc_conversion_log ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (request_signature) DO UPDATE
        SET updated_at = NOW()
    """
    values = [record[col] for col in columns]
    try:
        with psycopg_module.connect(_db_dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()
    except Exception:
        return

def _cache_get(redis_client, request_signature: str) -> dict[str, Any] | None:
    if redis_client is None:
        return None
    redis_key = f"btc:conv:v1:{request_signature}"
    try:
        payload = redis_client.get(redis_key)
        if not payload:
            return None
        data = json.loads(payload)
        return data if isinstance(data, dict) else None
    except Exception:
        return None

def _cache_set(redis_client, request_signature: str, payload: dict[str, Any], ttl_seconds: int = 120) -> None:
    if redis_client is None:
        return
    redis_key = f"btc:conv:v1:{request_signature}"
    try:
        redis_client.setex(redis_key, ttl_seconds, json.dumps(payload, ensure_ascii=True))
    except Exception:
        return

def _apply_record_to_session(record: dict[str, Any], field_keys: dict[str, str]) -> None:
    mapping = {
        "private_dec": "out_private_dec",
        "private_hex": "out_private_hex",
        "private_wif": "out_private_wif",
        "private_wif_uncompressed": "out_private_wif_u",
        "seed_phrase": "in_seed_phrase",
        "public_key": "out_public_key_c",
        "public_key_uncompressed": "out_public_key_u",
        "ripemd160": "out_ripemd160_c",
        "ripemd160_uncompressed": "out_ripemd160_u",
        "address": "out_address_c",
        "address_uncompressed": "out_address_u",
        "address_p2sh": "out_address_p2sh",
        "address_p2wpkh": "out_address_p2wpkh",
        "private_dec_norm": "out_private_dec",
        "private_hex_norm": "out_private_hex_normalized",
        "balance": "out_balance_text",
        "address_summary": "out_address_summary_text",
        "address_info": "out_address_info",
        "utxos_view": "out_utxos_text",
        "txs_view": "out_txs_text",
    }
    for session_name, record_name in mapping.items():
        value = record.get(record_name)
        st.session_state[field_keys[session_name]] = "" if value is None else str(value)
    curve_error = record.get("out_pubkey_curve_error")
    st.session_state.btc_pubkey_curve_error = "" if curve_error is None else str(curve_error)

def render_btc_keys_component(texts: dict[str, str]) -> None:
    try:
        from ecdsa import SECP256k1, VerifyingKey
    except ModuleNotFoundError:
        st.error(texts["btc.error.ecdsa"])
        return

    field_keys = {
        "private_dec": "btc_private_dec",
        "private_hex": "btc_private_hex",
        "private_wif": "btc_private_wif",
        "private_wif_uncompressed": "btc_private_wif_uncompressed",
        "seed_phrase": "btc_seed_phrase",
        "public_key": "btc_public_key_compressed",
        "public_key_uncompressed": "btc_public_key_uncompressed",
        "ripemd160": "btc_ripemd160",
        "ripemd160_uncompressed": "btc_ripemd160_uncompressed",
        "address": "btc_address",
        "address_uncompressed": "btc_address_uncompressed",
        "address_p2sh": "btc_address_p2sh",
        "address_p2wpkh": "btc_address_p2wpkh",
        "balance": "btc_balance",
        "address_summary": "btc_address_summary",
        "address_info": "btc_address_info",
        "utxos_view": "btc_utxos_view",
        "txs_view": "btc_txs_view",
        "private_dec_norm": "btc_private_dec_norm",
        "private_hex_norm": "btc_private_hex_norm",
    }

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    clear_left_col, clear_right_col = st.columns([4, 1], vertical_alignment="center")
    with clear_right_col:
        if st.button(texts["btc.clear_all"], key="btc_clear_all_button", use_container_width=True):
            for state_key in field_keys.values():
                st.session_state[state_key] = ""
            st.session_state.btc_last_inputs = {}
            st.rerun()

    for state_key in field_keys.values():
        if state_key not in st.session_state:
            st.session_state[state_key] = ""
    if "btc_last_inputs" not in st.session_state:
        st.session_state.btc_last_inputs = {}
    if "btc_pubkey_curve_error" not in st.session_state:
        st.session_state.btc_pubkey_curve_error = ""

    def _render_input_with_count(label: str, key: str, disabled: bool = False, show_count: bool = True) -> None:
        value = str(st.session_state.get(key, ""))
        display_label = f"{label} [{len(value)}]" if show_count else label
        st.text_input(display_label, key=key, disabled=disabled)

    def _render_textarea_with_count(
        label: str,
        key: str,
        height: int,
        disabled: bool = False,
        show_count: bool = True,
    ) -> None:
        value = str(st.session_state.get(key, ""))
        display_label = f"{label} [{len(value)}]" if show_count else label
        st.text_area(display_label, key=key, height=height, disabled=disabled)

    current_inputs = {
        "private_dec": st.session_state[field_keys["private_dec"]],
        "private_hex": st.session_state[field_keys["private_hex"]],
        "private_wif": st.session_state[field_keys["private_wif"]],
        "private_wif_uncompressed": st.session_state[field_keys["private_wif_uncompressed"]],
        "seed_phrase": st.session_state[field_keys["seed_phrase"]],
        "public_key": st.session_state[field_keys["public_key"]],
        "public_key_uncompressed": st.session_state[field_keys["public_key_uncompressed"]],
        "ripemd160": st.session_state[field_keys["ripemd160"]],
        "ripemd160_uncompressed": st.session_state[field_keys["ripemd160_uncompressed"]],
        "address": st.session_state[field_keys["address"]],
        "address_uncompressed": st.session_state[field_keys["address_uncompressed"]],
        "address_p2sh": st.session_state[field_keys["address_p2sh"]],
        "address_p2wpkh": st.session_state[field_keys["address_p2wpkh"]],
    }
    last_inputs: dict[str, str] = st.session_state.btc_last_inputs
    changed_field = next(
        (k for k in current_inputs.keys() if current_inputs[k] != last_inputs.get(k, "")),
        None,
    )
    redis_client = _get_redis_client()
    request_signature: str | None = None
    entry_point_map = {
        "private_wif_uncompressed": "private_wif_u",
        "public_key": "public_key_c",
        "public_key_uncompressed": "public_key_u",
        "ripemd160": "ripemd160_c",
        "ripemd160_uncompressed": "ripemd160_u",
        "address": "address_c",
        "address_uncompressed": "address_u",
    }
    changed_field_for_log: str | None = entry_point_map.get(changed_field, changed_field)
    loaded_from_cache = False

    if changed_field is not None:
        candidate_value = str(current_inputs.get(changed_field, "")).strip()
        if candidate_value:
            request_signature = _build_request_signature(changed_field, candidate_value)
            cached_record = _cache_get(redis_client, request_signature)
            if cached_record is None:
                cached_record = _load_conversion_record_by_signature(request_signature)
                if cached_record is not None:
                    _cache_set(redis_client, request_signature, cached_record, ttl_seconds=120)
            if cached_record is not None:
                _apply_record_to_session(cached_record, field_keys)
                loaded_from_cache = True
                changed_field = None

    if changed_field is not None:
        for field_name in current_inputs.keys():
            if field_name == changed_field:
                continue
            st.session_state[field_keys[field_name]] = ""
        st.session_state[field_keys["private_dec_norm"]] = ""
        st.session_state[field_keys["private_hex_norm"]] = ""
        st.session_state[field_keys["balance"]] = ""
        st.session_state[field_keys["address_summary"]] = ""
        st.session_state[field_keys["address_info"]] = ""
        st.session_state[field_keys["utxos_view"]] = ""
        st.session_state[field_keys["txs_view"]] = ""
        st.session_state.btc_pubkey_curve_error = ""

    private_key_int: int | None = None
    pubkey_compressed: bytes | None = None
    pubkey_uncompressed: bytes | None = None
    hash160: bytes | None = None
    hash160_uncompressed: bytes | None = None
    address: str | None = None
    address_uncompressed: str | None = None

    if changed_field is not None:
        raw_value = current_inputs[changed_field].strip()
        if raw_value:
            try:
                if changed_field == "private_dec":
                    private_key_int = int(raw_value, 10)
                elif changed_field == "private_hex":
                    private_key_int = int(raw_value.lower().removeprefix("0x"), 16)
                elif changed_field == "private_wif":
                    private_key_int = _wif_to_private_int(raw_value)
                elif changed_field == "private_wif_uncompressed":
                    private_key_int = _wif_to_private_int(raw_value)
                elif changed_field == "seed_phrase":
                    private_key_int = _private_int_from_seed_phrase(raw_value)
                elif changed_field == "public_key":
                    pubkey_compressed = bytes.fromhex(raw_value.lower().removeprefix("0x"))
                    pubkey_uncompressed = _decompress_compressed_pubkey(pubkey_compressed)
                elif changed_field == "public_key_uncompressed":
                    pubkey_uncompressed = bytes.fromhex(raw_value.lower().removeprefix("0x"))
                    if len(pubkey_uncompressed) != 65 or pubkey_uncompressed[0] != 0x04:
                        raise ValueError("invalid uncompressed key")
                    VerifyingKey.from_string(pubkey_uncompressed[1:], curve=SECP256k1)
                    pubkey_compressed = _compress_uncompressed_pubkey(pubkey_uncompressed)
                elif changed_field == "ripemd160":
                    hash160 = bytes.fromhex(raw_value.lower().removeprefix("0x"))
                    if len(hash160) != 20:
                        raise ValueError("invalid hash160 length")
                elif changed_field == "ripemd160_uncompressed":
                    hash160_uncompressed = bytes.fromhex(raw_value.lower().removeprefix("0x"))
                    if len(hash160_uncompressed) != 20:
                        raise ValueError("invalid hash160 length")
                elif changed_field in {"address", "address_uncompressed"}:
                    addr_s = raw_value.strip()
                    if changed_field == "address":
                        try:
                            hash160 = _hash160_from_p2pkh(addr_s)
                        except ValueError:
                            try:
                                hash160 = _hash160_from_p2wpkh(addr_s)
                            except ValueError:
                                if not _is_valid_p2sh_address(addr_s):
                                    raise ValueError("unsupported address format")
                    else:
                        hash160_uncompressed = _hash160_from_p2pkh(addr_s)
                    try:
                        found_pubkey_hex = _lookup_pubkey_by_address(addr_s)
                    except requests.RequestException:
                        found_pubkey_hex = None
                    if found_pubkey_hex:
                        try:
                            pubkey_compressed, pubkey_uncompressed = _pubkey_pair_from_hex(found_pubkey_hex)
                        except ValueError:
                            pass
                elif changed_field == "address_p2wpkh":
                    hash160 = _hash160_from_p2wpkh(raw_value)
                    try:
                        found_pubkey_hex = _lookup_pubkey_by_address(raw_value.strip())
                    except requests.RequestException:
                        found_pubkey_hex = None
                    if found_pubkey_hex:
                        try:
                            pubkey_compressed, pubkey_uncompressed = _pubkey_pair_from_hex(found_pubkey_hex)
                        except ValueError:
                            pass
                elif changed_field == "address_p2sh":
                    if not _is_valid_p2sh_address(raw_value):
                        raise ValueError("invalid p2sh address")
                    try:
                        found_pubkey_hex = _lookup_pubkey_by_address(raw_value.strip())
                    except requests.RequestException:
                        found_pubkey_hex = None
                    if found_pubkey_hex:
                        try:
                            pubkey_compressed, pubkey_uncompressed = _pubkey_pair_from_hex(found_pubkey_hex)
                        except ValueError:
                            pass
                else:
                    raise ValueError("unsupported field")
            except ValueError:
                if changed_field in {"public_key", "public_key_uncompressed"}:
                    st.session_state.btc_pubkey_curve_error = texts["btc.error.pubkey_not_on_curve"]
                elif changed_field == "seed_phrase":
                    st.error(texts["btc.error.seed_phrase"])
                # Keep current values and wait for valid input.
                pass

    if private_key_int is not None:
        curve_order = SECP256k1.order
        if private_key_int <= 0 or private_key_int >= curve_order:
            st.error(texts["btc.error.range"])
        else:
            pubkey_compressed = _pubkey_from_private_int(private_key_int, compressed=True)
            pubkey_uncompressed = _pubkey_from_private_int(private_key_int, compressed=False)

    if pubkey_compressed is not None:
        hash160 = _hash160(pubkey_compressed)
        address = _btc_address_from_pubkey(pubkey_compressed)
    if pubkey_uncompressed is not None:
        hash160_uncompressed = _hash160(pubkey_uncompressed)
        address_uncompressed = _btc_address_from_pubkey(pubkey_uncompressed)
    if hash160 is not None:
        if address is None:
            address = _hash160_to_p2pkh(hash160)
        address_p2sh = _hash160_to_p2sh_p2wpkh(hash160)
        address_p2wpkh = _hash160_to_p2wpkh(hash160)
    else:
        address_p2sh = None
        address_p2wpkh = None
    if hash160_uncompressed is not None and address_uncompressed is None:
        address_uncompressed = _hash160_to_p2pkh(hash160_uncompressed)

    if private_key_int is not None and 0 < private_key_int < SECP256k1.order:
        normalized_hex = f"{private_key_int:064x}"
        compact_hex = normalized_hex.lstrip("0") or "0"
        st.session_state[field_keys["private_dec"]] = str(private_key_int)
        st.session_state[field_keys["private_hex"]] = compact_hex
        st.session_state[field_keys["private_wif"]] = _private_int_to_wif(private_key_int, compressed=True)
        st.session_state[field_keys["private_wif_uncompressed"]] = _private_int_to_wif(private_key_int, compressed=False)
        st.session_state[field_keys["private_dec_norm"]] = str(private_key_int)
        st.session_state[field_keys["private_hex_norm"]] = normalized_hex
    else:
        st.session_state[field_keys["private_dec_norm"]] = ""
        st.session_state[field_keys["private_hex_norm"]] = ""

    if pubkey_compressed is not None:
        st.session_state[field_keys["public_key"]] = pubkey_compressed.hex()
    if pubkey_uncompressed is not None:
        st.session_state[field_keys["public_key_uncompressed"]] = pubkey_uncompressed.hex()
    if hash160 is not None:
        st.session_state[field_keys["ripemd160"]] = hash160.hex()
    elif changed_field != "ripemd160":
        st.session_state[field_keys["ripemd160"]] = ""
    if hash160_uncompressed is not None:
        st.session_state[field_keys["ripemd160_uncompressed"]] = hash160_uncompressed.hex()
    elif changed_field != "ripemd160_uncompressed":
        st.session_state[field_keys["ripemd160_uncompressed"]] = ""
    if address is not None:
        st.session_state[field_keys["address"]] = address
    if address_uncompressed is not None:
        st.session_state[field_keys["address_uncompressed"]] = address_uncompressed
    if address_p2sh is not None:
        st.session_state[field_keys["address_p2sh"]] = address_p2sh
    if address_p2wpkh is not None:
        st.session_state[field_keys["address_p2wpkh"]] = address_p2wpkh

    if changed_field is not None:
        target_address = ""
        if address:
            target_address = address.strip()
        elif address_uncompressed:
            target_address = address_uncompressed.strip()
        else:
            for name in ("address", "address_uncompressed", "address_p2sh", "address_p2wpkh"):
                candidate = st.session_state.get(field_keys[name], "").strip()
                if candidate:
                    target_address = candidate
                    break
        if target_address:
            try:
                balance_sats = _lookup_balance_sats(target_address)
                st.session_state[field_keys["balance"]] = f"{balance_sats} sats ({balance_sats / 100_000_000:.8f} BTC)"
            except (requests.RequestException, ValueError):
                st.session_state[field_keys["balance"]] = texts["btc.balance.unavailable"]
            try:
                txs = _lookup_transactions(target_address)
                tip_height = _lookup_tip_height()
                if txs:
                    st.session_state[field_keys["txs_view"]] = _format_transactions_for_view(txs, target_address, tip_height)
                else:
                    st.session_state[field_keys["txs_view"]] = texts["btc.txs.empty"]
            except (requests.RequestException, ValueError):
                st.session_state[field_keys["txs_view"]] = texts["btc.txs.unavailable"]
            try:
                utxos = _lookup_utxos(target_address)
                if utxos:
                    st.session_state[field_keys["utxos_view"]] = _format_utxos_for_view(utxos, texts)
                else:
                    st.session_state[field_keys["utxos_view"]] = texts["btc.utxos.empty"]
            except (requests.RequestException, ValueError):
                st.session_state[field_keys["utxos_view"]] = texts["btc.utxos.unavailable"]
            try:
                summary = _lookup_address_summary(target_address)
                st.session_state[field_keys["address_summary"]] = (
                    f"{texts['btc.address_summary.received']}: {summary['received']} sats ({summary['received'] / 100_000_000:.8f} BTC) | "
                    f"{texts['btc.address_summary.sent']}: {summary['sent']} sats ({summary['sent'] / 100_000_000:.8f} BTC) | "
                    f"{texts['btc.address_summary.balance']}: {summary['balance']} sats ({summary['balance'] / 100_000_000:.8f} BTC)"
                )
            except (requests.RequestException, ValueError):
                st.session_state[field_keys["address_summary"]] = texts["btc.address_summary.unavailable"]
        else:
            st.session_state[field_keys["balance"]] = ""
            st.session_state[field_keys["address_summary"]] = ""
            st.session_state[field_keys["utxos_view"]] = ""
            st.session_state[field_keys["txs_view"]] = ""

    info_address = ""
    for name in ("address", "address_uncompressed", "address_p2wpkh", "address_p2sh"):
        value = st.session_state.get(field_keys[name], "").strip()
        if value:
            info_address = value
            break
    st.session_state[field_keys["address_info"]] = _describe_address_type_network(info_address, texts) if info_address else ""

    if request_signature and changed_field_for_log and not loaded_from_cache:
        input_snapshot = {
            "private_dec": "",
            "private_hex": "",
            "private_wif": "",
            "private_wif_uncompressed": "",
            "seed_phrase": "",
            "public_key": "",
            "public_key_uncompressed": "",
            "ripemd160": "",
            "ripemd160_uncompressed": "",
            "address": "",
            "address_uncompressed": "",
            "address_p2sh": "",
            "address_p2wpkh": "",
        }
        if changed_field and changed_field in input_snapshot:
            input_snapshot[changed_field] = str(current_inputs.get(changed_field, "")).strip()
        private_dec_value = str(st.session_state.get(field_keys["private_dec"], "")).strip()
        position_percent: Decimal | None = None
        if private_dec_value.isdigit():
            try:
                private_int = int(private_dec_value, 10)
                if 0 < private_int < SECP256k1.order:
                    getcontext().prec = 80
                    position_percent = (Decimal(private_int - 1) / Decimal(SECP256k1.order - 2)) * Decimal(100)
            except ValueError:
                position_percent = None
        pubkey_u_value = str(st.session_state.get(field_keys["public_key_uncompressed"], "")).strip()
        pubkey_on_curve: bool | None = None
        if pubkey_u_value:
            try:
                raw_pub = bytes.fromhex(pubkey_u_value.lower().removeprefix("0x"))
                if len(raw_pub) == 65 and raw_pub[0] == 0x04:
                    x_int = int.from_bytes(raw_pub[1:33], "big")
                    y_int = int.from_bytes(raw_pub[33:], "big")
                    p_int = SECP256k1.curve.p()
                    pubkey_on_curve = (pow(y_int, 2, p_int) - (pow(x_int, 3, p_int) + 7)) % p_int == 0
            except ValueError:
                pubkey_on_curve = None
        record = {
            "request_signature": request_signature,
            "entry_point_field": changed_field_for_log,
            "in_private_dec": input_snapshot["private_dec"],
            "in_private_hex": input_snapshot["private_hex"],
            "in_private_wif": input_snapshot["private_wif"],
            "in_private_wif_u": input_snapshot["private_wif_uncompressed"],
            "in_seed_phrase": input_snapshot["seed_phrase"],
            "in_public_key_c": input_snapshot["public_key"],
            "in_public_key_u": input_snapshot["public_key_uncompressed"],
            "in_ripemd160_c": input_snapshot["ripemd160"],
            "in_ripemd160_u": input_snapshot["ripemd160_uncompressed"],
            "in_address_c": input_snapshot["address"],
            "in_address_u": input_snapshot["address_uncompressed"],
            "in_address_p2sh": input_snapshot["address_p2sh"],
            "in_address_p2wpkh": input_snapshot["address_p2wpkh"],
            "out_private_dec": str(st.session_state.get(field_keys["private_dec"], "")).strip(),
            "out_private_hex": str(st.session_state.get(field_keys["private_hex"], "")).strip(),
            "out_private_hex_normalized": str(st.session_state.get(field_keys["private_hex_norm"], "")).strip(),
            "out_private_wif": str(st.session_state.get(field_keys["private_wif"], "")).strip(),
            "out_private_wif_u": str(st.session_state.get(field_keys["private_wif_uncompressed"], "")).strip(),
            "out_public_key_c": str(st.session_state.get(field_keys["public_key"], "")).strip(),
            "out_public_key_u": str(st.session_state.get(field_keys["public_key_uncompressed"], "")).strip(),
            "out_ripemd160_c": str(st.session_state.get(field_keys["ripemd160"], "")).strip(),
            "out_ripemd160_u": str(st.session_state.get(field_keys["ripemd160_uncompressed"], "")).strip(),
            "out_address_c": str(st.session_state.get(field_keys["address"], "")).strip(),
            "out_address_u": str(st.session_state.get(field_keys["address_uncompressed"], "")).strip(),
            "out_address_p2sh": str(st.session_state.get(field_keys["address_p2sh"], "")).strip(),
            "out_address_p2wpkh": str(st.session_state.get(field_keys["address_p2wpkh"], "")).strip(),
            "out_address_info": str(st.session_state.get(field_keys["address_info"], "")).strip(),
            "out_balance_text": str(st.session_state.get(field_keys["balance"], "")).strip(),
            "out_address_summary_text": str(st.session_state.get(field_keys["address_summary"], "")).strip(),
            "out_utxos_text": str(st.session_state.get(field_keys["utxos_view"], "")).strip(),
            "out_txs_text": str(st.session_state.get(field_keys["txs_view"], "")).strip(),
            "out_private_key_position_percent": float(position_percent) if position_percent is not None else None,
            "out_pubkey_on_curve": pubkey_on_curve,
            "out_pubkey_curve_error": str(st.session_state.get("btc_pubkey_curve_error", "")).strip(),
            "redis_cache_key": f"btc:conv:v1:{request_signature}",
            "redis_ttl_seconds": 120,
            "cache_version": 1,
        }
        _insert_conversion_record(record)
        _cache_set(redis_client, request_signature, record, ttl_seconds=120)

    _render_input_with_count(texts["btc.private_dec"], field_keys["private_dec"])
    _render_copy_button(texts, str(st.session_state.get(field_keys["private_dec"], "")).strip(), "copy_private_dec")
    _render_textarea_with_count(texts["btc.private_hex"], field_keys["private_hex"], height=78)
    _render_copy_button(texts, str(st.session_state.get(field_keys["private_hex"], "")).strip(), "copy_private_hex")
    _render_textarea_with_count(texts["btc.private_hex_norm"], field_keys["private_hex_norm"], height=78, disabled=True)
    _render_copy_button(texts, str(st.session_state.get(field_keys["private_hex_norm"], "")).strip(), "copy_private_hex_norm")
    _render_textarea_with_count(texts["btc.private_wif"], field_keys["private_wif"], height=78)
    _render_copy_button(texts, str(st.session_state.get(field_keys["private_wif"], "")).strip(), "copy_private_wif")
    _render_textarea_with_count(texts["btc.private_wif_uncompressed"], field_keys["private_wif_uncompressed"], height=78)
    _render_copy_button(
        texts,
        str(st.session_state.get(field_keys["private_wif_uncompressed"], "")).strip(),
        "copy_private_wif_uncompressed",
    )
    _render_textarea_with_count(texts["btc.seed_phrase"], field_keys["seed_phrase"], height=88)
    _render_textarea_with_count(texts["btc.public_key"], field_keys["public_key"], height=78)
    _render_copy_button(texts, str(st.session_state.get(field_keys["public_key"], "")).strip(), "copy_public_key")
    _render_textarea_with_count(texts["btc.public_key_uncompressed"], field_keys["public_key_uncompressed"], height=98)
    _render_copy_button(
        texts,
        str(st.session_state.get(field_keys["public_key_uncompressed"], "")).strip(),
        "copy_public_key_uncompressed",
    )
    _render_input_with_count(texts["btc.ripemd160"], field_keys["ripemd160"])
    _render_input_with_count(texts["btc.ripemd160_uncompressed"], field_keys["ripemd160_uncompressed"])
    _render_input_with_count(texts["btc.address"], field_keys["address"])
    st.caption(_address_validation_status("address", str(st.session_state.get(field_keys["address"], "")), texts))
    _render_copy_button(texts, str(st.session_state.get(field_keys["address"], "")).strip(), "copy_address")
    _render_input_with_count(texts["btc.address_uncompressed"], field_keys["address_uncompressed"])
    st.caption(
        _address_validation_status(
            "address_uncompressed",
            str(st.session_state.get(field_keys["address_uncompressed"], "")),
            texts,
        )
    )
    _render_copy_button(
        texts,
        str(st.session_state.get(field_keys["address_uncompressed"], "")).strip(),
        "copy_address_uncompressed",
    )
    _render_input_with_count(texts["btc.address_p2sh"], field_keys["address_p2sh"])
    st.caption(_address_validation_status("address_p2sh", str(st.session_state.get(field_keys["address_p2sh"], "")), texts))
    _render_copy_button(texts, str(st.session_state.get(field_keys["address_p2sh"], "")).strip(), "copy_address_p2sh")
    _render_input_with_count(texts["btc.address_p2wpkh"], field_keys["address_p2wpkh"])
    st.caption(_address_validation_status("address_p2wpkh", str(st.session_state.get(field_keys["address_p2wpkh"], "")), texts))
    _render_copy_button(texts, str(st.session_state.get(field_keys["address_p2wpkh"], "")).strip(), "copy_address_p2wpkh")
    _render_input_with_count(texts["btc.address_info"], field_keys["address_info"], disabled=True)
    _render_input_with_count(texts["btc.balance"], field_keys["balance"], disabled=True, show_count=False)
    _render_input_with_count(texts["btc.address_summary"], field_keys["address_summary"], disabled=True, show_count=False)
    _render_textarea_with_count(texts["btc.utxos"], field_keys["utxos_view"], height=180, disabled=True, show_count=False)
    _render_textarea_with_count(texts["btc.txs"], field_keys["txs_view"], height=220, disabled=True, show_count=False)
    private_dec_for_visual = st.session_state.get(field_keys["private_dec"], "").strip()
    if private_dec_for_visual.isdigit():
        _render_private_key_line_visualization(int(private_dec_for_visual), SECP256k1.order, texts)
    _render_pubkey_curve_visualization(st.session_state[field_keys["public_key_uncompressed"]], texts)
    qr_value = str(st.session_state.get(field_keys["address"], "")).strip()
    if not qr_value:
        qr_value = str(st.session_state.get(field_keys["address_uncompressed"], "")).strip()
    if qr_value:
        st.markdown(f"**{texts['btc.qr']}**")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={qr_value}")
    if st.session_state.btc_pubkey_curve_error:
        st.warning(st.session_state.btc_pubkey_curve_error)

    st.session_state.btc_last_inputs = {
        "private_dec": st.session_state[field_keys["private_dec"]],
        "private_hex": st.session_state[field_keys["private_hex"]],
        "private_wif": st.session_state[field_keys["private_wif"]],
        "private_wif_uncompressed": st.session_state[field_keys["private_wif_uncompressed"]],
        "seed_phrase": st.session_state[field_keys["seed_phrase"]],
        "public_key": st.session_state[field_keys["public_key"]],
        "public_key_uncompressed": st.session_state[field_keys["public_key_uncompressed"]],
        "ripemd160": st.session_state[field_keys["ripemd160"]],
        "ripemd160_uncompressed": st.session_state[field_keys["ripemd160_uncompressed"]],
        "address": st.session_state[field_keys["address"]],
        "address_uncompressed": st.session_state[field_keys["address_uncompressed"]],
        "address_p2sh": st.session_state[field_keys["address_p2sh"]],
        "address_p2wpkh": st.session_state[field_keys["address_p2wpkh"]],
    }
