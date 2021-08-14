ALTER TABLE sites
  ALTER COLUMN geometry
    TYPE geometry(Point, 4326)
  USING ST_SetSRID(geometry, 4326);


WITH big_roads AS
    (SELECT * FROM roads WHERE roads.gp_rtp != 5)
SELECT sites.id, big_roads.objectid
  FROM sites
       JOIN big_roads ON ST_DWithin(geometry(sites.geometry),
				    geometry(big_roads.shape), 1000)
 WHERE sites.id < 10;


-- Older code (without WITH)
SELECT sites.id, roads2.objectid
  FROM sites
       JOIN (
	 SELECT * FROM roads WHERE roads.gp_rtp != 5) AS roads2
	   ON ST_DWithin(geometry(sites.geometry),
			 geometry(roads2.shape), 1000)  WHERE sites.id < 10;

