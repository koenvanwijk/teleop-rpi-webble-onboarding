#!/usr/bin/env python3
# Minimal BlueZ GATT Server with dbus-next for Web Bluetooth provisioning
import asyncio, os, json, time, subprocess, signal
from dbus_next.aio import MessageBus
from dbus_next import Variant
from dbus_next.service import (ServiceInterface, method, dbus_property, PropertyAccess)
from dbus_next.constants import PropertyAccess

SERVICE_UUID = "12345678-1234-5678-1234-56789abc0000"
CHAR_TOKEN_UUID = "12345678-1234-5678-1234-56789abc0001"
CHAR_CMD_UUID   = "12345678-1234-5678-1234-56789abc0002"
CHAR_SSID_UUID  = "12345678-1234-5678-1234-56789abc0003"
CHAR_PASS_UUID  = "12345678-1234-5678-1234-56789abc0004"
CHAR_RESP_UUID  = "12345678-1234-5678-1234-56789abc0005"

SETUP_TOKEN = os.getenv("SETUP_TOKEN","")
BLE_WINDOW_SECONDS = int(os.getenv("BLE_WINDOW_SECONDS","300"))
KEEP_BLE_IF_NO_WIFI = os.getenv("KEEP_BLE_IF_NO_WIFI","1") == "1"

authorized = False
state = {"ssid":"", "pass":"", "resp":"{}"}

def log(*a):
    print("[ble]", *a, flush=True)

class Application(ServiceInterface):
    def __init__(self, path):
        super().__init__('org.bluez.GattApplication1')
        self.path = path

class Service(ServiceInterface):
    def __init__(self, path, uuid, primary=True):
        super().__init__('org.bluez.GattService1')
        self.path = path
        self.uuid = uuid
        self.primary = primary

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> 's':
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> 'b':
        return self.primary

class Characteristic(ServiceInterface):
    def __init__(self, path, uuid, flags):
        super().__init__('org.bluez.GattCharacteristic1')
        self.path = path
        self.uuid = uuid
        self.flags = flags
        self.value = bytearray()

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> 's':
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> 'as':
        return self.flags

    @method()
    def ReadValue(self, options: 'a{sv}') -> 'ay':
        return self.value

    @method()
    def WriteValue(self, value: 'ay', options: 'a{sv}'):
        self.value = bytearray(value)

class TokenChar(Characteristic):
    def __init__(self, path):
        super().__init__(path, CHAR_TOKEN_UUID, ["write"])

    @method()
    def WriteValue(self, value: 'ay', options: 'a{sv}'):
        global authorized
        token = bytes(value).decode('utf-8').strip()
        authorized = (token == SETUP_TOKEN)
        log("token write", "OK" if authorized else "BAD")
        self.value = bytearray()

class SSIDChar(Characteristic):
    def __init__(self, path):
        super().__init__(path, CHAR_SSID_UUID, ["write"])

    @method()
    def WriteValue(self, value: 'ay', options: 'a{sv}'):
        state["ssid"] = bytes(value).decode('utf-8')
        self.value = bytearray()

class PassChar(Characteristic):
    def __init__(self, path):
        super().__init__(path, CHAR_PASS_UUID, ["write"])

    @method()
    def WriteValue(self, value: 'ay', options: 'a{sv}'):
        state["pass"] = bytes(value).decode('utf-8')
        self.value = bytearray()

class RespChar(Characteristic):
    def __init__(self, path):
        super().__init__(path, CHAR_RESP_UUID, ["read","notify"])
        self.notifying = False

    @method()
    def ReadValue(self, options: 'a{sv}') -> 'ay':
        return bytearray(state["resp"].encode())

class CmdChar(Characteristic):
    def __init__(self, path):
        super().__init__(path, CHAR_CMD_UUID, ["write"])

    @method()
    def WriteValue(self, value: 'ay', options: 'a{sv}'):
        if not authorized:
            state["resp"] = json.dumps({"ok":False, "error":"unauthorized"})
            return
        cmd = bytes(value).decode('utf-8').strip()
        if cmd == "scan":
            # naive scan using script
            try:
                out = subprocess.check_output(["/usr/local/teleop/scan_wifi.sh"]).decode()
                state["resp"] = json.dumps({"ok":True, "ssids": json.loads(out)})
            except Exception as e:
                state["resp"] = json.dumps({"ok":False, "error":str(e)})
        elif cmd == "connect":
            try:
                payload = {"cmd":"connect", "ssid":state["ssid"], "psk":state["pass"]}
                out = subprocess.check_output(["/usr/bin/python3","/usr/local/teleop/wifi_config.py"],input=json.dumps(payload).encode())
                state["resp"] = out.decode()
            except Exception as e:
                state["resp"] = json.dumps({"ok":False, "error":str(e)})
        elif cmd == "status":
            try:
                payload = {"cmd":"status"}
                out = subprocess.check_output(["/usr/bin/python3","/usr/local/teleop/wifi_config.py"],input=json.dumps(payload).encode())
                state["resp"] = out.decode()
            except Exception as e:
                state["resp"] = json.dumps({"ok":False, "error":str(e)})
        else:
            state["resp"] = json.dumps({"ok":False, "error":"unknown cmd"})

