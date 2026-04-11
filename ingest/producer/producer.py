import json 
import time
import requests
import os
from confluent_kafka import Producer


TOPIC_NAME = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER = os.getenv('KAFKA_BROKER')
OPENSKY_URI= os.getenv('OPENSKY_URI')   # Esta URL es la Base, se requiere añadir la operación que se quiere hacer
OPENSKY_EXT = 'states/all'

# Creamos el producer
producer = Producer({
    "bootstrap.servers": KAFKA_BROKER
})


def delivery_report(err, msg):
    """ Callback opcional para confirmar que el mensaje llegó """
    print("El mensaje ha llegado con éxito")
    if err is not None:
        print(f"Error al entregar mensaje: {err}")

def fetch_flights():
    try:

        # Dependiendo de los datos que queremos usamos una terminación diferente
        OPENSKY_URL = f"{OPENSKY_URI}/{OPENSKY_EXT}"
        response = requests.get(OPENSKY_URL)

        print(response.text)

        data = response.json()

        if response.status_code != 200:
            print(f"Error de API: {response.status_code} - {response.text[:50]}")
            return

        # 2. Verificar si el contenido no está vacío
        if not response.text.strip():
            print("La API devolvió un cuerpo vacío")
            return

        

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
    except ValueError as e:
        print(f"Error parseando JSON: {e}. Contenido recibido: {response.text[:100]}")
    except Exception as e:
        print(f"Error: {e}") 




if __name__ == "__main__":
    while True:
        fetch_flights()
        # Cuenta Gratuita Uso estimado cada 10s, por seguridad se incrementa a 15, debido a que no queremos un shadowban.
        time.sleep(15)
