import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import pytz

from huawei_solar import create_tcp_client, SUN2000Device
from huawei_solar.register_names import (
    INPUT_POWER,
    ACTIVE_POWER,
    POWER_METER_ACTIVE_POWER,
)


# IP local del inversor
HOST = "192.168.0.111"


async def fetch_inverter_data():
    """Función async que lee datos del inversor."""
    client = create_tcp_client(host=HOST)
    try:
        device = SUN2000Device(client, "SUN2000")
        input_power = await device.get(INPUT_POWER)
        active_power = await device.get(ACTIVE_POWER)
        power_meter_active_power = await device.get(POWER_METER_ACTIVE_POWER)

        # Consumo neto = generación - exportación
        energy_consumption = active_power.value - power_meter_active_power.value

        # Hora local de España
        tz_ES = pytz.timezone("Europe/Madrid")
        datetime_ES = datetime.now(tz_ES)

        return {
            "input_power": input_power.value,
            "active_power": active_power.value,
            "power_meter_active_power": power_meter_active_power.value,
            "energy_consumption": energy_consumption,
            "datetime_ES": datetime_ES,
        }
    except Exception as e:
        print(f"Error al leer el inversor: {e}")
        return None
    finally:
        await client.disconnect()


# Dirección y puerto del servidor web (solo accesible desde este equipo)
hostName = "localhost"
serverPort = 8081


class MyServer(BaseHTTPRequestHandler):
    """Manejador HTTP que sirve una página con datos del inversor."""

    def do_GET(self):
        # Obtener datos del inversor para esta petición
        data = asyncio.run(fetch_inverter_data())

        self.send_response(503 if data is None else 200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        if data is None:
            self.wfile.write(bytes(
                "<html><head><title>Huawei Solar - Error</title>"
                "<meta http-equiv='refresh' content='10' /></head>",
                "utf-8"
            ))
            self.wfile.write(bytes(
                "<body><p>Error al leer el inversor. Verifica la conexión.</p></body></html>",
                "utf-8"
            ))
        else:
            # Formato de fecha/hora
            date_str = data["datetime_ES"].strftime("%d/%m/%Y")
            time_str = data["datetime_ES"].strftime("%H:%M:%S")

            self.wfile.write(bytes("<html><head><title>Huawei Solar inverter Data</title>", "utf-8"))
            self.wfile.write(bytes("<meta http-equiv='refresh' content='10' />", "utf-8"))
            self.wfile.write(bytes("</head>", "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes(f"<p>Input energy (registered by panels): {data['input_power']} W</p>", "utf-8"))
            self.wfile.write(bytes(f"<p>Active energy (ready to be taken): {data['active_power']} W</p>", "utf-8"))
            self.wfile.write(bytes(f"<p>Exported energy (discharged to be compensated): {data['power_meter_active_power']} W</p>", "utf-8"))
            self.wfile.write(bytes(f"<p>Energy consumption currently: {data['energy_consumption']} W</p>", "utf-8"))
            self.wfile.write(bytes(f"<p>Date: {date_str}</p>", "utf-8"))
            self.wfile.write(bytes(f"<p>Time: {time_str}</p>", "utf-8"))
            self.wfile.write(bytes(f"<p>Timezone: Europe/Madrid</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))

    # Evitar logs de petición cada línea en la consola
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    finally:
        webServer.server_close()
    print("Server stopped.")
