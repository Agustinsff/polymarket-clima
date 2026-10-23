import json, re, sys, requests
sys.path.insert(0, ".")
from estaciones import estacion_de_evento, TZ
S = requests.Session()
evs = []
for off in range(0, 2000, 100):
    r = S.get("https://gamma-api.polymarket.com/events", params={"tag_slug": "daily-temperature", "closed": "false", "limit": 100, "offset": off}, timeout=30).json()
    evs += r
    if len(r) < 100:
        break
out = {"n_eventos": len(evs), "eventos": []}
for e in evs:
    m = re.match(r"^(highest|lowest)-temperature-in-(.+)-on-([a-z]+)-(\d+)-(\d{4})$", e.get("slug", ""))
    out["eventos"].append({"slug": e.get("slug"), "regex": bool(m), "ciudad_en_TZ": bool(m and m.group(2) in TZ),
                           "icao": estacion_de_evento(e), "resolutionSource": e.get("resolutionSource"),
                           "tags": [t.get("slug") for t in e.get("tags") or []], "endDate": e.get("endDate")})
json.dump(out, open("diag/gamma_eventos.json", "w"), indent=1, ensure_ascii=False)
# un evento completo de ejemplo de los que no pasan el filtro, y otro por busqueda de texto
malos = [e for e in evs if not re.match(r"^(highest|lowest)-temperature-in-", e.get("slug", "")) or not estacion_de_evento(e)]
json.dump(malos[:2], open("diag/gamma_ejemplo_malo.json", "w"), indent=1, ensure_ascii=False)
r = S.get("https://gamma-api.polymarket.com/public-search", params={"q": "highest temperature wuhan", "limit_per_type": 5}, timeout=30)
open("diag/busqueda.json", "w").write(r.text[:200000])
print(len(evs), "eventos;", len(malos), "no pasan")
