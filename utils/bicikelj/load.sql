-- load bicikelj data into postgresql

create table if not exists bicikelj (id integer, "timestamp" timestamptz, json_data jsonb);

\copy bicikelj from program 'gunzip -cd bicikeljdata_2016.csv.gz' with csv header;
