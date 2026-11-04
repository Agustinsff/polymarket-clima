# Pronóstico propio: elección del método (paso 2)

Generado 2026-11-04 12:04 UTC. Período de elección 2025-10-01 a 2026-09-30 (reglas en REGLAS.md); días con datos: 2026-03-01 a 2026-09-30 (214).

CRPS = error de la distribución completa (°C, menor es mejor). EMA = error medio absoluto de la media. Todos los métodos se miden sobre los mismos días.

## Todas las estaciones

| Método | Casos | CRPS | EMA |
|---|---|---|---|
| M0 | 30585 | 0.660 | 0.918 |
| M1 | 30585 | 0.621 | 0.859 |

Horizonte 1: M0 0.624, M1 0.588

Horizonte 2: M0 0.696, M1 0.653

## EE.UU. (con NBM y MOS)

| Método | Casos | CRPS | EMA |
|---|---|---|---|
| M0 | 7442 | 0.668 | 0.920 |
| M1 | 7442 | 0.619 | 0.844 |
| M1-EEUU | 7442 | 0.613 | 0.836 |

## Elección (regla fija)

M1 vs M0: +6.0 % de CRPS → se usa **M1** (M1 tiene que ganar por 2 % o más).
En EE.UU., M1-EEUU vs M1: +1.0 % → se usa M1 en EE.UU.

**Provisorio**: faltan datos del período de elección (214 de 365 días).
