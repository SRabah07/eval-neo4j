import logging

logger = logging.getLogger(__name__)

queries = [
    """
    // Create Stations Nodes
    LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/pauldechorgnat/cool-datasets/master/ratp/stations.csv' AS row
    CREATE (:Station {
                        id: row.nom_clean + "-" + row.ligne, 
                        nom:row.nom_clean, 
                        nom_gare: row.nom_gare, 
                        ligne: row.ligne,
                        latitude: toFloat(row.x), 
                        longitude: toFloat(row.y),
                        trafic: toFloat(row.Trafic),
                        ville: row.Ville
    });
    """,
    """
    // Create Relationships of type Liaison
    LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/pauldechorgnat/cool-datasets/master/ratp/liaisons.csv' AS row
    MATCH (f:Station {nom: row.start, ligne: row.ligne})
    MATCH (t:Station {nom:  row.stop, ligne: row.ligne})
    MERGE (f)-[:liaison {ligne: row.ligne, distance: sqrt((t.latitude - f.latitude)^2 + (t.longitude - f.longitude)^2)}]->(t)
    RETURN f, t;
    """,
    """
    // Add time duration between each station
    MATCH (:Station) -[r:liaison]->(:Station)
    SET r.time = (r.distance / 1000 / 40)*60
    RETURN r;
    """,
    """
    // Create Relationships of type correspondance
    LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/pauldechorgnat/cool-datasets/master/ratp/liaisons.csv' AS row
    MATCH (f:Station {nom: row.start}) WHERE f.ligne=row.ligne
    MATCH (t:Station {nom: row.start}) WHERE t.ligne<>row.ligne
    MERGE (f)-[:correspondance {ligne: t.ligne, distance: 266.666666, time: 4}]->(t)
    RETURN f, t;
    """
]


async def init(driver):
    logger.info('Create Neo4J objects: Stations, Liaison, Correspondences...')
    with driver.session() as session:
        for query in queries:
            logger.debug(query)
            session.run(query)
    logger.info('Neo4J objects created')


async def drop_all(driver):
    logger.info('Drop Neo4J objects: Stations, Liaison, Correspondences...')
    with driver.session() as session:
        query = """
        MATCH(n)
        DETACH DELETE n;
        """
        logger.debug(query)
        session.run(query)
    logger.info('Neo4J objects deleted')
