"""Prueba rapida: que modelos y que endpoints de Open-Meteo devuelven historia de pronosticos."""
import requests, json
S = requests.Session()
loc = {"latitude": -34.822, "longitude": -58.536, "timezone": "America/Argentina/Buenos_Aires"}
modelos = ["gfs_seamless", "gfs_graphcast025", "ecmwf_ifs025", "ecmwf_ifs", "ecmwf_aifs025_single", "icon_seamless",
           "gem_seamless", "jma_seamless", "meteofrance_seamless", "ukmo_seamless", "kma_seamless", "cma_grapes_global",
           "bom_access_global", "best_match", "ncep_nbm_conus"]
for m in modelos:
    r = S.get("https://previous-runs-api.open-meteo.com/v1/forecast", params=dict(loc, hourly="temperature_2m_previous_day1,temperature_2m_previous_day3,temperature_2m_previous_day5",
              models=m, start_date="2026-08-20", end_date="2026-10-22"), timeout=60)
    try:
        h = r.json().get("hourly", {})
        res = {k: sum(v is not None for v in vs) for k, vs in h.items() if k != "time"}
        primero = {k: next((t for t, v in zip(h["time"], vs) if v is not None), None) for k, vs in h.items() if k != "time"}
    except Exception as e:
        res, primero = r.text[:200], None
    print("PREV", m, r.status_code, res, primero)
pruebas = {
    "ens_pasado": ("https://ensemble-api.open-meteo.com/v1/ensemble", dict(loc, hourly="temperature_2m", models="gfs025", start_date="2026-09-20", end_date="2026-09-21")),
    "ens_prev": ("https://ensemble-api.open-meteo.com/v1/ensemble", dict(loc, hourly="temperature_2m_previous_day1", models="gfs025", start_date="2026-10-10", end_date="2026-10-11")),
    "single_ens": ("https://single-runs-api.open-meteo.com/v1/forecast", dict(loc, hourly="temperature_2m", models="ecmwf_ifs025_ensemble", run="2026-10-10T00:00")),
    "single_ens2": ("https://ensemble-api.open-meteo.com/v1/ensemble", dict(loc, hourly="temperature_2m", models="gfs025", run="2026-10-10T00:00")),
    "single_det": ("https://single-runs-api.open-meteo.com/v1/forecast", dict(loc, hourly="temperature_2m", models="gfs025", run="2026-10-10T00:00")),
}
for n, (u, p) in pruebas.items():
    r = S.get(u, params=p, timeout=60)
    txt = r.text
    try:
        h = r.json().get("hourly", {})
        txt = f"claves={len(h)} ej={list(h)[:4]} n={[sum(v is not None for v in h[k]) for k in list(h)[1:3]]} t0={h.get('time',[None])[0]}"
    except Exception:
        txt = txt[:300]
    print("PRUEBA", n, r.status_code, txt)
