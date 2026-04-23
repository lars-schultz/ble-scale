import asyncio
import requests
import json
import time
import sys

from bleak import BleakScanner, BleakClient

ARBOLEAF_NAME = "QN-KS"
ARBOLEAF_STATE = "0000fff1-0000-1000-8000-00805f9b34fb"

UNITS = {
    "01": "g",
    "02": "ml",
    "04": "Milk",
    "08": "fl.oz",
    "10": "lb.oz",
}

LOGGER_URL = sys.argv[1]
if ( not LOGGER_URL ):
    print("Logger URL required");
    sys.exit(1)

LOGGER_SOURCE = sys.argv[2]
if ( not LOGGER_SOURCE ):
    print("Logger Source required");
    sys.exit(1)

previousMessage = -1;
logdata = {"source":LOGGER_SOURCE,"data":{"status":"off"}}

def split_fixed_hex(hex_str: str):
    return hex_str[0:14], hex_str[14:16], hex_str[16:18], hex_str[18:22], hex_str[22:34], hex_str[34:36]

def hex_segment_to_int(hex_segment: str) -> int:
    return int(hex_segment, 16)

def notification_handler(sender, data):
    global previousMessage,logdata

    message = data.hex()

    if previousMessage == message:
        return

    previousMessage = message;

    if len(message) != 36:
        print(f"Unknown message {message}")
        return

    p1, unit, flags, value, p5, p6 = split_fixed_hex(message)

    value = hex_segment_to_int(value)
    flags = hex_segment_to_int(flags)

    tenth = bool(flags & 16)

    if tenth:
        value = value / 10;

    stable = bool(flags & 8)
    negative = bool(flags & 2)
    tara = bool(flags & 1)

    unit = UNITS.get(unit,unit);

    print(f"{message} Einheit {unit} / stable {stable} tenth {tenth}  negative {negative} tara {tara} Wert {value}")

    logdata['data']['unit'] = unit
    logdata['data']['value'] = value if not negative else -value
    logdata['data']['stable'] = stable
    logdata['data']['negative'] = negative
    logdata['data']['tara'] = tara
    
    update()

def update(status=''):
    global logdata

    if ( status ):
        logdata['data']['status'] = status;

    logdata['data']['time'] = int(time.time())

    post_json(LOGGER_URL,logdata)

def post_json(url: str, payload: dict) -> None:
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

    if response.ok:
        print(f"sent {payload["data"]["status"]}")
    else:
        print(f"received: {response.status_code}: {response.text} JSON {json.dumps(payload)}")

async def find_device_by_name(name: str):
    print(f"🔎 Starte Scan (≈ 5 s)…")
    update('scanning')
    
    devices = await BleakScanner.discover(timeout=5.0)

    for d in devices:
        if d.name and d.name == name:
            print(f"✅ Gefunden: {d.name} [{d.address}]")
            return d

    print(f"❌ Kein Gerät mit Namen '{name}' gefunden.")
    return None

async def main():
    global logdata

    update('running')

    while True:
        try:
            device = await find_device_by_name(ARBOLEAF_NAME)

            if ( device == None ): continue

            logdata["data"]["device"] = device.address;
            update('connecting')

            async with BleakClient(device) as client:
                if not client.is_connected:
                    update('connection failed')
                    print("❌ Verbindung fehlgeschlagen – retry in 5 s")
                    await asyncio.sleep(5)
                    continue   # zurück nach außen in die while‑True‑Schleife

                print("✅ Verbunden – starte Benachrichtigungen")

                update('connected')

                await client.start_notify(ARBOLEAF_STATE, notification_handler)

                try:
                    while client.is_connected:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    # Wird ausgelöst, wenn das äußere `asyncio.run` das Event‑Loop
                    # abschaltet (z. B. bei KeyboardInterrupt)
                    pass
                finally:
                    await client.stop_notify(ARBOLEAF_STATE)
                    print("🔌 Benachrichtigungen gestoppt")
        except Exception as exc:
            print(f"🚨 Ausnahme: {exc!r}")
            print("🔄 Versuche in 5 s erneut zu verbinden …")
            update('reconnecting')
            await asyncio.sleep(5)   # kurze Pause, bevor wir es nochmal probieren
        finally:
            # Wenn wir hier landen, ist die Verbindung geschlossen.
            # Die äußere while‑True‑Schleife sorgt dafür, dass wir es erneut versuchen.
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        update("interrupted")
        print("\n👋 Benutzer hat das Programm mit Ctrl‑C beendet.")