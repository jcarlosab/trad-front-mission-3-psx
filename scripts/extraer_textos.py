import csv
import os
import re
import struct

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
EXTRACTED_DIR = os.path.join(PROJECT_DIR, "juego_extraido")
OUTPUT_DIR = os.path.join(BASE_DIR, "textos_extraidos")

CONTROL_CODES = {
    0x0A: "[NL]",
    0x16: "[NEWLINE]",
    0x19: "[CMD]",
    0x0B: "[NAME_START]",
    0x01: "[NAME_END]",
    0x1D: "[ITEM_START]",
    0x1E: "[ITEM_END]",
}


def is_printable_latin1(byte):
    return (0x20 <= byte <= 0x7E) or (0xA0 <= byte <= 0xFF)


def decode_text_block(data, start, end):
    result = []
    i = start
    while i < end:
        byte = data[i]
        if is_printable_latin1(byte):
            j = i
            while j < end and is_printable_latin1(data[j]):
                j += 1
            result.append(data[i:j].decode("latin-1"))
            i = j
        elif byte == 0x00:
            i += 1
        elif byte in CONTROL_CODES:
            result.append(CONTROL_CODES[byte])
            i += 1
        else:
            result.append(f"[0x{byte:02X}]")
            i += 1
    return "".join(result)


def is_meaningful_text(text):
    clean = text
    for code in CONTROL_CODES.values():
        clean = clean.replace(code, "")
    clean = clean.replace("[0x", "").replace("]", "")
    clean = clean.strip()

    if len(clean) < 2:
        return False
    if clean.startswith("F.M.III"):
        return False
    if re.match(r'^[0-9+\-*/=()#@!$%^&|~\s]+$', clean):
        return False
    if re.match(r'^[wfgUDe3"+]+$', clean):
        return False

    has_letters = bool(re.search(r'[a-zA-Z]', clean))
    return has_letters


def extract_stgdata():
    path = os.path.join(EXTRACTED_DIR, "STGDATA.BIN")
    with open(path, "rb") as f:
        data = f.read()

    entries = []
    entry_id = 0

    i = 0
    while i < len(data):
        while i < len(data) and data[i] == 0x00:
            i += 1

        if i >= len(data):
            break

        block_start = i
        has_text = False

        while i < len(data) and data[i] != 0x00:
            if is_printable_latin1(data[i]):
                has_text = True
            i += 1

        if not has_text:
            continue

        block_end = i
        block_data = data[block_start:block_end]

        parts = []
        j = 0
        while j < len(block_data):
            byte = block_data[j]
            if is_printable_latin1(byte):
                k = j
                while k < len(block_data) and is_printable_latin1(block_data[k]):
                    k += 1
                parts.append(block_data[j:k].decode("latin-1"))
                j = k
            elif byte == 0x0A:
                parts.append("[NL]")
                j += 1
            elif byte == 0x16:
                parts.append("[NEWLINE]")
                j += 1
            elif byte == 0x0B:
                parts.append("[NAME_START]")
                j += 1
            elif byte == 0x01:
                parts.append("[NAME_END]")
                j += 1
            elif byte == 0x1D:
                parts.append("[ITEM_START]")
                j += 1
            elif byte == 0x1E:
                parts.append("[ITEM_END]")
                j += 1
            elif byte == 0x19:
                parts.append("[CMD]")
                j += 1
            else:
                parts.append(f"[0x{byte:02X}]")
                j += 1

        text = "".join(parts)

        clean = text
        for code in ["[NL]", "[NEWLINE]", "[NAME_START]", "[NAME_END]", "[ITEM_START]", "[ITEM_END]", "[CMD]"]:
            clean = clean.replace(code, "")
        clean = re.sub(r'\[0x[0-9A-F]{2}\]', '', clean)
        clean = clean.strip()

        if len(clean) < 4:
            continue

        lowers = set(c for c in clean if c.islower())
        if len(lowers) < 2:
            continue

        vowels = set(c for c in clean if c in 'aeiou')
        if not vowels:
            continue

        if clean.startswith("F.M.III"):
            continue

        if re.match(r'^[0-9+\-*/=()#@!$%^&|~\s]+$', clean):
            continue

        if re.match(r'^[a-z]{1,3}\([a-z]{1,3}$', clean):
            continue

        if re.match(r'^[a-z]{3,}\([a-z]{3,}$', clean):
            continue

        if len(clean) < 15:
            has_space = ' ' in clean
            if not has_space:
                continue

        codes_count = len(re.findall(r'\[0x[0-9A-F]{2}\]', text))
        if codes_count > 5:
            continue

        clean_len = len(re.sub(r'\[0x[0-9A-F]{2}\]', '', text))
        for code in ["[NL]", "[NEWLINE]", "[NAME_START]", "[NAME_END]", "[ITEM_START]", "[ITEM_END]", "[CMD]"]:
            clean_len -= len(code) * text.count(code)
        if clean_len < 4:
            continue

        entry_id += 1
        text_type = "dialogo"
        if "[CMD]" in text:
            text_type = "sistema"
        elif any(w in clean.lower() for w in ["winning condition", "losing condition", "destroy all", "arrive at"]):
            text_type = "mision"
        elif any(w in clean.lower() for w in ["select", "confirm", "cancel", "save", "load", "option", "config", "equip", "shop", "factory", "mail", "network"]):
            text_type = "menu"

        entries.append({
            "id": entry_id,
            "archivo": "STGDATA.BIN",
            "offset": f"0x{block_start:06X}",
            "offset_decimal": block_start,
            "tipo": text_type,
            "longitud_original": block_end - block_start,
            "texto_original": text,
            "traduccion_ia": "",
            "traduccion": "",
        })

    return entries


