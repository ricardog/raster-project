with table_extent as (
  select ST_SetSRID(ST_Extent(shape), 4326)
    from roads where roads.gp_rtp != 5
),
grid as (
  select (ST_SquareGrid(1, table_extent))
)
select count(*) from grid;

------------------------------------------------------------------------
with table_extent as (
  select ST_SetSRID(ST_Extent(shape), 4326) as extent
    from roads where roads.gp_rtp != 5
), grid as (select ST_SquareGrid(1, extent) from table_extent)
  select count(*) from grid;

------------------------------------------------------------------------
with grid as (
  select (ST_SquareGrid(1, ST_Transform(wkb_geometry, 4326))).*
    from ne_10m_admin_0_countries where name = 'Canada'
)
select ST_AsText(ST_Centroid(geom)) from grid;


------------------------------------------------------------------------
with table_extent as (
  select ST_SetSRID(ST_Extent(shape), 4326) as extent
    from roads where roads.gp_rtp != 5
), grid as (select (ST_SquareGrid(1, extent)).* from table_extent)
select ST_AsText(ST_Centroid(geom)) from grid;

------------------------------------------------------------------------
WITH table_extent AS (
  SELECT ST_SetSRID(ST_Extent(shape), 4326) AS extent
    FROM roads WHERE roads.gp_rtp != 5
),
grid AS (
  SELECT (ST_SquareGrid(1, extent)).* AS geom FROM table_extent
),
points AS (
    SELECT ST_Centroid(geom) AS center FROM grid
),
big_roads AS (
  SELECT shape FROM roads WHERE roads.gp_rtp != 5 AND roads.objectid <= 19549124
)
SELECT ST_Astext(points.center) FROM points;

========================================================================
with table_extent AS (
  SELECT ST_SetSRID(ST_Extent(shape), 4326) AS extent
    FROM roads WHERE roads.gp_rtp != 5
),
grid AS (
  SELECT (ST_SquareGrid(1, extent)).* AS geom FROM table_extent
),
big_roads AS (
  SELECT shape FROM roads WHERE roads.gp_rtp != 5 AND roads.objectid <= 19549124
)
select count(*)
  FROM grid
       JOIN big_roads ON ST_Intersects(geography(grid.geom),
				       geography(big_roads.shape))
	      GROUP BY grid

	      SUM(ST_LengthSpheroid(
  ST_Intersection(geography(grid.geom), geography(big_roads.shape)),
  'SPHEROID["WGS 84",6378137,298.257223563]'
))

========================================================================
WITH table_extent AS (
  SELECT ST_SetSRID(ST_Extent(shape), 4326) AS extent
    FROM roads WHERE roads.gp_rtp != 5
),
grid AS (
  SELECT (ST_SquareGrid(1, extent)).* AS geom FROM table_extent
),
points AS (
    SELECT ST_Centroid(geom) AS center FROM grid
),
big_roads AS (
  SELECT shape FROM roads WHERE roads.gp_rtp != 5 AND roads.objectid <= 19549124
)
select SUM(ST_Length(
  ST_Intersection(
    ST_Buffer(geography(points.center), 1000),
    geography(big_roads.shape))
))
  FROM points
       JOIN big_roads ON ST_DWithin(ST_Buffer(geography(points.center), 1000),
				    geography(big_roads.shape),
				    1000);

========================================================================
WITH grid AS (
  SELECT *
    FROM ST_SquareGrid(1,
		       ST_GeomFromText('POLYGON((-180 -90, 180 -90, 180 90, -180 90, -180 -90))'))
),
points AS (
    SELECT ST_Centroid(geom) AS center FROM grid
),
big_roads AS (
  SELECT shape FROM roads WHERE roads.gp_rtp = 1
)
select SUM(ST_Length(
  ST_Intersection(
    ST_Buffer(geography(points.center), 1000),
    geography(big_roads.shape))
))
  FROM points
       JOIN big_roads ON ST_DWithin(ST_Buffer(geography(points.center), 1000),
				    geography(big_roads.shape),
				    1000);

========================================================================
EXPLAIN WITH major_roads AS (
  SELECT *,
         geography(shape) AS geog
    FROM roads
   WHERE roads.gp_rtp != 5
),
table_extent as (
  select ST_SetSRID(ST_Extent(shape), 4326) AS extent FROM major_roads
),
grid AS (
  SELECT (ST_SquareGrid(1, extent)).* FROM table_extent
),
some_sites AS (
  SELECT ST_Centroid(geom) AS geom,
	 geography(geom) as geog,
	 ST_Buffer(geography(geom), 1000) AS buffer
    FROM grid
)  
  SELECT COUNT(major_roads.objectid),
  SUM(ST_LengthSpheroid(ST_Intersection(geography(some_sites.buffer),
                                        major_roads.geog)::geometry,
					'SPHEROID["WGS 84",6378137,298.257223563]'))
  FROM some_sites
  JOIN major_roads ON
  ST_DWithin(some_sites.geog, major_roads.geog, 1000)
  GROUP BY some_sites.geog;

========================================================================
  -- To generate a table with the grid
create table grid_0_25_50 AS WITH major_roads AS (
  SELECT *,
         geography(shape) AS geog
    FROM roads
   WHERE roads.gp_rtp != 5
),
table_extent as (
  select ST_SetSRID(ST_Extent(shape), 4326) AS extent FROM major_roads
),
grid AS (
  SELECT (ST_SquareGrid(0.25, extent)).* FROM table_extent
),
some_sites AS (
  SELECT ST_SetSRID(ST_Centroid(geom), 4326) AS geom,
 geography(geom) as geog,
 ST_Buffer(geography(geom), 50000) AS buffer
    FROM grid
)
select * from some_sites;

ALTER TABLE grid_0_25_50
  ALTER COLUMN geom
    TYPE geometry(Point, 4326)
  USING ST_SetSRID(geom, 4326);

CREATE INDEX grid_0_25_50_geom_idx ON grid_0_25_50 USING GIST (geom);
CREATE INDEX grid_0_25_50_geog_idx ON grid_0_25_50 USING GIST (geog);
CREATE INDEX grid_0_25_50_buffer_idx ON grid_0_25_50 USING GIST (buffer);


========================================================================
EXPLAIN WITH major_roads AS (
  SELECT *,
         geography(shape) AS geog
    FROM roads
   WHERE roads.gp_rtp != 5
)
  SELECT COUNT(major_roads.objectid),
  SUM(ST_LengthSpheroid(ST_Intersection(grid_0_25.buffer,
                                        major_roads.geog)::geometry,
					'SPHEROID["WGS 84",6378137,298.257223563]'))
  FROM grid_0_25
  JOIN major_roads ON
  ST_DWithin(grid_0_25.geog, major_roads.geog, 1000)
  GROUP BY grid_0_25.geog;


EXPLAIN WITH major_roads AS (
  SELECT *,
         geography(shape) AS geog
    FROM roads
   WHERE roads.gp_rtp != 5
)
  SELECT grid_0_25_50.geom, COUNT(major_roads.objectid),
  SUM(ST_LengthSpheroid(ST_Intersection(grid_0_25_50.buffer,
                                        major_roads.geog)::geometry,
					'SPHEROID["WGS 84",6378137,298.257223563]'))
  FROM grid_0_25_50
  JOIN major_roads ON
  ST_DWithin(grid_0_25_50.geog, major_roads.geog, 1000)
  GROUP BY grid_0_25_50.geom;
