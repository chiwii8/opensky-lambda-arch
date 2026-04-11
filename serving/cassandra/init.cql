-- Fichero que permite la inserción de los datos a través de un contenedor auxiliar

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
);


-- En esta tabla se almacenan los datos por horas, en las que se realizará una medición del número de aviones que hubo por el páis en cada hora
CREATE TABLE IF NOT EXISTS hourly_stats_by_country (
    day date,
    hour int,
    country text,
    flight_count counter,
    PRIMARY KEY ((day), hour, country)
) WITH CLUSTERING ORDER BY (hour DESC, country ASC);


-- Filtrado de los aviones que van a tener una baja latitud(Despiegue o aterrizaje) para poder medir el uso apropiado de la altura ideal
CREATE TABLE IF NOT EXISTS flight_alerts (
    alert_type text, -- Ej: 'LOW_ALTITUDE', 'HIGH_SPEED'
    ts timestamp,
    icao24 text,
    altitude double,
    PRIMARY KEY (alert_type, ts)
) WITH CLUSTERING ORDER BY (ts DESC);