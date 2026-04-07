# opensky-lambda-arch

## Requisitos

* **Ingesta**: Producer Kafka que lea de la API periódicamente o de un dataset estático simulando un flujo en tiempo real (emitiendo eventos poco a poco).
* **Procesamiento**: Trabajo Spark Structured Streaming con ventanas temporales y al menos una agregación. Si lo consideráis adecuado, podéis utilizar otros motores como Kafka Streams o Apache Flink.
* **Almacenamiento**: Persistencia en Cassandra, PostgreSQL u otra base de datos que consideréis adecuada para vuestro proyecto. También podéis crear vuestro propio data lake (HDFS/MinIO) para almacenar los datos crudos.
* **Visualización**: Dashboard de Grafana con al menos 2 paneles.
* **Infraestructura**: Todo desplegado con Docker Compose, integrado en la misma red.
* **Documentación**: README con arquitectura, instrucciones de despliegue y decisiones de diseño. 

## Arquitectura

Para la realización de este proyecto se ha decidido utilizar una arquitectura Lambda.
