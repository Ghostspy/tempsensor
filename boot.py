import time
import network
import machine
import webrepl
from wifi_config import load_config

# === Constants ===
AP_SSID = "TempSensor"
AP_PASSWORD = "password"  # 8+ characters
HOSTNAME = "temp-sensor"

def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(dhcp_hostname=HOSTNAME)

    if wlan.isconnected():
        print("Already connected. IP:", wlan.ifconfig()[0])
        return wlan

    try:
        print(f"Connecting to SSID: {ssid}")
        wlan.connect(ssid, password)
    except OSError as e:
        print("Wi-Fi connect error:", e)
        # Reset interface and retry once
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        try:
            wlan.connect(ssid, password)
        except OSError as e2:
            print("Second connect attempt failed:", e2)
            return None

    start = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
            print("Wi-Fi connection timeout.")
            return None
        time.sleep(0.5)

    print("Connected. IP address:", wlan.ifconfig()[0])
    return wlan


def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)
    print(f"Started AP mode: {AP_SSID}")
    print("AP IP address:", ap.ifconfig()[0])
    return ap

def ensure_mdns_installed():
    try:
        import mdns_client
    except ImportError:
        import mip
        mip.install("github:cbrand/micropython-mdns")
        import machine
        print("mDNS installed. Rebooting...")
        machine.reset()

# Call here to install if missing
ensure_mdns_installed()

def start_mdns(hostname):
    try:
        from mdns_client import MDNS
        mdns = MDNS(hostname)
        print(f"mDNS started as {hostname}.local")
    except ImportError:
        print("mDNS not available: mdns_client not installed.")
    except Exception as e:
        print("Failed to start mDNS:", e)

# === Main Logic ===

cfg = load_config()

if cfg and "ssid" in cfg and "password" in cfg:
    sta = connect_wifi(cfg["ssid"], cfg["password"])
    if sta and sta.isconnected():
        start_mdns(HOSTNAME)
    else:
        ap = start_ap()
        start_mdns(HOSTNAME)
        try:
            import wifi_web
            wifi_web.start_config_server()
        except Exception as e:
            print("Web config error:", e)
else:
    ap = start_ap()
    start_mdns(HOSTNAME)
    try:
        import wifi_web
        wifi_web.start_config_server()
    except Exception as e:
        print("Web config error:", e)

# === WebREPL ===
try:
    webrepl.start()
    print("WebREPL started.")
except Exception as e:
    print("WebREPL error:", e)

# Keep REPL alive
machine.freq()
