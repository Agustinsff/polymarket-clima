# Pronóstico propio: elección del método (paso 2)

Generado 2026-11-08 14:03 UTC. Período de elección 2025-10-01 a 2026-09-30 (reglas en REGLAS.md); días con datos: 2025-10-01 a 2026-09-30 (365).

CRPS = error de la distribución completa (°C, menor es mejor). EMA = error medio absoluto de la media. Todos los métodos se miden sobre los mismos días.

## Todas las estaciones

| Método | Casos | CRPS | EMA |
|---|---|---|---|
| M0 | 64996 | 0.699 | 0.972 |
| M1 | 64996 | 0.649 | 0.900 |

Horizonte 1: M0 0.661, M1 0.609

Horizonte 2: M0 0.737, M1 0.688

## EE.UU. (con NBM y MOS)

| Método | Casos | CRPS | EMA |
|---|---|---|---|
| M0 | 16060 | 0.729 | 1.010 |
| M1 | 16060 | 0.671 | 0.927 |
| M1-EEUU | 16060 | 0.661 | 0.913 |

## Elección (regla fija)

M1 vs M0: +7.2 % de CRPS → se usa **M1** (M1 tiene que ganar por 2 % o más).
En EE.UU., M1-EEUU vs M1: +1.6 % → se usa M1 en EE.UU.
