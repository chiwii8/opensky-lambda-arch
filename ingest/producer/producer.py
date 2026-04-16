import json 
import time
import requests
import os
from confluent_kafka import Producer


TOPIC_NAME = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER = os.getenv('KAFKA_BROKER')
# Credenciales
OPENSKY_USER = os.getenv('OPENSKY_USER')
OPENSKY_SECRET = os.getenv('OPENSKY_SECRET')

OPENSKY_TOKEN_URL= 'https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token'
OPENSKY_URI= os.getenv('OPENSKY_URI')   # Esta URL es la Base, se requiere añadir la operación que se quiere hacer
OPENSKY_EXT = 'states/all'


# Valores de la región objetivo( Por defecto España)
lamin = os.getenv('LAMIN', '35.0')
lomin = os.getenv('LOMIN', '-10.0')
lamax = os.getenv('LAMAX', '44.0')
lomax = os.getenv('LOMAX', '5.0')

# Región objetivo
REGION_PARAMS = f"?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

# Creamos el producer
producer = Producer({
    "bootstrap.servers": KAFKA_BROKER
})
current_token = None


def get_token():
    """Obtiene un token usando las credenciales"""
    global current_token
    try:
        data = {
            'grant_type': 'client_credentials',
            'client_id': OPENSKY_USER,
            'client_secret': OPENSKY_SECRET
        }
        response = requests.post(OPENSKY_TOKEN_URL,data=data, timeout=10)
        response.raise_for_status()
        current_token = response.json().get('access_token')
        print("Nuevo token obtenido")
        return current_token
    except Exception as e:
        print(f"Error obteniendo el token: {e}")
        return None


def delivery_report(err, msg):
    """ Callback opcional para confirmar que el mensaje llegó """
    if err is not None:
        print(f"Error al entregar mensaje: {err}")

def fetch_flights():
    global current_token
    if not current_token:
        if not get_token():
            return  # Salimos si falla conseguir el token

    headers = {
        'Authorization': f'Bearer {current_token}',
        'Accept': 'application/json'
    }

    try:

        # Dependiendo de los datos que queremos usamos una terminación diferente
        OPENSKY_URL = f"{OPENSKY_URI}/{OPENSKY_EXT}"
        response = requests.get(f"{OPENSKY_URL}{REGION_PARAMS}", headers=headers, timeout=15)

        if response.status_code == 401:
            print("El token ha caducado, renovando ...")
            current_token = None
            get_token()
            return fetch_flights()  # Volvemos a intentar


        if response.status_code != 200:
            print(f"Error de API: {response.status_code} - {response.text[:50]}")
            return
        

        data = response.json()

        if 'states' in data and data['states']:
            for s in data['states']:
                flight_data = {
                    "icao24": s[0],
                    "callsign": s[1].strip() if s[1] else "N/A",
                    "origin_country": s[2],
                    "timestamp": s[3],
                    "longitude": s[5],
                    "latitude": s[6],
                    "altitude": s[7],
                    "on_ground": s[8],
                    "velocity": s[9]
                }
                
                # Enviamos a Kafka
                producer.produce(
                    TOPIC_NAME, 
                    value=json.dumps(flight_data).encode('utf-8'),
                    callback=delivery_report
                )
            # Nos Aseguramos de que los mensajes se envían antes de llenar el buffer
            producer.flush()

            # Escribimos el número de vuelos que se ha enviado a kafka    
            print(f"Enviados {len(data['states'])} vuelos a Kafka.")
        else:
            print("No hay vuelos en la región en este momento.")
    except ValueError as e:
        print(f"Error parseando JSON: {e}. Contenido recibido: {response.text[:100]}")
    except Exception as e:
        print(f"Error: {e}") 




if __name__ == "__main__":
    while True:
        try:
            fetch_flights()
            
            # 25 segundos garantiza funcionamiento infinito con 4000 créditos/día
            time.sleep(25) 
            
        except Exception as e:
            print(f"Error crítico en el bucle: {e}")
            # Si hay un error de red, esperamos un minuto antes de reintentar
            time.sleep(60)