async def setup_gatt(bus):
    # Use BlueZ example object manager layout
    om = await bus.introspect('org.bluez', '/org/bluez')
    # Register app via experimental interface
    app_path = '/org/bluez/example/app'
    srv_path = '/org/bluez/example/service0'
    ch_paths = {
        "token": "/org/bluez/example/service0/char0",
        "cmd":   "/org/bluez/example/service0/char1",
        "ssid":  "/org/bluez/example/service0/char2",
        "pass":  "/org/bluez/example/service0/char3",
        "resp":  "/org/bluez/example/service0/char4",
    }

    bus.export(app_path, Application(app_path))
    service = Service(srv_path, SERVICE_UUID, True)
    bus.export(srv_path, service)
    bus.export(ch_paths["token"], TokenChar(ch_paths["token"]))
    bus.export(ch_paths["cmd"],   CmdChar(ch_paths["cmd"]))
    bus.export(ch_paths["ssid"],  SSIDChar(ch_paths["ssid"]))
    bus.export(ch_paths["pass"],  PassChar(ch_paths["pass"]))
    bus.export(ch_paths["resp"],  RespChar(ch_paths["resp"]))

    mngr = await bus.get_proxy_object('org.bluez', '/', None)
    gatt = await bus.get_proxy_object('org.bluez', '/org/bluez/hci0', None)
    gatt_mngr = (await bus.get_proxy_object('org.bluez','/org/bluez/hci0','org.bluez.GattManager1')).get_interface('org.bluez.GattManager1')
    ad_mngr = (await bus.get_proxy_object('org.bluez','/org/bluez/hci0','org.bluez.LEAdvertisingManager1')).get_interface('org.bluez.LEAdvertisingManager1')

    class Advertisement(ServiceInterface):
        def __init__(self, path, adv_type):
            super().__init__('org.bluez.LEAdvertisement1')
            self.path = path
            self.adv_type = adv_type
        @dbus_property(access=PropertyAccess.READ)
        def Type(self) -> 's':
            return self.adv_type
        @dbus_property(access=PropertyAccess.READ)
        def ServiceUUIDs(self) -> 'as':
            return [SERVICE_UUID]
        @dbus_property(access=PropertyAccess.READ)
        def LocalName(self) -> 's':
            return os.uname().nodename[:29]
        @dbus_property(access=PropertyAccess.READ)
        def Includes(self) -> 'as':
            return ["tx-power"]
        @method()
        def Release(self):
            pass

    adv_path = '/org/bluez/example/advertisement0'
    adv = Advertisement(adv_path, "peripheral")
    bus.export(adv_path, adv)

    await gatt_mngr.call_register_application(app_path, {})
    await ad_mngr.call_register_advertisement(adv_path, {})
    log("GATT service + advertising registered.")

async def main():
    # power on adapter
    subprocess.run(["rfkill","unblock","bluetooth"], check=False)
    subprocess.run(["hciconfig","hci0","up"], check=False)

    bus = await MessageBus().connect()
    await setup_gatt(bus)

    deadline = time.time() + BLE_WINDOW_SECONDS
    while True:
        await asyncio.sleep(2)
        # Auto stop after window if Wi‑Fi is up (or keep if configured)
        if time.time() > deadline:
            ip = subprocess.getoutput("hostname -I | awk '{print $1}'").strip()
            if ip and not KEEP_BLE_IF_NO_WIFI:
                log("Window elapsed, IP present, exiting.")
                os.kill(os.getpid(), signal.SIGTERM)
                break
            elif not ip:
                log("No Wi‑Fi yet; keep advertising.")
            else:
                log("Window elapsed but KEEP_BLE_IF_NO_WIFI=1; keep running.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