def extract_ovl_files():
    ovl_dir = os.path.join(EXTRACTED_DIR, "OVL")
    entries = []
    entry_id = 100000

    target_files = ["ZMAIL.BIN", "ZRES.BIN", "ZTIT.BIN", "NEND.BIN", "ZNET.BIN", "ZSTUP.BIN", "YSL.BIN", "ZNAM.BIN", "ZNMAP.BIN", "SENT.BIN", "YAREA.BIN"]

    for filename in target_files:
        path = os.path.join(ovl_dir, filename)
        if not os.path.exists(path):
            continue

        with open(path, "rb") as f:
            data = f.read()

        strings = re.finditer(rb'[\x20-\x7E\xA0-\xFF]{4,}', data)
        for match in strings:
            text = match.group().decode("latin-1")
            offset = match.start()

            if not is_meaningful_text(text):
                continue

            if text.startswith("MWo1") or text.startswith("F.M.III"):
                continue

            entry_id += 1
            text_type = "menu"
            if filename == "NEND.BIN":
                text_type = "creditos"
            elif filename == "ZMAIL.BIN":
                text_type = "correo"
            elif filename == "ZRES.BIN":
                text_type = "resultados"

            entries.append({
                "id": entry_id,
                "archivo": f"OVL/{filename}",
                "offset": f"0x{offset:06X}",
                "offset_decimal": offset,
                "tipo": text_type,
                "longitud_original": len(text),
                "texto_original": text,
                "traduccion_ia": "",
                "traduccion": "",
            })

    return entries


def extract_slus():
    path = os.path.join(EXTRACTED_DIR, "SLUS_010.11")
    with open(path, "rb") as f:
        data = f.read()

    entries = []
    entry_id = 200000

    keywords = [b"pilot", b"attack", b"weapon", b"enemy", b"target", b"battle",
                b"damage", b"skill", b"level", b"save", b"load", b"body",
                b"legs", b"left", b"right", b"shield", b"missile", b"rifle",
                b"Drake", b"Alisa", b"Network", b"EXP"]

    found_offsets = set()
    for kw in keywords:
        start = 0
        while True:
            idx = data.find(kw, start)
            if idx == -1:
                break
            block_start = idx
            while block_start > 0 and is_printable_latin1(data[block_start - 1]):
                block_start -= 1
            block_end = idx + len(kw)
            while block_end < len(data) and is_printable_latin1(data[block_end]):
                block_end += 1

            text = data[block_start:block_end].decode("latin-1", errors="replace")
            if block_start not in found_offsets and len(text) >= 4 and is_meaningful_text(text):
                found_offsets.add(block_start)
                entry_id += 1
                entries.append({
                    "id": entry_id,
                    "archivo": "SLUS_010.11",
                    "offset": f"0x{block_start:06X}",
                    "offset_decimal": block_start,
                    "tipo": "ejecutable",
                    "longitud_original": block_end - block_start,
                    "texto_original": text,
                    "traduccion_ia": "",
                    "traduccion": "",
                })
            start = idx + 1

    entries.sort(key=lambda x: x["offset_decimal"])
    return entries


def save_csv(entries, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "archivo", "offset", "tipo", "longitud_original",
            "texto_original", "traduccion_ia", "traduccion"
        ])
        writer.writeheader()
        for entry in entries:
            row = {k: v for k, v in entry.items() if k != "offset_decimal"}
            writer.writerow(row)

    return path


def main():
    print("Extrayendo textos de STGDATA.BIN...")
    stg_entries = extract_stgdata()
    path = save_csv(stg_entries, "stgdata_textos.csv")
    print(f"  {len(stg_entries)} textos extraidos -> {path}")

    print("Extrayendo textos de archivos OVL...")
    ovl_entries = extract_ovl_files()
    path = save_csv(ovl_entries, "ovl_textos.csv")
    print(f"  {len(ovl_entries)} textos extraidos -> {path}")

    print("Extrayendo textos de SLUS_010.11...")
    slus_entries = extract_slus()
    path = save_csv(slus_entries, "slus_textos.csv")
    print(f"  {len(slus_entries)} textos extraidos -> {path}")

    all_entries = stg_entries + ovl_entries + slus_entries
    path = save_csv(all_entries, "todos_los_textos.csv")
    print(f"\nTotal: {len(all_entries)} textos -> {path}")

    tipos = {}
    for e in all_entries:
        tipos[e["tipo"]] = tipos.get(e["tipo"], 0) + 1
    print("\nPor tipo:")
    for tipo, count in sorted(tipos.items(), key=lambda x: -x[1]):
        print(f"  {tipo}: {count}")


if __name__ == "__main__":
    main()
