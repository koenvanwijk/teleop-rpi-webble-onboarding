# TeleOp RPi WebBLE Onboarding

Provisioneer Wi‑Fi op een Raspberry Pi via **Bluetooth Low Energy** met een **webpagina** (Web Bluetooth, geen app nodig) + **QR‑code** beveiliging.  
Gemaakt voor headless onboarding met korte BLE‑window (5 min), en **teleop-<suffix>** hostname.

## Features
- Webpagina (`web/index.html`) gebruikt **Web Bluetooth** om te verbinden met de Pi en SSID/wachtwoord te sturen.
- **Setup token** vereist (QR op onderkant). Zonder geldige token accepteert de Pi geen commando’s.
- BLE blijft **5 minuten** actief na boot. Blijft actief als er geen Wi‑Fi is of bij mislukte verbinding.
- Schrijft **/etc/wpa_supplicant/wpa_supplicant.conf** (of gebruikt NetworkManager als aanwezig).
- **Unique hostname**: `teleop-<last6-mac>` bij eerste boot.
- Scripts om **image overlay** te maken (kopieer files naar `/boot` en rootfs), en **QR‑codes te genereren**.

## Snel starten (Raspberry Pi OS Lite aanbevolen)
1. Flash een SD‑kaart met Raspberry Pi Imager.
2. Mount de **boot** partitie en kopieer de map `firmware/boot/` inhoud naar de SD `boot/` (zie _Image overlay_).
3. Plaats de SD in de Pi en start op met internet **nog niet** geconfigureerd.
4. Binnen 5 minuten: scan de QR‑code, open de webpagina, kies SSID en vul Wi‑Fi wachtwoord in.
5. Check status en IP in de UI. Na succes wordt BLE uitgezet (tenzij je dit wijzigt in config).

## Web UI hosten
De webpagina moet over **HTTPS** geladen worden (vereiste van Web Bluetooth).
- Gebruik GitHub Pages of een eigen webserver met HTTPS.
- Of open `web/index.html` lokaal op je **telefoon/laptop** via `file://` in Chrome (soms toegestaan), maar HTTPS is betrouwbaarder.

## Projectstructuur
```
.
├── LICENSE
├── SECURITY.md
├── README.md
├── config/
│   ├── onboarding.env.example
│   └── wpa_supplicant.template
├── firmware/
│   ├── boot/
│   │   ├── onboarding.env              # kopie naar /boot
│   │   └── firstboot.flag              # triggert eenmalige setup
│   ├── systemd/
│   │   ├── ble_onboard.service
│   │   └── firstboot.service
│   └── scripts/
│       ├── ble_onboard.py
│       ├── wifi_config.py
│       ├── gen_hostname.sh
│       ├── provision_token.sh
│       └── scan_wifi.sh
├── setup/
│   ├── install_deps.sh
│   └── enable_services.sh
├── tools/
│   ├── make_image_overlays.sh
│   └── gen_qr.py
└── web/
    ├── index.html
    └── app.js
```

## Image overlay
- **Boot overlay:** kopieer `firmware/boot/*` naar de **boot** partitie van je SD-kaart (FAT).
- **Root overlay:** na eerste boot:
  ```bash
  sudo ./setup/install_deps.sh
  sudo ./setup/enable_services.sh
  ```

Wil je alles in één keer op de kaart plaatsen (bijv. chroot of Pi aan USB)? Gebruik `tools/make_image_overlays.sh` (zie comments in script).

## Configuratie
- `config/onboarding.env.example` → kopieer naar `firmware/boot/onboarding.env` en vul:
  - `SETUP_TOKEN=...` (uniek, random)
  - `BLE_WINDOW_SECONDS=300`
  - `KEEP_BLE_IF_NO_WIFI=1`
  - `BRAND_PREFIX=teleop`
- `config/wpa_supplicant.template` → basis voor wpa_supplicant als NetworkManager niet aanwezig is.

## QR‑code genereren
Genereer per device een QR met token + link naar de Web UI:
```bash
python3 tools/gen_qr.py --token <YOUR_TOKEN> --url https://your-domain/setup
# Output: qrcodes/teleop-<token>.png (sticker)
```
Plak deze sticker op de onderzijde van de Pi-case.

## Werking
1. `firstboot.service` zet hostname `teleop-<last6-mac>`, verplaatst configs van `/boot` naar `/etc/teleop/`, en activeert `ble_onboard.service`.
2. `ble_onboard.py` start een GATT-server (BlueZ D-Bus) met service/characteristics:
   - **Token**: verification write
   - **Command**: `"scan" | "connect" | "status"`
   - **SSID** + **PASS**
   - **Response**: JSON resultaat
3. Web UI (HTTPS) maakt via Web Bluetooth verbinding en voert het protocol uit.
4. Bij `"connect"` wordt `wifi_config.py` aangeroepen → schrijft config en herstart wpa_supplicant/NetworkManager.

## Dependencies (Pi)
- BlueZ + dbus, Python 3: `dbus-next`, `PyGObject` (voor systemctl/wifi scripts niet noodzakelijk), `qrencode` (optioneel).
- Zie `setup/install_deps.sh`.

## Browser support
- Web Bluetooth werkt goed in Chrome/Edge op Android en desktop.
- iOS/iPadOS: beperkt of experimenteel. Alternatief: gebruik nRF Connect app om characteristics te schrijven (dev/test).

## Beveiliging
- Zonder **juiste token** accepteert de Pi geen provisioning-commando's.
- Rotatie: wijzig `SETUP_TOKEN` en hergenereer QR.
- Verkort de BLE-window of vereis pairing met passkey voor extra bescherming (BlueZ config).

---

> Tip: Wil je dat BLE ook later **op aanvraag** weer aan kan (na de 5 min)? Laat `ble_onboard.service` enabled en start via fysieke knop of GPIO-trigger (uit te breiden in `ble_onboard.py`).

