import hashlib
import html

import streamlit as st
import requests


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

def _lookup_transactions(address: str) -> list[dict]:
    url = f"https://blockstream.info/api/address/{address}/txs"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("invalid tx payload")
    return [tx for tx in payload if isinstance(tx, dict)]

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
                f"{texts['btc.curve.on_curve']}: {'yes' if on_curve else 'no'}",
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

def _format_transactions_for_view(txs: list[dict], address: str) -> str:
    lines: list[str] = []
    for i, tx in enumerate(txs, start=1):
        txid = str(tx.get("txid", ""))
        fee = tx.get("fee")
        status = tx.get("status", {}) if isinstance(tx.get("status"), dict) else {}
        confirmed = bool(status.get("confirmed", False))
        block_height = status.get("block_height")
        received_sats, sent_sats = _tx_amounts_for_address(tx, address)
        net_sats = received_sats - sent_sats
        lines.append(f"{i}. txid: {txid}")
        lines.append(f"   confirmed: {'yes' if confirmed else 'no'}")
        if block_height is not None:
            lines.append(f"   block: {block_height}")
        lines.append(f"   received: {received_sats} sats ({received_sats / 100_000_000:.8f} BTC)")
        lines.append(f"   sent: {sent_sats} sats ({sent_sats / 100_000_000:.8f} BTC)")
        lines.append(f"   net: {net_sats:+d} sats ({net_sats / 100_000_000:+.8f} BTC)")
        if fee is not None:
            lines.append(f"   fee: {fee} sats")
        lines.append("")
    return "\n".join(lines).strip()

def render_btc_keys_component(texts: dict[str, str]) -> None:
    try:
        from ecdsa import SECP256k1, VerifyingKey
    except ModuleNotFoundError:
        st.error(texts["btc.error.ecdsa"])
        return

    field_keys = {
        "private_dec": "btc_private_dec",
        "private_hex": "btc_private_hex",
        "public_key": "btc_public_key_compressed",
        "public_key_uncompressed": "btc_public_key_uncompressed",
        "ripemd160": "btc_ripemd160",
        "ripemd160_uncompressed": "btc_ripemd160_uncompressed",
        "address": "btc_address",
        "address_uncompressed": "btc_address_uncompressed",
        "address_p2sh": "btc_address_p2sh",
        "address_p2wpkh": "btc_address_p2wpkh",
        "balance": "btc_balance",
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

    current_inputs = {
        "private_dec": st.session_state[field_keys["private_dec"]],
        "private_hex": st.session_state[field_keys["private_hex"]],
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

    if changed_field is not None:
        for field_name in current_inputs.keys():
            if field_name == changed_field:
                continue
            st.session_state[field_keys[field_name]] = ""
        st.session_state[field_keys["private_dec_norm"]] = ""
        st.session_state[field_keys["private_hex_norm"]] = ""
        st.session_state[field_keys["balance"]] = ""
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
                    if changed_field == "address":
                        hash160 = _hash160_from_p2pkh(raw_value)
                    else:
                        hash160_uncompressed = _hash160_from_p2pkh(raw_value)
                    try:
                        found_pubkey_hex = _lookup_pubkey_by_address(raw_value)
                    except requests.RequestException:
                        found_pubkey_hex = None
                    if found_pubkey_hex:
                        found_pubkey = bytes.fromhex(found_pubkey_hex)
                        if len(found_pubkey) == 33 and found_pubkey[0] in (2, 3):
                            pubkey_compressed = found_pubkey
                            pubkey_uncompressed = _decompress_compressed_pubkey(found_pubkey)
                        elif len(found_pubkey) == 65 and found_pubkey[0] == 4:
                            pubkey_uncompressed = found_pubkey
                            pubkey_compressed = _compress_uncompressed_pubkey(found_pubkey)
                elif changed_field == "address_p2wpkh":
                    hash160 = _hash160_from_p2wpkh(raw_value)
                elif changed_field == "address_p2sh":
                    _ = _hash160_from_p2sh_p2wpkh(raw_value)
                else:
                    raise ValueError("unsupported field")
            except ValueError:
                if changed_field in {"public_key", "public_key_uncompressed"}:
                    st.session_state.btc_pubkey_curve_error = texts["btc.error.pubkey_not_on_curve"]
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
                if txs:
                    st.session_state[field_keys["txs_view"]] = _format_transactions_for_view(txs, target_address)
                else:
                    st.session_state[field_keys["txs_view"]] = texts["btc.txs.empty"]
            except (requests.RequestException, ValueError):
                st.session_state[field_keys["txs_view"]] = texts["btc.txs.unavailable"]
        else:
            st.session_state[field_keys["balance"]] = ""
            st.session_state[field_keys["txs_view"]] = ""

    st.text_input(texts["btc.private_dec"], key=field_keys["private_dec"])
    st.text_input(texts["btc.private_hex"], key=field_keys["private_hex"])
    st.text_input(texts["btc.private_dec_norm"], key=field_keys["private_dec_norm"], disabled=True)
    st.text_input(texts["btc.private_hex_norm"], key=field_keys["private_hex_norm"], disabled=True)
    st.text_input(texts["btc.public_key"], key=field_keys["public_key"])
    st.text_input(texts["btc.public_key_uncompressed"], key=field_keys["public_key_uncompressed"])
    pubkey_uncompressed_value = st.session_state.get(field_keys["public_key_uncompressed"], "").strip()
    if pubkey_uncompressed_value:
        st.markdown(
            (
                "<div style='font-size:0.72rem; line-height:1.2; color:#9cb09c; "
                "word-break:break-all; overflow-wrap:anywhere; user-select:text;'>"
                f"{html.escape(pubkey_uncompressed_value)}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    st.text_input(texts["btc.ripemd160"], key=field_keys["ripemd160"])
    st.text_input(texts["btc.ripemd160_uncompressed"], key=field_keys["ripemd160_uncompressed"])
    st.text_input(texts["btc.address"], key=field_keys["address"])
    st.text_input(texts["btc.address_uncompressed"], key=field_keys["address_uncompressed"])
    st.text_input(texts["btc.address_p2sh"], key=field_keys["address_p2sh"])
    st.text_input(texts["btc.address_p2wpkh"], key=field_keys["address_p2wpkh"])
    st.text_input(texts["btc.balance"], key=field_keys["balance"], disabled=True)
    st.text_area(texts["btc.txs"], key=field_keys["txs_view"], height=220, disabled=True)
    _render_pubkey_curve_visualization(st.session_state[field_keys["public_key_uncompressed"]], texts)
    if st.session_state.btc_pubkey_curve_error:
        st.warning(st.session_state.btc_pubkey_curve_error)

    st.session_state.btc_last_inputs = {
        "private_dec": st.session_state[field_keys["private_dec"]],
        "private_hex": st.session_state[field_keys["private_hex"]],
        "public_key": st.session_state[field_keys["public_key"]],
        "public_key_uncompressed": st.session_state[field_keys["public_key_uncompressed"]],
        "ripemd160": st.session_state[field_keys["ripemd160"]],
        "ripemd160_uncompressed": st.session_state[field_keys["ripemd160_uncompressed"]],
        "address": st.session_state[field_keys["address"]],
        "address_uncompressed": st.session_state[field_keys["address_uncompressed"]],
        "address_p2sh": st.session_state[field_keys["address_p2sh"]],
        "address_p2wpkh": st.session_state[field_keys["address_p2wpkh"]],
    }
