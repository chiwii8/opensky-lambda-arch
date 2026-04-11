import os
import logging
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debido a problemas causados porque la compilación binaria .jar del conector de cassandra no dispone de del streaming en esa versión
# Se emplea una versión de python pura usando un driver de cassandra de python
# Se registran los datos de la ejecución para ver si se realiza correctamente 


# Creación de un Sink para Cassandra
class CassandraSinkMapFunction:
    """
    Esta clase maneja la conexión a Cassandra de forma eficiente.
    Se inicializa una vez por cada slot de ejecución de Flink.
    """
    def __init__(self, hosts, keyspace):
        self.hosts = hosts
        self.keyspace = keyspace
        self.session = None
        self.cluster = None

    def _open_connection(self):
        if self.session is None:
            logger.info(f"Conectando al cluster de Cassandra en: {self.hosts}")
            self.cluster = Cluster(self.hosts)
            self.session = self.cluster.connect(self.keyspace)
            
            # Preparamos las sentencias
            self.insert_live = self.session.prepare("""
                INSERT INTO live_flights 
                (icao24, callsign, origin_country, longitude, latitude, altitude, on_ground, velocity) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """)

            self.insert_alert = self.session.prepare("""
                INSERT INTO flight_alerts (alert_type, icao24, altitude, ts) 
                VALUES (?, ?, ?, toTimestamp(now()))
            """)

    def process(self, row):
        # Aseguramos que la conexión esté abierta
        self._open_connection()
        
        try:
            # 1. Insertar en tabla principal (Live Flights)
            # Flink Row accede por índice: icao24(0), callsign(1), country(2)...
            self.session.execute(self.insert_live, (
                row[0], row[1], row[2], row[4], row[5], row[6], row[7], row[8]
            ))

            # 2. Lógica de Alertas (Altitud < 500m y no está en tierra)
            altitude = row[6]
            on_ground = row[7]
            
            if altitude is not None and altitude < 500 and not on_ground:
                self.session.execute(self.insert_alert, (
                    "LOW_ALTITUDE", row[0], altitude
                ))
                
        except Exception as e:
            logger.error(f"Error insertando en Cassandra: {str(e)}")
        
        return row # Devolvemos la fila por si queremos encadenar más pasos



def run_flights_streaming():
    
    # Configuración de l entorno
    env = StreamExecutionEnvironment.get_execution_environment()
    t_env = StreamTableEnvironment.create(env)


    # Cargamos las variables de entorno necesarias
    KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS","kafka:19092")
    CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
    CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC')


    # Definimos el conjunto de datos provenientes de kafka, revisar con Redpanda si es necesario
    kafka_source_ddl = f"""
        CREATE TABLE flights_input (
            icao24 STRING,
            callsign STRING,
            origin_country STRING,
            `timestamp` BIGINT,
            longitude DOUBLE,
            latitude DOUBLE,
            altitude DOUBLE,
            on_ground BOOLEAN,
            velocity DOUBLE
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{KAFKA_TOPIC}',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVER}',
            'properties.group.id' = 'flink-consumer-group',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """
    t_env.execute_sql(kafka_source_ddl)

    # Definimos el tipo de datos que se usan
    type_info = Types.ROW([
        Types.STRING(),  # icao24 (0)
        Types.STRING(),  # callsign (1)
        Types.STRING(),  # origin_country (2)
        Types.LONG(),    # timestamp (3)
        Types.DOUBLE(),  # longitude (4)
        Types.DOUBLE(),  # latitude (5)
        Types.DOUBLE(),  # altitude (6)
        Types.BOOLEAN(), # on_ground (7)
        Types.DOUBLE()   # velocity (8)
    ])

    table = t_env.from_path("flights_input")
    ds = t_env.to_append_stream(table,type_info)

    # Configuración del sink de Cassandra
    sinkCassandra = CassandraSinkMapFunction([CASSANDRA_HOST],CASSANDRA_KEYSPACE)

    ds.map(lambda row: sinkCassandra.process(row), output_type=type_info)
    
    logger.info("Pipeline de Flink 2.2.0 iniciado con éxito (Cassandra Python Sink)...")
    env.execute("OpenSky_RealTime_Analytics")

if __name__ == '__main__':
    run_flights_streaming()