import socket
from wifi_config import save_config

def start_config_server():
    html = """\
HTTP/1.0 200 OK

<!DOCTYPE html>
<html>
  <head><title>Wi-Fi Setup</title></head>
  <body>
    <h2>Configure Wi-Fi</h2>
    <form method="GET">
      SSID: <input name="ssid"><br>
      Password: <input name="password" type="password"><br>
      <input type="submit">
    </form>
  </body>
</html>
"""

    s = socket.socket()
    s.bind(('', 80))
    s.listen(1)
    print("Web server started on port 80")

    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        req = conn.recv(1024).decode()
        if "ssid=" in req:
            try:
                ssid = req.split("ssid=")[1].split("&")[0]
                password = req.split("password=")[1].split(" ")[0]
                ssid = ssid.replace('+', ' ')
                password = password.replace('+', ' ')
                save_config(ssid, password)
                conn.send("HTTP/1.0 200 OK\r\n\r\nSaved. Rebooting...")
                conn.close()
                time.sleep(2)
                import machine
                machine.reset()
            except:
                pass
        else:
            conn.sendall(html)
        conn.close()
