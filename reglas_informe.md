# Reglas de los mercados de Polymarket

Actualizado 2026-10-30 10:26 UTC por `reglas.py` (cada 3 h). Lo que Polymarket usa hoy en cada familia de mercados, y los cambios que se detectaron.

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-10-29 06:25 UTC): `what-intensity-will-champi-reach`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura máxima** (fuente de resolución, ya no aparece el 2026-10-28 18:29 UTC): `weather.gov/wrh/timeseries`. Ver [reglas_informe.md](reglas_informe.md).

## Comisiones

Comisión del taker = **tasa × p × (1 − p)** por acción. Desde el 23-oct cada operación en papel anota la tasa que trae su mercado (`feeSchedule.rate`, columna `tasa_comision`); las de antes usan 0.05 para todo. Según la ayuda de Polymarket (julio 2026) la tasa es 0.05 en clima y 0.07 en cripto.

| Familia | Eventos abiertos | Comisión que trae el mercado (cajas) | Tasa |
|---|---|---|---|
| cripto bitcoin-hit-price-daily | 1 | `feesEnabled=True feeType=crypto_fees_v2 feeSchedule={"exponent": 1, "rate": 0.07, "rebateRate": 0.2, "takerOnly": true} takerBaseFee=1000` (1) | 0.07 |
| cripto bitcoin-neg-risk-weekly | 7 | `feesEnabled=True feeType=crypto_fees_v2 feeSchedule={"exponent": 1, "rate": 0.07, "rebateRate": 0.2, "takerOnly": true} takerBaseFee=1000` (7) | 0.07 |
| cripto btc-multi-strikes-weekly | 7 | `feesEnabled=True feeType=crypto_fees_v2 feeSchedule={"exponent": 1, "rate": 0.07, "rebateRate": 0.2, "takerOnly": true} takerBaseFee=1000` (7) | 0.07 |
| cripto ethereum-hit-price-daily | 1 | `feesEnabled=True feeType=crypto_fees_v2 feeSchedule={"exponent": 1, "rate": 0.07, "rebateRate": 0.2, "takerOnly": true} takerBaseFee=1000` (1) | 0.07 |
| cripto ethereum-multi-strikes-weekly | 7 | `feesEnabled=True feeType=crypto_fees_v2 feeSchedule={"exponent": 1, "rate": 0.07, "rebateRate": 0.2, "takerOnly": true} takerBaseFee=1000` (7) | 0.07 |
| cripto ethereum-neg-risk-weekly | 7 | `feesEnabled=True feeType=crypto_fees_v2 feeSchedule={"exponent": 1, "rate": 0.07, "rebateRate": 0.2, "takerOnly": true} takerBaseFee=1000` (7) | 0.07 |
| temperatura máxima | 142 | `feesEnabled=True feeType=zero_fees feeSchedule={"exponent": 1, "rate": 0, "rebateRate": 0, "takerOnly": true} takerBaseFee=1000` (138) | 0 |
| temperatura máxima | 142 | `feesEnabled=True feeType=weather_fees feeSchedule={"exponent": 1, "rate": 0.05, "rebateRate": 0.25, "takerOnly": true} takerBaseFee=1000` (4) | 0.05 |
| temperatura mínima | 127 | `feesEnabled=True feeType=zero_fees feeSchedule={"exponent": 1, "rate": 0, "rebateRate": 0, "takerOnly": true} takerBaseFee=1000` (127) | 0 |

## Fuente de resolución y parámetros

