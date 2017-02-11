
select distinct
	(v#>>'{lat}')::numeric as lat,
	(v#>>'{lng}')::numeric as lng,
	(v#>>'{name}') as name,
	(v#>>'{number}')::integer as number
into bicikelj_postaje
from (
	SELECT 
		id as id_meritve,
		timestamp as cas_meritve, 
		row_to_json(jsonb_each(json_data#>'{markers}'))#>'{value}' as v
	from bicikelj
) A ;



select
	id_meritve,
	cas_meritve,
	(v#>>'{open}')::integer as open,
	(v#>>'{bonus}')::integer as bonus,
	(v#>>'{number}')::integer as number,
	(v#>>'{station,free}')::integer as free,
	(v#>>'{station,total}')::integer as total,
	(v#>>'{station,ticket}')::numeric as ticket,
	(v#>>'{station,available}')::integer as available,
	(v#>>'{updated}')::integer as updated,
	(v#>>'{timestamp}')::timestamp as timestamp,
	(v#>>'{station_valid}')::boolean as station_valid
into bicikelj_stanje
from (
	SELECT 
		id as id_meritve,
		timestamp as cas_meritve, 
		row_to_json(jsonb_each(json_data#>'{markers}'))#>'{value}' as v
	from bicikelj
) A ;


