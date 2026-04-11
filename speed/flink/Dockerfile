FROM flink:2.2.0

# Cambiamos a root para realizar instalaciones
USER root

# 2. Instalamos dependencias mínimas de Python
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools && \
    rm -rf /var/lib/apt/lists/*

# 3. Enlace simbólico para que Flink encuentre "python"
RUN ln -sf /usr/bin/python3 /usr/bin/python

# 4. Gestión de dependencias de Python mediante requirements.txt
# Copiamos el archivo primero para aprovechar la caché de Docker
COPY flink/requirements.txt /opt/flink/requirements.txt

RUN pip3 install --no-cache-dir -r /opt/flink/requirements.txt --break-system-packages || \
    pip3 install --no-cache-dir -r /opt/flink/requirements.txt

# Copiamos el conector de Kafka
COPY flink/lib/flink-sql-connector-kafka-4.0.0-2.0.jar /opt/flink/lib/

# Ajustamos permisos para que el usuario 'flink' pueda leer el jar
RUN chmod 644 /opt/flink/lib/flink-sql-connector-kafka-4.0.0-2.0.jar

# Volvemos al usuario flink
USER flink