| Familia | Qué | Variante (eventos o cajas) | Desde |
|---|---|---|---|
| cripto bitcoin-hit-price-daily | fuente de resolución | `binance.com/en/trade/BTC_USDT` (1) | 2026-10-23 13:08 |
| cripto bitcoin-hit-price-daily | parámetros | `orden minima=5 tick=0.01` (1) | 2026-10-23 13:08 |
| cripto bitcoin-hit-price-daily | parámetros | `orden minima=5 tick=0.001` (1) | 2026-10-23 13:08 |
| cripto bitcoin-neg-risk-weekly | fuente de resolución | `binance.com/en/trade/BTC_USDT` (7) | 2026-10-23 13:08 |
| cripto bitcoin-neg-risk-weekly | parámetros | `orden minima=5 tick=0.01` (7) | 2026-10-23 13:08 |
| cripto bitcoin-neg-risk-weekly | parámetros | `orden minima=5 tick=0.001` (7) | 2026-10-23 13:08 |
| cripto btc-multi-strikes-weekly | fuente de resolución | `binance.com/en/trade/BTC_USDT` (7) | 2026-10-23 13:08 |
| cripto btc-multi-strikes-weekly | parámetros | `orden minima=5 tick=0.001` (7) | 2026-10-23 13:08 |
| cripto btc-multi-strikes-weekly | parámetros | `orden minima=5 tick=0.01` (6) | 2026-10-23 13:08 |
| cripto ethereum-hit-price-daily | fuente de resolución | `binance.com/en/trade/ETH_USDT` (1) | 2026-10-23 13:08 |
| cripto ethereum-hit-price-daily | parámetros | `orden minima=5 tick=0.01` (1) | 2026-10-23 13:08 |
| cripto ethereum-hit-price-daily | parámetros | `orden minima=5 tick=0.001` (1) | 2026-10-23 13:08 |
| cripto ethereum-multi-strikes-weekly | fuente de resolución | `binance.com/en/trade/ETH_USDT` (7) | 2026-10-23 13:08 |
| cripto ethereum-multi-strikes-weekly | parámetros | `orden minima=5 tick=0.001` (7) | 2026-10-23 13:08 |
| cripto ethereum-multi-strikes-weekly | parámetros | `orden minima=5 tick=0.01` (6) | 2026-10-23 13:08 |
| cripto ethereum-neg-risk-weekly | fuente de resolución | `binance.com/en/trade/ETH_USDT` (7) | 2026-10-23 13:08 |
| cripto ethereum-neg-risk-weekly | parámetros | `orden minima=5 tick=0.001` (7) | 2026-10-23 13:08 |
| cripto ethereum-neg-risk-weekly | parámetros | `orden minima=5 tick=0.01` (7) | 2026-10-23 13:08 |
| temperatura máxima | fuente de resolución | `aviationweather.gov/api/data/metar` (135) | 2026-10-23 13:08 |
| temperatura máxima | fuente de resolución | `wunderground.com/history/daily` (4) | 2026-10-23 13:08 |
| temperatura máxima | fuente de resolución | `(sin fuente)` (3) | 2026-10-23 13:08 |
| temperatura máxima | parámetros | `orden minima=5 tick=0.001` (138) | 2026-10-23 13:08 |
| temperatura máxima | parámetros | `orden minima=5 tick=0.01` (120) | 2026-10-23 13:08 |
| temperatura mínima | fuente de resolución | `aviationweather.gov/api/data/metar` (124) | 2026-10-23 13:08 |
| temperatura mínima | fuente de resolución | `(sin fuente)` (3) | 2026-10-23 13:08 |
| temperatura mínima | parámetros | `orden minima=5 tick=0.01` (120) | 2026-10-23 13:08 |
| temperatura mínima | parámetros | `orden minima=5 tick=0.001` (84) | 2026-10-23 13:08 |

## Mercados de clima que no son de temperatura diaria

