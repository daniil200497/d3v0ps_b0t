FROM postgres:16

COPY init.sql /docker-entrypoint-initdb.d/

RUN echo "#!/bin/bash" > /usr/local/bin/init_1.sh && \
echo "mkdir /oracle" >> /usr/local/bin/init_1.sh && \
echo "mkdir /oracle/pg_data" >> /usr/local/bin/init_1.sh && \
echo "mkdir /oracle/pg_data/archive" >> /usr/local/bin/init_1.sh && \
echo "chown postgres:postgres /oracle/pg_data/archive" >> /usr/local/bin/init_1.sh

RUN chmod +x /usr/local/bin/init_1.sh

CMD ["/usr/local/bin/init_1.sh"]