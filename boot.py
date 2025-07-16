import time
import network
import machine
import webrepl
from wifi_config import load_config

# === Constants ===
AP_SSID = "TempSensor"
AP_PASSWORD = "password"  # At least 8 characters
HOSTNAME = "temp-sensor"

# === Optional: mDNS support if already installed ===
def start_mdns(hostname):
    try:
        from mdns_client import MDNS
        mdns = MDNS(hostname)
        print(f"mDNS started as {hostname}.local")
    except ImportError:
        print("mDNS not available: mdns_client not installed.")
    except Exception as e:
        print("Failed to start mDNS:", e)

# === Connect to Wi-Fi ===
def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()  # Clear previous state
    wlan.config(pm=0)  # Disable power save
    wlan.config(dhcp_hostname=HOSTNAME)

    print(f"Connecting to SSID: {ssid}")
    try:
        wlan.connect(ssid, password)
    except Exception as e:
        print("Initial connect error:", e)
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        wlan.connect(ssid, password)

    start = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
            print("Wi-Fi connection timeout.")
            return None
        time.sleep(0.5)

    print("Connected. IP:", wlan.ifconfig()[0])
    return wlan

# === Start Access Point with fallback config server ===
def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)
    print(f"Started AP mode: {AP_SSID}")
    print("AP IP address:", ap.ifconfig()[0])
    try:
        import wifi_web
        wifi_web.start_config_server()
    except Exception as e:
        print("Web config error:", e)
    return ap

# === Boot Logic ===

cfg = load_config()
if cfg and "ssid" in cfg and "password" in cfg:
    sta = connect_wifi(cfg["ssid"], cfg["password"])
    if sta and sta.isconnected():
        ap = network.WLAN(network.AP_IF)
        ap.active(False)
        start_mdns(HOSTNAME)
    else:
        start_ap()
        start_mdns(HOSTNAME)
else:
    print("No Wi-Fi config found.")
    start_ap()
    start_mdns(HOSTNAME)

# === WebREPL ===
try:
    webrepl.start()
    print("WebREPL started.")
except Exception as e:
    print("WebREPL error:", e)

# === Keep REPL alive ===
machine.freq()
