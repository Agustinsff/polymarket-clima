# Bot maker en un servidor (sin depender de la PC)

Para que el bot maker siga andando aunque la PC se apague. Escrito el 7-nov-2026.

## Dónde ponerlo

Polymarket bloquea operar desde EE.UU., Reino Unido, Alemania, Francia, Italia, Polonia, **Brasil y Argentina**
(entre otros; lista en <https://docs.polymarket.com/developers/CLOB/geoblock>). No bloquea Uruguay, Chile,
Finlandia, Suecia ni España. Por eso no sirve GitHub Actions (EE.UU.) ni un servidor en São Paulo o Buenos Aires.

| Opción | Costo | Pros | Contras |
|---|---|---|---|
| **Servidor Hetzner en Helsinki (CX23)** — recomendado | ≈ € 4–5 por mes | barato, estable, cerca de los servidores de Polymarket (Londres) | piden tarjeta y a veces documento al abrir la cuenta |
| Servidor en Santiago de Chile (Vultr u otro) | ≈ US$ 5–6 por mes | país permitido y cerca | un poco más caro |
| Oracle Cloud "Always Free" (Madrid, Estocolmo o Santiago) | gratis | gratis | alta engorrosa, a veces "sin capacidad"; puede borrar máquinas que usan poca CPU |
| Raspberry Pi en tu casa | ≈ US$ 80 una vez | sin pago mensual | se corta igual con la luz o internet de casa; el DNS de Antel |
| Seguir en la PC + arranque automático de Windows | gratis | sin cambios | solo arregla reinicios; si la apagás, se apaga |

Con recompensas de ≈ US$ 1 por día, el servidor cuesta ≈ 15 % de lo que entra. Si en la semana de prueba la
recompensa real no llega, se borra el servidor y se deja de pagar (se paga por hora).

**Términos de Polymarket:** prohíben usar VPN para saltear el bloqueo de un país. Acá no se saltea nada: vos vivís en
Uruguay (permitido) y el servidor está en un país permitido. Igual es una zona gris: una IP de centro de datos podría
llamar la atención y, en el peor caso, Polymarket podría poner la cuenta en "solo cerrar" (se pueden vender y cobrar
las acciones, no abrir nuevas). Con US$ 100 en juego el riesgo es acotado.

## Pasos

### 1. Crear el servidor (10 minutos, una vez)

1. En la PC, abrir PowerShell y crear una llave para entrar al servidor sin contraseña:
   `ssh-keygen -t ed25519` (Enter a todo). La llave pública queda en `C:\Users\Aguwus\.ssh\id_ed25519.pub`.
2. En <https://console.hetzner.cloud>: crear cuenta → proyecto → **Add Server**: ubicación **Helsinki**, imagen
   **Ubuntu 24.04**, tipo **CX23** (el más barato, x86), en "SSH keys" pegar el contenido de `id_ed25519.pub`.
3. Anotar la IP del servidor. Probar: `ssh root@IP` (contestar `yes` la primera vez).

### 2. Instalar (5 minutos; el bot NO arranca todavía)

Dentro del servidor (`ssh root@IP`):

```
curl -fsSL https://raw.githubusercontent.com/Agustinsff/polymarket-clima/main/bot/linux/instalar.sh | bash
```

Primero revisa que Polymarket deje operar desde ahí (si dice ALTO, ese servidor no sirve: borrarlo). Después instala
Python, baja el repo, corre las pruebas del bot y deja el servicio instalado pero apagado.

### 3. El día del cambio (5 minutos)

1. En la PC: `bot\parar_bot.cmd` y esperar que la ventana del bot diga "Bot maker apagado" (cancela las órdenes).
2. En la PC, PowerShell, en la carpeta del repo, copiar las claves y el estado al servidor (las claves viajan
   cifradas por ssh; no se pegan en ningún chat):

   ```
   cd C:\Users\Aguwus\Documents\polymarket-clima-repo
   ssh root@IP mkdir -p /root/migrar
   scp bot\secreto.cmd bot\config.json bot\maker_estado_real.json bot\maker_ops_real.csv root@IP:/root/migrar/
   ```
3. En el servidor: `maker-pasar_de_la_pc`. Pide confirmar que la PC está apagada, pasa las claves a
   `/etc/polymarket-maker/secreto.env` (solo root lo puede leer), borra la copia de `secreto.cmd`, revisa el
   inventario contra la cuenta y arranca. Llega "Maker (real) arrancó" al celular.
4. **No volver a abrir `iniciar_maker.cmd` en la PC**: dos bots con la misma cuenta se cancelan las órdenes entre sí.

## Uso diario (dentro del servidor)

| Para | Comando |
|---|---|
| ver cómo anda | `maker-estado` |
| apagarlo (cancela órdenes; no vuelve solo) | `maker-parar` |
| volver a prenderlo | `rm /home/bot/polymarket-clima/bot/PARAR && systemctl start polymarket-maker` |
| traer cambios de main | `maker-actualizar` |
| ver el registro en vivo | `journalctl -u polymarket-maker -f` |

El servicio arranca solo si el servidor se reinicia y vuelve a arrancar a los 60 s si el bot se cae con error, igual que
`iniciar_maker.cmd`. Si el bot se frena por un freno (pérdida, fecha, `PARAR`) queda apagado hasta que lo prendas.

## Volver a la PC

`maker-parar` en el servidor, copiar `bot/maker_estado_real.json` y `bot/maker_ops_real.csv` a la PC con `scp`
(al revés que arriba) y abrir `iniciar_maker.cmd`. El bot igual reconstruye el inventario desde los trades del CLOB.
