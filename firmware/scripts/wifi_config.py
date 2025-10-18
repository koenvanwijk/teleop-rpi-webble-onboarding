#!/usr/bin/env python3
import os, subprocess, sys, json, pathlib

def nmcli_available():
    return subprocess.call(["bash","-lc","command -v nmcli >/dev/null 2>&1"]) == 0

def write_wpa(SSID, PSK):
    template = pathlib.Path("/usr/local/teleop/wpa_supplicant.template")
    if not template.exists():
        template = pathlib.Path("/etc/teleop/wpa_supplicant.template")
    if not template.exists():
        template = pathlib.Path("/usr/local/teleop/../config/wpa_supplicant.template")
    if not template.exists():
        # fallback minimal
        content = f'ctrl_interface=DIR=/run/wpa_supplicant GROUP=netdev\nupdate_config=1\nnetwork={{\n ssid="{SSID}"\n psk="{PSK}"\n}}\n'
    else:
        t = template.read_text()
        content = t.replace("{SSID}", SSID).replace("{PSK}", PSK)
    pathlib.Path("/etc/wpa_supplicant/wpa_supplicant.conf").write_text(content)
    subprocess.run(["systemctl","restart","wpa_supplicant"], check=False)

def configure_wifi(ssid, psk):
    if nmcli_available():
        subprocess.run(["nmcli","dev","wifi","connect", ssid, "password", psk], check=False)
    else:
        write_wpa(ssid, psk)

def status():
    ip = subprocess.getoutput("hostname -I | awk '{print $1}'")
    ssid = subprocess.getoutput("iwgetid -r || nmcli -t -f active,ssid dev wifi | awk -F: '/^yes:/{print $2; exit}'")
    return {"ip": ip.strip(), "ssid": ssid.strip()}

def main():
    data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    cmd = data.get("cmd")
    if cmd == "connect":
        configure_wifi(data["ssid"], data["psk"])
        print(json.dumps({"ok": True, "status": status()}))
    elif cmd == "status":
        print(json.dumps({"ok": True, "status": status()}))
    else:
        print(json.dumps({"ok": False, "error": "unknown"}))

if __name__ == "__main__":
    main()
