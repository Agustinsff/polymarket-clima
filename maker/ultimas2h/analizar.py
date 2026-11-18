"""Medicion "ultimas 2 horas" (reglas en maker/ultimas2h/REGLA.md). Solo lectura de datos guardados del medidor maker.
Uso: python maker/ultimas2h/analizar.py <carpeta con fotos_*.csv.gz y llenados.csv de la rama medidor-maker>
Escribe maker/ultimas2h/informe.md."""
import glob
import os
import sys

import numpy as np
import pandas as pd

C = sys.argv[1]
AQUI = os.path.dirname(os.path.abspath(__file__))
D = 2                      # orden a 2 c del medio
TAM = 100
# periodos con llenados validos (la data-api v1 dejo de devolver operaciones 2-nov 22:25Z -> 7-nov 23:20Z)
VALIDO = [(pd.Timestamp("2026-10-26", tz="UTC"), pd.Timestamp("2026-11-02 22:25", tz="UTC")),
          (pd.Timestamp("2026-11-07 23:20", tz="UTC"), pd.Timestamp("2026-11-10", tz="UTC"))]
COLS = ["ts", "grupo", "serie", "evento", "caja", "cid", "hora_local", "horas_hasta_fin", "pozo", "spread_max", "tam_min",
        "medio", "bid", "ask", "comp", f"nbid_{D}c", f"nask_{D}c"]

fotos = pd.concat(pd.read_csv(f, sep=";", usecols=COLS) for f in sorted(glob.glob(os.path.join(C, "fotos_*.csv.gz"))))
fotos = fotos[fotos.grupo == "clima"].copy()
t = pd.to_datetime(fotos.ts, unit="s", utc=True)
fotos["valido"] = np.logical_or.reduce([(t >= a) & (t < b) for a, b in VALIDO])
# diferencia horaria de la ciudad (hora local de la foto - hora UTC), y horas hasta la medianoche local del dia del
# evento: Polymarket pone el fin del evento a las 12:00 UTC del dia; la medianoche local es fin + 12 - offset
fotos["off"] = ((fotos.hora_local - t.dt.hour + t.dt.minute / 60 + 12) % 24) - 12
fotos["off"] = fotos.off.round()
fotos["h_rest"] = fotos.horas_hasta_fin + 12 - fotos.off
fotos["dia_ev"] = fotos.evento.str.extract(r"on-([a-z]+-\d+-\d{4})$")[0]


def punt(v, s):
    return np.where((s >= 0) & (s < v) & (v > 0), ((v - s) / np.where(v > 0, v, 1)) ** 2, 0.0)


tam = np.maximum(TAM, fotos.tam_min)
v = fotos.spread_max / 100 if fotos.spread_max.max() > 1 else fotos.spread_max
nuestro = np.minimum(punt(v, fotos.medio - fotos[f"nbid_{D}c"]), punt(v, fotos[f"nask_{D}c"] - fotos.medio)) * tam
comp = pd.to_numeric(fotos.comp, errors="coerce").fillna(0)
fotos["pes"] = np.where((fotos.pozo > 0) & (nuestro > 0), fotos.pozo * nuestro / (2 * nuestro + comp), 0.0)  # US$/dia
fotos["cumple"] = ((fotos.ask - fotos.bid) <= 0.05 + 1e-9) & fotos.medio.between(0.03, 0.97) & (fotos.pozo > 0)
fotos["ventana"] = np.select([(fotos.h_rest > 0) & (fotos.h_rest <= 2), fotos.horas_hasta_fin >= 24],
                             ["fin del dia (ultimas 2 h)", "como hoy (>24 h al fin)"], "otro")

# movimiento del medio en 1 hora (foto 12 lugares despues, misma caja, ambas en la misma ventana)
fotos = fotos.sort_values(["cid", "ts"])
g = fotos.groupby("cid")
fotos["medio_1h"] = g.medio.shift(-12)
fotos["ts_1h"] = g.ts.shift(-12)
fotos["vent_1h"] = g.ventana.shift(-12)
mov_ok = (fotos.ts_1h - fotos.ts).between(3300, 3900) & (fotos.vent_1h == fotos.ventana)
fotos["mov1h"] = np.where(mov_ok, (fotos.medio_1h - fotos.medio).abs(), np.nan)

ll = pd.read_csv(os.path.join(C, "llenados.csv"), sep=";")
ll = ll[(ll.grupo == "clima") & (ll.dist_c == D)].copy()
ll["signo"] = np.where(ll.lado == "compra", 1, -1)
ll["pnl_res"] = np.where(ll.gano.isna(), np.nan, ll.signo * (ll.gano.fillna(0) - ll.precio_nuestro) * ll.acciones)
ll = ll.merge(fotos[["cid", "ts", "ventana", "cumple", "valido", "dia_ev"]].rename(columns={"ts": "ts_foto"}),
              on=["cid", "ts_foto"], how="inner")
ll = ll[ll.cumple & ll.valido]