- `1-megaton-meteor-strike`: 1 abiertos (ej. `1-megaton-meteor-strike-in-2026`), visto desde 2026-10-23 13:08
- `10pt0-or-above-earthquake-before`: 1 abiertos (ej. `10pt0-or-above-earthquake-before-2027`), visto desde 2026-10-23 13:08
- `5kt-meteor-strike`: 1 abiertos (ej. `5kt-meteor-strike-in-2026`), visto desde 2026-10-23 13:08
- `9pt0-or-above-earthquake-before`: 1 abiertos (ej. `9pt0-or-above-earthquake-before-2027`), visto desde 2026-10-23 13:08
- `ai-data-center`: 1 abiertos (ej. `ai-data-center-in-space-by`), visto desde 2026-10-23 13:08
- `all-time-pacific-category`: 1 abiertos (ej. `all-time-pacific-category-5-hurricane-record-broken-in-2026`), visto desde 2026-10-23 13:08
- `biggest-earthquake`: 4 abiertos (ej. `biggest-earthquake-2026-10-29`), visto desde 2026-10-23 13:08
- `blue-origin-new-glenn-launch`: 1 abiertos (ej. `blue-origin-new-glenn-launch-in-2026`), visto desde 2026-10-23 13:08
- `california-winter`: 1 abiertos (ej. `california-winter-2026-27-wetter-or-drier`), visto desde 2026-10-23 13:08
- `ebola-pandemic`: 1 abiertos (ej. `ebola-pandemic-in-2026`), visto desde 2026-10-23 13:08
- `etna-eruption-with-vei`: 1 abiertos (ej. `etna-eruption-with-vei-2-in-2026`), visto desde 2026-10-23 13:08
- `first-snow`: 1 abiertos (ej. `first-snow-2026`), visto desde 2026-10-23 13:08
- `hantavirus-pandemic`: 1 abiertos (ej. `hantavirus-pandemic-in-2026`), visto desde 2026-10-23 13:08
- `hantavirus-vaccine`: 1 abiertos (ej. `hantavirus-vaccine-in-2026`), visto desde 2026-10-23 13:08
- `highest-earthquake-magnitude`: 1 abiertos (ej. `highest-earthquake-magnitude-in-2026`), visto desde 2026-10-23 13:08
- `highest-mtpt-washington-wind-speed`: 1 abiertos (ej. `highest-mtpt-washington-wind-speed-in-october-20260928t160000000z`), visto desde 2026-10-23 13:08
- `highest-sea-level`: 1 abiertos (ej. `highest-sea-level-in-san-diego-this-winter`), visto desde 2026-10-23 13:08
- `how-low-will-lake-mead-drop`: 1 abiertos (ej. `how-low-will-lake-mead-drop-1786981653904`), visto desde 2026-10-23 13:08
- `how-low-will-lake-powell-drop`: 1 abiertos (ej. `how-low-will-lake-powell-drop-1786980780361`), visto desde 2026-10-23 13:08
- `how-many`: 3 abiertos (ej. `how-many-7pt0-or-above-earthquakes-in-2026`), visto desde 2026-10-23 13:08
- `how-many-chinook-will-pass-bonneville-dam-by`: 1 abiertos (ej. `how-many-chinook-will-pass-bonneville-dam-by-october-31-2026`), visto desde 2026-10-23 13:08
- `how-many-hurricanes-will-form-during-the-atlantic-hurricane-season`: 1 abiertos (ej. `how-many-hurricanes-will-form-during-the-atlantic-hurricane-season-in-2026-20260728201848339`), visto desde 2026-10-23 13:08
- `how-many-large-volcano-eruption-vei`: 1 abiertos (ej. `how-many-large-volcano-eruption-vei-4-in-2026-657`), visto desde 2026-10-23 13:08
- `how-many-tornadoes`: 1 abiertos (ej. `how-many-tornadoes-in-the-us-in-2026`), visto desde 2026-10-23 13:08
- `how-many-tropical-cyclones-will-make-landfall`: 1 abiertos (ej. `how-many-tropical-cyclones-will-make-landfall-in-china-during-2026-20260805184236864`), visto desde 2026-10-23 13:08
- `how-strong-of-an-earthquake-will-occur-worldwide-by`: 1 abiertos (ej. `how-strong-of-an-earthquake-will-occur-worldwide-by-october-31-20260928t160000000z`), visto desde 2026-10-23 13:08
- `lowest-great-salt-lake-elevation`: 1 abiertos (ej. `lowest-great-salt-lake-elevation-in-2026`), visto desde 2026-10-23 13:08
- `lowest-mississippi-level-at-baton-rouge-by`: 1 abiertos (ej. `lowest-mississippi-level-at-baton-rouge-by-november-30`), visto desde 2026-10-23 13:08
- `lowest-mississippi-level-at-st-louis-by`: 1 abiertos (ej. `lowest-mississippi-level-at-st-louis-by-november-30`), visto desde 2026-10-23 13:08
- `magnitude`: 1 abiertos (ej. `magnitude-6pt5-earthquake-in-la-before-2027`), visto desde 2026-10-23 13:08
- `major-meteor-strike`: 1 abiertos (ej. `major-meteor-strike-10kt-in-2026`), visto desde 2026-10-23 13:08
- `major-volcano-eruption-vei`: 1 abiertos (ej. `major-volcano-eruption-vei-6-in-2026`), visto desde 2026-10-23 13:08
- `measles-cases`: 2 abiertos (ej. `measles-cases-in-us-in-2026`), visto desde 2026-10-23 13:08
- `melbournes-wettest-month-of`: 1 abiertos (ej. `melbournes-wettest-month-of-2026`), visto desde 2026-10-23 13:08
- `natural-disaster`: 1 abiertos (ej. `natural-disaster-in-2026`), visto desde 2026-10-23 13:08
- `october`: 2 abiertos (ej. `october-2026-temperature-increase-c-20260928t160000000z`), visto desde 2026-10-23 13:08
- `peak-severe-drought`: 1 abiertos (ej. `peak-severe-drought-in-minas-gerais-during-the-coffee-growing-season`), visto desde 2026-10-23 13:08
- `peak-wind-gust`: 1 abiertos (ej. `peak-wind-gust-in-the-worlds-windiest-city-in-october-20260928t160000000z`), visto desde 2026-10-23 13:08
- `precipitation`: 5 abiertos (ej. `precipitation-in-london-in-october-20260925t160000000z`), visto desde 2026-10-23 13:08
- `state-d4-drought`: 1 abiertos (ej. `state-d4-drought-2026-11-03`), visto desde 2026-10-23 13:08
- `us-tornadoes`: 2 abiertos (ej. `us-tornadoes-september-2026`), visto desde 2026-10-23 13:08
- `vesuvius-eruption-with`: 1 abiertos (ej. `vesuvius-eruption-with-1-vei-in-2026`), visto desde 2026-10-23 13:08
- `west-nile-neuroinvasive-cases-nyc`: 1 abiertos (ej. `west-nile-neuroinvasive-cases-nyc-2026-20260820104404`), visto desde 2026-10-23 13:08
- `what-category-will-vance-reach`: 1 abiertos (ej. `what-category-will-vance-reach`), visto desde 2026-10-23 13:08
- `what-intensity-will`: 1 abiertos (ej. `what-intensity-will-in-fa-reach`), visto desde 2026-10-26 20:44
- `what-will-the-peak-roni-be`: 1 abiertos (ej. `what-will-the-peak-roni-be-for-the-2026-27-el-nino-1786975502957`), visto desde 2026-10-23 13:08
- `when-will-the-danube-river-return-to-normal-levels`: 1 abiertos (ej. `when-will-the-danube-river-return-to-normal-levels-20260807212534133`), visto desde 2026-10-23 13:08
- `when-will-the-rhine-river-return-to-normal-levels`: 1 abiertos (ej. `when-will-the-rhine-river-return-to-normal-levels-20260906`), visto desde 2026-10-23 13:08
- `where-will`: 1 abiertos (ej. `where-will-2026-rank-among-the-hottest-years-on-record`), visto desde 2026-10-23 13:08
- `where-will-a`: 1 abiertos (ej. `where-will-a-6pt0-magnitude-earthquake-occur-by-end-of-october-20260928t160000000z`), visto desde 2026-10-23 13:08
- `where-will-a-hurricane-make-landfall`: 1 abiertos (ej. `where-will-a-hurricane-make-landfall-in-the-us-during-the-2026-hurricane-season`), visto desde 2026-10-23 13:08
- `where-will-it-rain`: 2 abiertos (ej. `where-will-it-rain-on-october-29-2026`), visto desde 2026-10-23 13:08
- `which-countries-will-have-an-ebola-case`: 1 abiertos (ej. `which-countries-will-have-an-ebola-case-in-2026`), visto desde 2026-10-23 13:08
- `will`: 1 abiertos (ej. `will-2-or-more-hurricanes-make-landfall-in-the-us-in-2026-20260721164140039`), visto desde 2026-10-23 13:08
- `will-a-hurricane-make-landfall`: 1 abiertos (ej. `will-a-hurricane-make-landfall-in-hawaii-before-2027-20260721182828397`), visto desde 2026-10-23 13:08
- `will-any-category`: 2 abiertos (ej. `will-any-category-4-hurricane-make-landfall-in-the-us-in-before-2027`), visto desde 2026-10-23 13:08
- `will-california-experience-a`: 1 abiertos (ej. `will-california-experience-a-7pt0-or-above-magnitude-earthquake-in-2026-20260723232901145`), visto desde 2026-10-23 13:08
- `will-hawaii-reach-coral-bleaching-alert-level`: 1 abiertos (ej. `will-hawaii-reach-coral-bleaching-alert-level-1-by-december-31-2026-20260807170348514`), visto desde 2026-10-23 13:08
- `will-it-rain-during-the-united-states-grand-prix`: 1 abiertos (ej. `will-it-rain-during-the-united-states-grand-prix`), visto desde 2026-10-23 13:08
- `will-the`: 1 abiertos (ej. `will-the-2026-27-el-nino-be-the-strongest-on-record`), visto desde 2026-10-23 13:08
- `will-the-climate-clocks`: 1 abiertos (ej. `will-the-climate-clocks-1pt5c-deadline-change-byptptpt`), visto desde 2026-10-23 13:08
- `will-the-tfff-reach`: 1 abiertos (ej. `will-the-tfff-reach-10-billion-in-2026`), visto desde 2026-10-23 13:08
- `will-the-us-break-its-record`: 1 abiertos (ej. `will-the-us-break-its-record-for-billion-dollar-weather-and-climate-disasters-in-2026-1787153419673`), visto desde 2026-10-23 13:08
- `will-there-be-a-super-el-nino-this-winter`: 1 abiertos (ej. `will-there-be-a-super-el-nino-this-winter-202627-20260721221614682`), visto desde 2026-10-23 13:08

