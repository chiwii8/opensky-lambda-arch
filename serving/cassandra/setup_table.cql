-- Fichero que contiene la configuración final para la creación de la tabla de datos

CREATE KEYSPACE IF NOT EXISTS opensky_analytics 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE opensky_analytics;

-- Nos permite tener un control como una serie temporal en la que se puede observar el avión como se va desplazando
CREATE TABLE IF NOT EXISTS live_flights (
    icao24 text PRIMARY KEY,
    callsign text,
    origin_country text,
    latitude double,
    longitude double,
    altitude double,
    velocity double,
    on_ground boolean,
    last_update timestamp
) WITH default_time_to_live = 120;


-- Filtrado de los aviones que van a tener una baja latitud(Despiegue o aterrizaje) para poder medir el uso apropiado de la altura ideal
CREATE TABLE IF NOT EXISTS flight_alerts (
    alert_type text, -- Ej: 'LOW_ALTITUDE', 'HIGH_SPEED'
    ts timestamp,
    icao24 text,
    altitude double,
    PRIMARY KEY (alert_type, ts)
) WITH CLUSTERING ORDER BY (ts DESC);