lin = ["# Últimas 2 horas antes de la medianoche local vs. regla de hoy (clima, orden a 2 ¢, 100 acciones)", "",
       "Reglas: `maker/ultimas2h/REGLA.md` (escritas antes de ver esto). Datos: fotos cada 5 min del medidor maker "
       "(26-oct al 9-nov) y sus llenados simulados (solo los períodos con llenados válidos). Montos en US$ por caja y "
       "por hora, para 100 acciones por lado; el bot pone 20–25.", ""]
filas, boot = [], {}
rng = np.random.default_rng(1)
for w in ["fin del dia (ultimas 2 h)", "como hoy (>24 h al fin)"]:
    f = fotos[(fotos.ventana == w) & fotos.cumple]
    fv = f[f.valido]
    horas = len(fv) * 5 / 60                                     # caja-horas con llenados validos
    l = ll[ll.ventana == w]
    lr = l[l.pnl_res.notna()]
    rec_h = fv.pes.sum() * (5 / 1440) / horas if horas else np.nan
    llen_h = lr.pnl_res.sum() / horas if horas else np.nan
    reemb_h = l.reembolso.sum() / horas if horas else np.nan
    # bootstrap por dia del evento: (mitad de la recompensa + llenados + reembolso) / caja-horas
    por_dia = pd.DataFrame({"horas": fv.groupby("dia_ev").size() * 5 / 60,
                            "rec": fv.groupby("dia_ev").pes.sum() * (5 / 1440),
                            "llen": lr.groupby("dia_ev").pnl_res.sum(),
                            "reemb": l.groupby("dia_ev").reembolso.sum()}).fillna(0)
    por_dia = por_dia[por_dia.horas > 0]
    est = []
    for _ in range(5000):
        s = por_dia.iloc[rng.integers(0, len(por_dia), len(por_dia))]
        est.append((s.rec.sum() / 2 + s.llen.sum() + s.reemb.sum()) / s.horas.sum())
    lo, hi = np.percentile(est, [5, 95])
    filas.append({"ventana": w, "caja_horas": horas, "cajas_dist": f.cid.nunique(), "dias": len(por_dia),
                  "mov1h_c": 100 * f.mov1h.mean(), "pct_mov6": 100 * (f.mov1h >= 0.06).mean(),
                  "rec_h": rec_h, "llenados": len(l), "resueltos": len(lr), "acc_h": l.acciones.sum() / horas,
                  "llen_acc_c": 100 * lr.pnl_res.sum() / lr.acciones.sum() if len(lr) else np.nan,
                  "llen_h": llen_h, "reemb_h": reemb_h, "neto_h": rec_h + llen_h + reemb_h,
                  "neto_medio_h": rec_h / 2 + llen_h + reemb_h, "lo": lo, "hi": hi})
t = pd.DataFrame(filas)
lin += ["| ventana | caja-horas | días | mov. medio 1 h | horas con salto ≥6 ¢ | recompensa pesimista | llenados (resueltos) | "
        "acciones llenadas/h | llenados por acción | llenados | reembolso | neto | **neto con ½ recompensa** | intervalo 90 % |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in t.itertuples():
    lin.append(f"| {r.ventana} | {r.caja_horas:,.0f} | {r.dias} | {r.mov1h_c:.2f} ¢ | {r.pct_mov6:.1f} % | {r.rec_h:+.3f} | "
               f"{r.llenados} ({r.resueltos}) | {r.acc_h:.1f} | {r.llen_acc_c:+.2f} ¢ | {r.llen_h:+.3f} | {r.reemb_h:+.4f} | "
               f"{r.neto_h:+.3f} | **{r.neto_medio_h:+.3f}** | [{r.lo:+.3f}, {r.hi:+.3f}] |")
x = t.iloc[0]
if x.resueltos < 30:
    ver = "NO CONCLUYENTE (menos de 30 llenados resueltos en la ventana)"
elif x.neto_medio_h <= 0:
    ver = "NO PASA (neto con la mitad de la recompensa ≤ 0)"
elif x.lo > 0:
    ver = "PASA (neto > 0 y el intervalo del 90 % no toca el cero)"
else:
    ver = "DUDOSO (neto > 0 pero el intervalo cruza el cero)"
lin += ["", f"**Veredicto según la regla: {ver}.**", ""]
# cuantas cajas quedan para cotizar en la ventana (por evento-dia) y que precio tienen
f = fotos[(fotos.ventana == "fin del dia (ultimas 2 h)")]
lin += [f"En las últimas 2 h hay en promedio {f.groupby('ts').cid.nunique().mean():.0f} cajas vivas por foto y "
        f"{f[f.cumple].groupby('ts').cid.nunique().mean():.1f} cumplen los filtros del bot (spread ≤ 5 ¢, medio 0,03–0,97, pozo); "
        f"el resto ya está casi decidida (medio < 0,03 o > 0,97) o con el libro abierto.", ""]
open(os.path.join(AQUI, "informe.md"), "w", encoding="utf-8").write("\n".join(lin) + "\n")
print("\n".join(lin))
