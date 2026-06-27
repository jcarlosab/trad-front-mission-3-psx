#!/usr/bin/env python3
import csv
import os
import sys
import re

CONTROL_CODES = {
    "[NL]": 0x0A,
    "[NEWLINE]": 0x16,
    "[CMD]": 0x19,
    "[NAME_START]": 0x0B,
    "[NAME_END]": 0x01,
    "[ITEM_START]": 0x1D,
    "[ITEM_END]": 0x1E,
}

# Reverse mapping
BYTE_TO_CONTROL = {v: k for k, v in CONTROL_CODES.items()}


def csv_text_to_bytes(text):
    """Convierte texto del CSV (con marcadores [NL], etc.) a bytes Latin-1."""
    parts = []
    i = 0
    while i < len(text):
        if text[i] == '[':
            end = text.find(']', i)
            if end == -1:
                parts.append(text[i].encode('latin-1'))
                i += 1
                continue
            token = text[i:end+1]
            if token in CONTROL_CODES:
                parts.append(bytes([CONTROL_CODES[token]]))
                i = end + 1
                continue
            # [0xNN] - raw byte
            m = re.match(r'\[0x([0-9A-Fa-f]{2})\]', token)
            if m:
                parts.append(bytes([int(m.group(1), 16)]))
                i = end + 1
                continue
            # Unknown token, keep as-is
            parts.append(token.encode('latin-1', errors='replace'))
            i = end + 1
        else:
            char = text[i]
            try:
                parts.append(char.encode('latin-1'))
            except UnicodeEncodeError:
                parts.append(char.encode('ascii', errors='replace'))
            i += 1
    return b''.join(parts)


def reinsert_into_file(filepath, entries, dry_run=False):
    """Reinserta textos en un archivo binario."""
    if not os.path.exists(filepath):
        print(f"  ERROR: {filepath} no encontrado")
        return 0, 0

    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    modified = 0
    errors = 0

    for entry in entries:
        text_to_use = entry.get('traduccion', '').strip() or entry.get('traduccion_ia', '').strip()
        if not text_to_use:
            continue

        offset = int(entry['offset'], 16) if isinstance(entry['offset'], str) else entry['offset']
        original_len = int(entry.get('longitud_original', 0))

        new_bytes = csv_text_to_bytes(text_to_use)

        if len(new_bytes) > original_len:
            print(f"  AVISO: offset 0x{offset:06X}: texto muy largo "
                  f"({len(new_bytes)} > {original_len}), se truncara")
            new_bytes = new_bytes[:original_len]
        elif len(new_bytes) < original_len:
            new_bytes = new_bytes + b'\x00' * (original_len - len(new_bytes))

        if offset + original_len > len(data):
            print(f"  ERROR: offset 0x{offset:06X} fuera de rango")
            errors += 1
            continue

        old_bytes = data[offset:offset + original_len]
        if old_bytes == new_bytes:
            continue

        if not dry_run:
            data[offset:offset + original_len] = new_bytes
        modified += 1

        if modified <= 5 or dry_run:
            old_preview = old_bytes.decode('latin-1', errors='replace')
            new_preview = new_bytes.decode('latin-1', errors='replace')
            print(f"  {'[DRY]' if dry_run else '[OK]'} 0x{offset:06X}: "
                  f"'{old_preview[:60]}' -> '{new_preview[:60]}'")

    if not dry_run and modified > 0:
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"  Archivo guardado: {modified} cambios")

    return modified, errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Reinserta textos traducidos a archivos BIN")
    parser.add_argument('csv', help="Archivo CSV con traducciones")
    parser.add_argument('--dry-run', action='store_true', help="Solo mostrar cambios sin escribir")
    parser.add_argument('--dir', default=None, help="Directorio del juego extraido (por defecto: ../juego_extraido)")
    args = parser.parse_args()

    if args.dir:
        extracted_dir = args.dir
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(script_dir))
        extracted_dir = os.path.join(base_dir, "juego_extraido")

    if not os.path.isdir(extracted_dir):
        print(f"ERROR: Directorio {extracted_dir} no encontrado")
        sys.exit(1)

    with open(args.csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"CSV cargado: {len(rows)} entradas")

    # Agrupar por archivo
    files = {}
    for row in rows:
        archivo = row.get('archivo', '')
        if archivo not in files:
            files[archivo] = []
        files[archivo].append(row)

    total_modified = 0
    total_errors = 0

    for archivo, file_entries in sorted(files.items()):
        filepath = os.path.join(extracted_dir, archivo)
        print(f"\n--- {archivo} ({len(file_entries)} entradas) ---")
        m, e = reinsert_into_file(filepath, file_entries, dry_run=args.dry_run)
        total_modified += m
        total_errors += e

    print(f"\n{'='*50}")
    print(f"Total: {total_modified} textos insertados, {total_errors} errores")
    if args.dry_run:
        print("(Modo dry-run: no se escribieron cambios)")


if __name__ == '__main__':
    main()
