"""
Baja las fuentes publicas que resuelven (o adelantan) los mercados de clima lentos, para compararlas con el precio.
Corre en GitHub Actions (el contenedor no llega a estos sitios). Guarda cada archivo tal cual en otros_clima/datos/fuentes/.

Uso: python otros_clima/fuentes.py
"""

import os
from datetime import date

import requests

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos", "fuentes")
HOY = date.today()
IEM = ("https://mesonet.agron.iastate.edu/cgi-bin/request/daily.py?network={net}&stations={st}"
       "&year1=2024&month1=1&day1=1&year2={y}&month2={m}&day2={d}&var=precip_in&var=snow_in&format=csv")
FUENTES = {
    # resuelve la anomalia global del mes
    "gistemp_glb.csv": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    # ERA5 diario (Climate Pulse de Copernicus), ~2 dias de demora: adelanta a GISTEMP
    "era5_diario_2t.csv": "https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv",
    "noaa_global_mensual.csv": "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/"
                               "globe/land_ocean/1/0/1850-2026/data.csv",
    # hielo del Artico, diario
    "nsidc_norte_diario.csv": "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v3.0.csv",
    # lluvia y nieve diaria de las estaciones de los mercados de precipitacion
    "iem_nyc.csv": IEM.format(net="NY_ASOS", st="NYC", y=HOY.year, m=HOY.month, d=HOY.day),
    "iem_sea.csv": IEM.format(net="WA_ASOS", st="SEA", y=HOY.year, m=HOY.month, d=HOY.day),
    # tornados preliminares del SPC
    "spc_torn_2026.csv": "https://www.spc.noaa.gov/climo/reports/2026_torn_prelim.csv",
}


def main():
    os.makedirs(CARPETA, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = "polymarket-clima-otros/1.0 (investigacion personal)"
    for nombre, url in FUENTES.items():
        try:
            r = s.get(url, timeout=90)
            print(nombre, r.status_code, len(r.content), flush=True)
            if r.ok:
                with open(os.path.join(CARPETA, nombre), "wb") as f:
                    f.write(r.content)
        except Exception as ex:
            print(nombre, "error", ex, flush=True)


if __name__ == "__main__":
    main()
