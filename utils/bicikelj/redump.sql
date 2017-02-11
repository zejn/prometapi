

-- this should be all zero
SELECT
	count(*) filter (where station_valid != true) as station_valid_not_true_count,
	count(*) filter (where ticket != 0) as ticket_not_zero_count,
	count(*) filter (where open != 1) as open_not_one_count,
	count(*) filter (where bonus != 0) as bonus_not_zero_count
from bicikelj_stanje   ;



-- psql bici -c '\copy (select id_meritve, cas_meritve, number, free as slots_free, available as bikes_available, total as capacity, updated, timestamp from bicikelj_stanje) to stdout with csv header;' | gzip -9c > bicikelj_stanje.csv.gz