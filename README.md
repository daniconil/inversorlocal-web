# inversorlocal-web

Lectura local de un inversor Huawei fotovoltaico y visualización de su potencia instantánea en una página web. No necesita acceder a FusionSolar.

## Requisitos

- Python **3.12 o superior**.
- Un inversor Huawei accesible desde el equipo por la red local, con Modbus TCP habilitado. La configuración predeterminada de la biblioteca usa el puerto **502**.
- Acceso al registro del medidor de potencia para calcular el intercambio con la red y el consumo.

## 1. Preparar el entorno

En Debian/Ubuntu, instala Python y las herramientas del entorno virtual:

```bash
sudo apt update
sudo apt install git python3 python3-pip python3-venv
python3 --version
```

Si la versión instalada es inferior a 3.12, instala una versión compatible antes de continuar.

Clona el repositorio si aún no lo tienes:

```bash
git clone https://github.com/daniconil/inversorlocal-web.git
cd inversorlocal-web
```

Si ya está clonado, entra en su directorio. Crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "huawei-solar>=3.0.7,<4" pytz
```

`huawei-solar` instala automáticamente sus dependencias de comunicación. `pytz` se utiliza para mostrar la hora en `Europe/Madrid`.

## 2. Configurar el inversor

Edita **`main.py`**:

```bash
nano main.py
```

La IP está configurada para esta instalación:

```python
HOST = "192.168.0.111"
```

Cámbiala si tu inversor tiene otra dirección. No confundas esta IP con la dirección del servidor web:

```python
hostName = "localhost"
serverPort = 8081
```

Por defecto, la web solo es accesible desde el equipo donde se ejecuta. Si cambias `hostName` a `"0.0.0.0"`, podrás acceder desde otros equipos de tu red usando `http://IP_DEL_EQUIPO:8081`. El servidor no tiene autenticación ni HTTPS: úsalo únicamente en una red de confianza y no lo expongas a Internet.

## 3. Ejecutar y probar

Con el entorno virtual activado:

```bash
python main.py
```

Aparecerá:

```text
Server started http://localhost:8081
```

Abre **http://localhost:8081** en el navegador y deja la terminal abierta. La página se recarga cada **10 segundos**; cada petición lee datos nuevos mediante la API asíncrona de `huawei-solar` y cierra la conexión con el inversor al terminar.

También puedes comprobar la respuesta desde otra terminal:

```bash
curl -i http://localhost:8081/
```

Una lectura correcta devuelve **HTTP 200**. Si falla la lectura, devuelve **HTTP 503**, muestra un aviso en la página y registra el detalle en la terminal. La página de error también reintenta cada 10 segundos.

Para detenerlo, pulsa **Ctrl+C**. En futuras ejecuciones basta con:

```bash
cd /ruta/a/inversorlocal-web
source .venv/bin/activate
python main.py
```

## Datos mostrados

Los valores están en **W (potencia instantánea)**, no en Wh o kWh (energía acumulada). Los rótulos de la página se mantienen en inglés:

| Rótulo | Significado |
|---|---|
| Input energy | Potencia captada por los paneles, lado de corriente continua. |
| Active energy | Potencia activa generada por el inversor. |
| Exported energy | Intercambio con la red: positivo al exportar y negativo al importar, con el medidor instalado correctamente. |
| Energy consumption currently | Consumo estimado: potencia generada menos intercambio con la red. |
| Date / Time / Timezone | Fecha, hora y zona horaria de la lectura. |

Por ejemplo: generación de **911 W** e intercambio de **−221 W** (importación) dan un consumo estimado de **1132 W**. El cálculo puede no representar todo el consumo en instalaciones con baterías u otros generadores.

## Problemas frecuentes

- **Error al leer el inversor:** comprueba que esté encendido, la IP, la conectividad, el puerto Modbus TCP y su habilitación en el inversor/dongle. Algunas instalaciones limitan las conexiones simultáneas; evita otros lectores durante la prueba.
- **Address already in use:** ya hay un servidor usando el puerto 8081. Usa el que está ejecutándose, detén tu instancia anterior o cambia `serverPort`.
- **ModuleNotFoundError:** activa `.venv` e instala las dependencias dentro de ese entorno.
- **No aparecen datos nuevos:** mantén el proceso activo y espera la recarga; si hay un error, consulta la terminal.

La implementación usa `create_tcp_client`, `SUN2000Device` y `await device.get(...)`; no utiliza la antigua interfaz síncrona `HuaweiSolar` ni `importlib.reload`.

Más información: [huawei-solar](https://pypi.org/project/huawei-solar/) y [pytz](https://pypi.org/project/pytz/).
