# opensky-lambda-arch

## Requisitos

* **Ingesta**: Producer Kafka que lea de la API periódicamente o de un dataset estático simulando un flujo en tiempo real (emitiendo eventos poco a poco).
* **Procesamiento**: Trabajo Spark Structured Streaming con ventanas temporales y al menos una agregación. Si lo consideráis adecuado, podéis utilizar otros motores como Kafka Streams o Apache Flink.
* **Almacenamiento**: Persistencia en Cassandra, PostgreSQL u otra base de datos que consideréis adecuada para vuestro proyecto. También podéis crear vuestro propio data lake (HDFS/MinIO) para almacenar los datos crudos.
* **Visualización**: Dashboard de Grafana con al menos 2 paneles.
* **Infraestructura**: Todo desplegado con Docker Compose, integrado en la misma red.
* **Documentación**: README con arquitectura, instrucciones de despliegue y decisiones de diseño. 

## Estructura del Repositorio
Para la realización de este proyecto se proyecta el uso de un único orquestador para el despliegue de todos los contenedores, pero para el mantenimiento de cierta limpieza se han usado ficheros .yml incluidos en único fichero en el que se redactan los valores de cada una de las capas empleadas. Para ello, se ha decidido usar un árbol con las carpetas debido al gran número de ficheros utilizados.

```
opensky-kappa-arch/
├───grafana
│   ├───imports           # Contiene el Dashboard para importarlo
│   └───provisioning      # Contiene los ficheros generados para su uso
│       ├───alerts
│       ├───dashboards
│       └───datasources
├───ingest                # Capa de Ingesta
│   └───producer          # Contiene los ficheros para el despliegue del producer
├───serving               # Capa de Almacenamiento de datos
│   └───cassandra         # Datos de inicialización y fichero para generación
└───speed                 # Capa de Procesamiento en tiempo real
    └───flink             # Contiene los ficheros para el despliegue de Apache Flink y la ejecución del consumer
        ├───consumer
        ├───jobs
        └───lib
```

## Arquitectura del Sistema

El proyecto implementa una Arquitectura Kappa, diseñada para procesar datos de vuelos en tiempo real con baja latencia y alta consistencia.

### Flujo de Datos

1. Ingesta (Ingest Layer): Captura de datos de vuelos en tiempo real (OpenSky). Cada actualización es enviado al bus de mensajería(Kafka).
2. Almacenamiento de Stream (Ingest Layer): Uso de un log de eventos (ej. Kafka / Redpanda). La retención configurada permite el reprocesamiento histórico utilizando el mismo código de streaming.
3. Procesamiento (Speed Layer): Un motor de procesamiento de flujo consume los eventos (Apache Flink), aplica transformaciones, filtrado geoespacial configurable en el fichero de orquestación.
4. Servicio (Serving Layer): Los resultados se persisten en una base de datos(Cassandra).
5. Visualización (Grafana): Exposición de los datos en un único dashboard con un fin.

## Guía de Configuración

### Requisitos previos

* Docker
* Docker Compose V2.
* Credenciales de OpenSky.

### Preparación Fichero .env
 Antes de desplegar los servicios, se crea el fichero .env usando como referencia el ejemplo .env.example que se muestra a continuación:

 ```.env
GRAFANA_ADMIN_USER=adminuser
GRAFANA_ADMIN_PASSWORD=adminpass
KAFKA_BOOTSTRAP_SERVERS=kafka:19092

# Producer Variables
KAFKA_TOPIC =Vuelos_stream
KAFKA_BROKER =kafka:19092  # Puede variar si se ejecuta interna o externamente
OPENSKY_URI=https://opensky-network.org/api # Esta URL es la base para realizar las peticiones a los diferentes servicios independientes que ofrece la API

# Cassandra
CASSANDRA_HOST=cassandra
CASSANDRA_KEYSPACE=opensky_analytics 
CASSANDRA_URL=cassandra:9042

# API USERACCOUNT
OPENSKY_USER=your-api-client
OPENSKY_SECRET=your-secret

# Coordenadas de la región objetivo
LAMIN=35.0
LOMIN=-10.0
LAMAX=44.0
LOMAX=5.0
```

Se modifican las credenciales de la API de referencia por tus datos.

## Despliegue en Local
Para este despliegue se utilizará otro network por lo que es incompatible con el despliegue del resto de servicios, no se ha integrado debido a que si es requerido el despliegue de hadoop posteriormente, se rompería la estructura de red.

Para poder realizar este despliegue, se requiere que actualmente ninguno de los servicios usados en clase exista. Por ello, Solo hace falta desplegar los servicios: 

```bash
    # Construye las imágenes e inicia el docker-compose
    # En caso de que no tenga Make, copie el comando correspondiente del Makefile
    make build 
```

Una vez iniciado el docker-compose, el consumer y producer se ejecutan automáticamente. por ello, únicamente hay que observar la ejecución de los servicios en los puertos enumerados.

### Puertos Habilitados

    ---------------------------------------
    |     Servicio      |     Puerto      |
    ---------------------------------------
    |   Kafka           |      9092       |
    ---------------------------------------
    |   Redpanda        |      8080       |
    ---------------------------------------
    |   Apache Flink    |      8081       |
    ---------------------------------------
    |  Cassandra-web    |      8082       |
    ---------------------------------------
    |   Grafana         |      3000       |
    ---------------------------------------

## Despliegue en OpenStack

## Decisiones de Diseño

* Se ha decidido usar 2 tablas de Cassandra, en las cuales se ha añadido un TTL corto, para evitar observar o falsear los datos observados. Una de las tablas se centra únicamente, en aquellos vuelos de baja altitud para tener un mayor control sobre ellos, en cambio la otra tabla tiene más información genérica, que sirve para el tratamiento de muchos datos.
* Se ha centrado el Mapa en España, pero dentro del fichero docker-compose.yml se puede seleccionar unas coordenadas, con las cuales se puede seleccionar aquella región del mapa que resulte interesante de observar.


## Autores
* Alejandro Sánchez Rodríguez
* Rafael de Jesús Bautista Hernández