## Ciudades con mercado de temperatura

- **temperatura máxima** (51): amsterdam, ankara, atlanta, austin, beijing, buenos-aires, busan, cape-town, chengdu, chicago, chongqing, dallas, denver, guangzhou, helsinki, hong-kong, houston, istanbul, jeddah, jinan, karachi, kuala-lumpur, london, los-angeles, lucknow, madrid, manila, mexico-city, miami, milan, moscow, munich, nyc, panama-city, paris, qingdao, san-francisco, sao-paulo, seattle, seoul, shanghai, shenzhen, singapore, taipei, tel-aviv, tokyo, toronto, warsaw, wellington, wuhan, zhengzhou
- **temperatura mínima** (45): amsterdam, ankara, atlanta, austin, beijing, buenos-aires, busan, cape-town, chengdu, chicago, chongqing, dallas, denver, guangzhou, helsinki, hong-kong, houston, istanbul, jeddah, karachi, london, los-angeles, lucknow, madrid, mexico-city, miami, milan, moscow, munich, nyc, paris, qingdao, san-francisco, sao-paulo, seattle, seoul, shanghai, shenzhen, taipei, tel-aviv, tokyo, toronto, warsaw, wellington, wuhan

## Últimos cambios

| Cuándo (UTC) | Familia | Qué | Cambio | Detalle | Origen |
|---|---|---|---|---|---|
| 2026-10-29 06:25 | clima (otros) | mercado de clima nuevo | ya no aparece | what-intensity-will-champi-reach | auto |
| 2026-10-28 18:29 | temperatura máxima | fuente de resolución | ya no aparece | weather.gov/wrh/timeseries | auto |
| 2026-10-28 00:43 | temperatura mínima | fuente de resolución | ya no aparece | weather.gov/wrh/timeseries | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | To toggle between Fahrenheit and Celsius, click the "Switch to Metric Units" button until the relevant table displays °C. | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | The resolution source for this market measures temperatures to whole degrees Celsius (eg, #°C). | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | This market will resolve once the first data point for the following date has been published on the resolution source, or by #:# PM ET on the day following the observation date, whichever comes first. | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | Revisions to temperatures recorded within this market's timeframe will be considered until the first datapoint for the following date has been published, after which any alterations will not be considered. | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | The resolution source for this market will be information from <estacion>, specifically the lowest reading under the "Temp" column for all times on this day, available here: | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | Thus, this is the level of precision that will be used when resolving the market. | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | If <estacion> data for the observation date is unavailable by #:# PM ET on the day following the observation date, the Weather Underground Daily Observations table will be used as the resolution source. | auto |
| 2026-10-27 00:47 | temperatura mínima | reglamento | ya no aparece | In the event that there is no data for the observation date by #:# PM ET on the day following the observation date, this market will resolve to the lowest bracket. | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | To toggle between Fahrenheit and Celsius, click the "Switch to Metric Units" button until the relevant table displays °C. | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | The resolution source for this market will be information from <estacion>, specifically the highest reading under the "Temp" column for all times on this day, available here: | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | This market will resolve once the first data point for the following date has been published on the resolution source, or by #:# PM ET on the day following the observation date, whichever comes first. | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | Revisions to temperatures recorded within this market's timeframe will be considered until the first datapoint for the following date has been published, after which any alterations will not be considered. | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | If <estacion> data for the observation date is unavailable by #:# PM ET on the day following the observation date, the Weather Underground Daily Observations table will be used as the resolution source. | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | In the event that there is no data for the observation date by #:# PM ET on the day following the observation date, this market will resolve to the lowest bracket. | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | The resolution source for this market measures temperatures to whole degrees Celsius (eg, #°C). | auto |
| 2026-10-27 00:47 | temperatura máxima | reglamento | ya no aparece | Thus, this is the level of precision that will be used when resolving the market. | auto |
| 2026-10-26 20:44 | clima (otros) | mercado de clima nuevo | aparece | what-intensity-will-arnab-reach | auto |
| 2026-10-26 20:44 | clima (otros) | mercado de clima nuevo | aparece | what-intensity-will | auto |
| 2026-10-23 23:58 | temperatura máxima | reglamento | aparece | The qualifying value is converted using °F = °C × #/# + # and rounded to the nearest whole degree, with a value ending in exactly half rounded up to the next higher whole degree, and that whole Fahrenheit value determines which range contains it. | auto |
| 2026-10-23 23:58 | temperatura máxima | reglamento | aparece | Each market in this event states its range in whole degrees Fahrenheit. | auto |
| 2026-10-23 23:58 | temperatura máxima | reglamento | aparece | For example, #°C is #°F and counts as #°F; | auto |
| 2026-10-23 23:58 | temperatura máxima | reglamento | aparece | #°C is exactly #°F and counts as #°F. | auto |
| 2026-10-23 23:58 | temperatura máxima | reglamento | aparece | #°C is #°F and counts as #°F; | auto |
| 2026-10-23 19:31 | temperatura mínima | reglamento | aparece | #°C is exactly #°F and counts as #°F. | auto |
| 2026-10-23 19:31 | temperatura mínima | reglamento | aparece | The qualifying value is converted using °F = °C × #/# + # and rounded to the nearest whole degree, with a value ending in exactly half rounded up to the next higher whole degree, and that whole Fahrenheit value determines which range contains it. | auto |
| 2026-10-23 19:31 | temperatura mínima | reglamento | aparece | Each market in this event states its range in whole degrees Fahrenheit. | auto |
| 2026-10-23 19:31 | temperatura mínima | reglamento | aparece | #°C is #°F and counts as #°F; | auto |

## Reglamento actual (frases comunes)

<details><summary>cripto bitcoin-hit-price-daily (1 frases)</summary>

- What price will Bitcoin hit on <mes> #?

</details>

<details><summary>cripto bitcoin-neg-risk-weekly (5 frases)</summary>

- If the reported value falls exactly between two brackets, then this market will resolve to the higher range bracket.
- Otherwise, this market will resolve to "No".
- Please note that this market is about the price according to Binance BTC/<estacion>, not according to other exchanges or trading pairs.
- The resolution source for this market is Binance, specifically the BTC/<estacion> "Close" prices currently available at <link> with "#m" and "Candles" selected on the top bar.
- This market will resolve according to the final "Close" price of the Binance # minute candle for BTC/<estacion> closing at #:# in the ET timezone (noon) on the date specified in the title.

</details>

<details><summary>cripto btc-multi-strikes-weekly (5 frases)</summary>

- Otherwise, this market will resolve to "No".
- Please note that this market is about the price according to Binance BTC/<estacion>, not according to other exchanges or trading pairs.
- Price precision is determined by the number of decimal places in the source.
- The resolution source for this market is Binance, specifically the BTC/<estacion> "Close" prices currently available at <link> with "#m" and "Candles" selected on the top bar.
- This market will resolve to "Yes" if the Binance # minute candle for BTC/<estacion> closing at #:# in the ET timezone (noon) on the date specified in the title has a final "Close" price higher than the price specified in the title.

</details>

<details><summary>cripto ethereum-hit-price-daily (1 frases)</summary>

- What price will Ethereum hit on <mes> #?

</details>

<details><summary>cripto ethereum-multi-strikes-weekly (5 frases)</summary>

- Otherwise, this market will resolve to "No".
- Please note that this market is about the price according to Binance ETH/<estacion>, not according to other exchanges or trading pairs.
- Price precision is determined by the number of decimal places in the source.
- The resolution source for this market is Binance, specifically the ETH/<estacion> "Close" prices currently available at <link> with "#m" and "Candles" selected on the top bar.
- This market will resolve to "Yes" if the Binance # minute candle for ETH/<estacion> closing at #:# in the ET timezone (noon) on the date specified in the title has a final "Close" price higher than the price specified in the title.

</details>

<details><summary>cripto ethereum-neg-risk-weekly (5 frases)</summary>

- If the reported value falls exactly between two brackets, then this market will resolve to the higher range bracket.
- Otherwise, this market will resolve to "No".
- Please note that this market is about the price according to Binance ETH/<estacion>, not according to other exchanges or trading pairs.
- The resolution source for this market is Binance, specifically the ETH/<estacion> "Close" prices currently available at <link> with "#m" and "Candles" selected on the top bar.
- This market will resolve according to the final "Close" price of the Binance # minute candle for ETH/<estacion> closing at #:# in the ET timezone (noon) on the date specified in the title.

</details>

<details><summary>temperatura máxima (32 frases)</summary>

- #°C is #°F and counts as #°F;
- #°C is exactly #°F and counts as #°F.
- A report whose line begins with SPECI is a special observation and does not count.
- After the T, one digit for sign (# positive, # negative) and three for tenths of a degree Celsius give the temperature;
- An observation counts if its time stamp, converted to the station's local time (including any daylight-saving shift in effect), falls on the observation date.
- An observation that reports no temperature in either place is disregarded.
- Changes to observations within this market's timeframe will be considered until the first datapoint for the following date has been published, after which any alterations will not be considered.
- Each market in this event states its range in whole degrees Celsius.
- Each market in this event states its range in whole degrees Fahrenheit.
- Every other report is routine, including one issued off the nominal hour and one that carries no METAR or SPECI label.
- For How to Read the METAR Report, see:
- For example, #°C counts as #°C;
- For example, #°C is #°F and counts as #°F;
- If a routine observation does not carry the hourly temperature remark, the temperature group in the body of that observation governs for that observation, in whole degrees Celsius as reported.
- If no corrected value is published within that period, Polymarket will issue a Clarification to determine whether the originally published value may be eligible for resolution, or whether other action is required to preserve the orderly functioning of the Market.
- If the Resolution Source publishes a corrected value within that period, that value will be eligible for resolution.
- In the case that the Resolution Source publishes data, sufficient to settle a Market, that is clearly erroneous and the result of technical or operational error, or of unauthorized interference with the Resolution Source or its data, the Market may remain open for a period of up to seven (#) calendar days (ET) from the time of the original release, in anticipation of a correction by the Resolution
- In the event that neither source has published data sufficient to determine a temperature for the observation date by #:# PM ET on the day following the observation date, this market will resolve to the lowest bracket.
- In the event that the Aviation Weather Center has published no routine observation reporting a temperature for the observation date by #:# PM ET on the day following the observation date, the Weather Underground Daily Observations table will be used as the resolution source.
- It appears as temperature and dew point separated by a slash, with M marking a negative value:
- Resolution is determined from the observations the resolution source shows for the observation date.
- The hourly temperature remark is the group beginning with the letter T followed by exactly eight digits.
- The qualifying value is converted using °F = °C × #/# + # and rounded to the nearest whole degree, with a value ending in exactly half rounded up to the next higher whole degree, and that whole Fahrenheit value determines which range contains it.
- The qualifying value is rounded to the nearest whole degree, with a value ending in exactly half rounded up to the next higher whole degree, and that whole Celsius value determines which range contains it.
- The qualifying value is the highest temperature reported in the hourly temperature remark of any routine (METAR) observation for <estacion> on that date, in tenths of a degree Celsius as reported.
- The report the resolution source shows for a given observation time is the one that counts, whether or not it is marked as a correction (COR).
- The resolution source for this market will be the routine observations for <estacion> published here:
- This market will resolve at the issuance of the first METAR observation for the station on the day following the observation date or by #:# PM ET on the day following the observation date, whichever comes first.
- This market will resolve to the temperature range that contains the highest temperature reported at <estacion> on # <mes> #.
- Where it is not, resolution is determined from a read taken at that deadline.
- Where the first routine observation for the following date is published before that deadline, resolution is determined from a read taken after it.
- the following four are the dew point and are not used.

</details>

<details><summary>temperatura mínima (32 frases)</summary>

- #°C is #°F and counts as #°F;
- #°C is exactly #°F and counts as #°F.
- A report whose line begins with SPECI is a special observation and does not count.
- After the T, one digit for sign (# positive, # negative) and three for tenths of a degree Celsius give the temperature;
- An observation counts if its time stamp, converted to the station's local time (including any daylight-saving shift in effect), falls on the observation date.
- An observation that reports no temperature in either place is disregarded.
- Changes to observations within this market's timeframe will be considered until the first datapoint for the following date has been published, after which any alterations will not be considered.
- Each market in this event states its range in whole degrees Celsius.
- Each market in this event states its range in whole degrees Fahrenheit.
- Every other report is routine, including one issued off the nominal hour and one that carries no METAR or SPECI label.
- For How to Read the METAR Report, see:
- For example, #°C counts as #°C;
- For example, #°C is #°F and counts as #°F;
- If a routine observation does not carry the hourly temperature remark, the temperature group in the body of that observation governs for that observation, in whole degrees Celsius as reported.
- If no corrected value is published within that period, Polymarket will issue a Clarification to determine whether the originally published value may be eligible for resolution, or whether other action is required to preserve the orderly functioning of the Market.
- If the Resolution Source publishes a corrected value within that period, that value will be eligible for resolution.
- In the case that the Resolution Source publishes data, sufficient to settle a Market, that is clearly erroneous and the result of technical or operational error, or of unauthorized interference with the Resolution Source or its data, the Market may remain open for a period of up to seven (#) calendar days (ET) from the time of the original release, in anticipation of a correction by the Resolution
- In the event that neither source has published data sufficient to determine a temperature for the observation date by #:# PM ET on the day following the observation date, this market will resolve to the lowest bracket.
- In the event that the Aviation Weather Center has published no routine observation reporting a temperature for the observation date by #:# PM ET on the day following the observation date, the Weather Underground Daily Observations table will be used as the resolution source.
- It appears as temperature and dew point separated by a slash, with M marking a negative value:
- Resolution is determined from the observations the resolution source shows for the observation date.
- The hourly temperature remark is the group beginning with the letter T followed by exactly eight digits.
- The qualifying value is converted using °F = °C × #/# + # and rounded to the nearest whole degree, with a value ending in exactly half rounded up to the next higher whole degree, and that whole Fahrenheit value determines which range contains it.
- The qualifying value is rounded to the nearest whole degree, with a value ending in exactly half rounded up to the next higher whole degree, and that whole Celsius value determines which range contains it.
- The qualifying value is the lowest temperature reported in the hourly temperature remark of any routine (METAR) observation for <estacion> on that date, in tenths of a degree Celsius as reported.
- The report the resolution source shows for a given observation time is the one that counts, whether or not it is marked as a correction (COR).
- The resolution source for this market will be the routine observations for <estacion> published here:
- This market will resolve at the issuance of the first METAR observation for the station on the day following the observation date or by #:# PM ET on the day following the observation date, whichever comes first.
- This market will resolve to the temperature range that contains the lowest temperature reported at <estacion> on # <mes> #.
- Where it is not, resolution is determined from a read taken at that deadline.
- Where the first routine observation for the following date is published before that deadline, resolution is determined from a read taken after it.
- the following four are the dew point and are not used.

</details>

