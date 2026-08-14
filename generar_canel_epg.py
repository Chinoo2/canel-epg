import requests
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime, timedelta, timezone

API = "https://catalog-service-cdn.cms.api.canela.tv/content/epg"

CANALES = {
    "crimen": "Crimen de Warner",
    "bodas-plus": "Bodas de Warner",
    "tu-discovery": "Tu Discovery",
    "aventura": "Aventura de Warner",
    "construcciones-asombrosas": "Construcciones Asombrosas",
    "vidas-extremas": "Vidas Extremas",
    "expedientes-sobrenaturales": "Expedientes Sobrenaturales"
}

ahora_utc = datetime.now(timezone.utc)

# Consultamos 24 horas desde las 00:00 UTC
dia = ahora_utc.replace(
    hour=0,
    minute=0,
    second=0,
    microsecond=0
)

inicio = dia
fin = dia + timedelta(days=1)

start = inicio.strftime("%Y-%m-%dT%H:%M:%SZ")
end = fin.strftime("%Y-%m-%dT%H:%M:%SZ")

params = {
    "start": start,
    "end": end,
    "reg": "us",
    "acl": "en",
    "dt": "web",
    "ipr": "true",
    "client": "canela-canela-web",
    "pf": "main",
    "locale": "es-uy"
}

print("Consultando EPG de Canela...")
print(f"Desde: {start}")
print(f"Hasta: {end}")

try:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.canela.tv",
        "Referer": "https://www.canela.tv/",
    }

    r = requests.get(
        API,
        params=params,
        headers=headers,
        timeout=30
    )

    print(f"HTTP: {r.status_code}")

    r.raise_for_status()

    data = r.json()

except Exception as e:
    print(f"ERROR consultando Canela: {e}")
    raise


tv = Element(
    "tv",
    generator_info_name="Canela EPG"
)

programas_guardados = set()
canales_encontrados = set()


for canal in data.get("data", []):

    airings = canal.get("airing", [])

    if not airings:
        continue

    primer_airing = airings[0]

    ch_data = primer_airing.get("ch", {})
    canal_id = ch_data.get("cs")

    if canal_id not in CANALES:
        continue

    nombre = CANALES[canal_id]

    if canal_id not in canales_encontrados:

        print(
            f"Canal encontrado: {nombre} ({canal_id})"
        )

        ch = SubElement(
            tv,
            "channel",
            id=canal_id
        )

        dn = SubElement(
            ch,
            "display-name"
        )

        dn.text = nombre

        canales_encontrados.add(canal_id)


    for evento in airings:

        inicio_str = evento.get("sc_st_dt")
        fin_str = evento.get("sc_ed_dt")

        if not inicio_str or not fin_str:
            continue

        try:

            fecha_inicio = datetime.fromisoformat(
                inicio_str.replace("Z", "+00:00")
            )

            fecha_fin = datetime.fromisoformat(
                fin_str.replace("Z", "+00:00")
            )

        except ValueError:
            continue


        if fecha_fin < ahora_utc:
            continue


        clave = (
            canal_id,
            inicio_str,
            fin_str
        )

        if clave in programas_guardados:
            continue

        programas_guardados.add(clave)


        pgm = evento.get("pgm", {})


        # ==========================================
        # TÍTULO
        # ==========================================

        nombres = pgm.get("lon", [])

        titulo_texto = "Sin información"

        for item in nombres:

            if item.get("lang") == "es-MX":

                titulo_texto = item.get(
                    "n",
                    "Sin información"
                )

                break


        if titulo_texto == "Sin información" and nombres:

            titulo_texto = nombres[0].get(
                "n",
                "Sin información"
            )


        # ==========================================
        # DESCRIPCIÓN
        # ==========================================

        descripciones = pgm.get("lod", [])

        descripcion_texto = ""

        for item in descripciones:

            if item.get("lang") == "es-MX":

                descripcion_texto = item.get(
                    "n",
                    ""
                )

                break


        if not descripcion_texto and descripciones:

            descripcion_texto = descripciones[0].get(
                "n",
                ""
            )


        # ==========================================
        # PROGRAMA XMLTV
        # ==========================================

        prog = SubElement(
            tv,
            "programme",
            channel=canal_id,
            start=fecha_inicio.strftime(
                "%Y%m%d%H%M%S +0000"
            ),
            stop=fecha_fin.strftime(
                "%Y%m%d%H%M%S +0000"
            )
        )


        title = SubElement(
            prog,
            "title",
            lang="es"
        )

        title.text = titulo_texto


        desc = SubElement(
            prog,
            "desc",
            lang="es"
        )

        desc.text = descripcion_texto


# ==========================================
# GUARDAR XML
# ==========================================

ElementTree(tv).write(
    "canel_epg.xml",
    encoding="utf-8",
    xml_declaration=True
)


print()
print("====================================")
print("Canel EPG generado correctamente")
print("Archivo: canel_epg.xml")
print(
    f"Canales: {len(canales_encontrados)}/7"
)
print(
    f"Programas: {len(programas_guardados)}"
)
print("====================================")
