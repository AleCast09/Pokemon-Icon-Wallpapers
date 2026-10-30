#!/usr/bin/env python3
"""
Descarga/copia las imagenes de las cartas del set C1 (Dual Fusion -
la expansion nueva, salio a fines de octubre 2026) de Pokemon TCG
Pocket, usando la base de datos publica que usa tu propia app
(leanny.github.io/pocket_tcg_resources) para saber exactamente que
cartas son de C1, y usando el cache local de PTCGPB-ALE cuando ya
esta descargado ahi.

Este script se ejecuta EN TU COMPUTADORA (no en la nube), asi que
necesita que edites la variable RUTA_PTCGPB de abajo si tu carpeta
no esta en C:\\POKEMON\\PTCGPB-ALE.

Uso:
    python descargar_c1.py

Requisitos (instalar una vez):
    pip install requests pillow
"""

import io
import sys
import time
from pathlib import Path

import requests
from PIL import Image

# --- Ajusta esto si tu carpeta de PTCGPB-ALE esta en otro lado ---
RUTA_PTCGPB = Path(r"C:\POKEMON\PTCGPB-ALE")
CACHE_LOCAL = RUTA_PTCGPB / "Helper" / "CardImageCache"

EXPANSION_ID = "C1"
CARDMAP_URL = "https://leanny.github.io/pocket_tcg_resources/data/cardmap.json"
IMAGE_PREFIX = "https://leanny.github.io/pocket_tcg_resources/img/M/US/"

CARPETA_SALIDA = Path(f"cartas_{EXPANSION_ID}")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def obtener_cartas_del_set() -> list[dict]:
    print(f"Descargando el mapa de cartas desde {CARDMAP_URL} ...")
    resp = requests.get(CARDMAP_URL, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    cardmap = resp.json()

    cartas = []
    for card_id, info in cardmap.items():
        if info.get("ExpansionID") == EXPANSION_ID:
            cartas.append(
                {
                    "card_id": card_id,
                    "numero": info.get("CollectionNumber"),
                    "illustration_id": info.get("IllustrationID"),
                }
            )

    cartas.sort(key=lambda c: (c["numero"] is None, c["numero"]))
    return cartas


def conseguir_imagen(illustration_id: str) -> bytes:
    # 1) Primero busca en el cache local de tu app (mas rapido, sin
    #    usar internet).
    for ext in (".png", ".webp", ".jpg"):
        ruta_local = CACHE_LOCAL / f"{illustration_id}{ext}"
        if ruta_local.exists():
            return ruta_local.read_bytes()

    # 2) Si no esta en el cache, la baja de la base publica.
    for ext in (".png", ".webp"):
        url = f"{IMAGE_PREFIX}{illustration_id}{ext}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.ok:
            return resp.content

    raise FileNotFoundError(f"No se encontro la imagen para {illustration_id}")


def guardar_como_png(nombre_base: str, contenido: bytes, carpeta_salida: Path):
    imagen = Image.open(io.BytesIO(contenido)).convert("RGBA")
    ruta_salida = carpeta_salida / f"{nombre_base}.png"
    imagen.save(ruta_salida, "PNG")
    return ruta_salida


def main():
    if not CACHE_LOCAL.exists():
        print(f"AVISO: no encontre la carpeta de cache en {CACHE_LOCAL}")
        print("Revisa que RUTA_PTCGPB apunte a tu carpeta de PTCGPB-ALE.")

    try:
        cartas = obtener_cartas_del_set()
    except Exception as e:
        print(f"No se pudo bajar/leer cardmap.json: {e}")
        sys.exit(1)

    print(f"Se encontraron {len(cartas)} cartas con ExpansionID = {EXPANSION_ID} (Dual Fusion).")

    if not cartas:
        print(
            f"No hay ninguna carta con ExpansionID = '{EXPANSION_ID}' en la base "
            "publica todavia. Probemos mas tarde, puede que la base comunitaria "
            "no se haya actualizado aun del todo."
        )
        sys.exit(1)

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    ok, fallidas = 0, []
    for carta in cartas:
        illustration_id = carta["illustration_id"]
        numero = carta["numero"]
        if not illustration_id:
            fallidas.append(carta["card_id"])
            continue
        try:
            contenido = conseguir_imagen(illustration_id)
            ruta = guardar_como_png(illustration_id, contenido, CARPETA_SALIDA)
            print(f"[{numero:03}] Guardada: {ruta.name}")
            ok += 1
        except Exception as e:
            print(f"[{numero}] Error con {illustration_id}: {e}")
            fallidas.append(illustration_id)
        time.sleep(0.05)

    print(f"\nListo. {ok} imagenes guardadas en '{CARPETA_SALIDA}/'.")
    if fallidas:
        print(f"{len(fallidas)} fallaron:")
        for f in fallidas:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
