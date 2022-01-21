import logging

logger = logging.getLogger(__name__)


def create_starting_location(driver, latitude, longitude):
    query = """
     MERGE (from: Origin {
                    nom: "Current Position", 
                    latitude: $latitude, 
                    longitude: $longitude
     });

    """
    with driver.session() as session:
        session.run(query, latitude=latitude, longitude=longitude)


def create_ending_location(driver, latitude, longitude):
    query = """
     MERGE (from: Target {
                    nom: "Final Position", 
                    latitude: $latitude, 
                    longitude: $longitude
     });

    """
    with driver.session() as session:
        session.run(query, latitude=latitude, longitude=longitude)


def get_closer_station_to_starting(driver):
    query = """
        MATCH(from:Origin {nom: "Current Position"})
        MATCH (other: Station)
        WITH sqrt((other.latitude - from.latitude)^2 + (other.longitude - from.longitude)^2) as distance, other
        ORDER BY distance ASC
        LIMIT 1
        WITH other, distance
        RETURN other.id as id, distance
    """

    with driver.session() as session:
        result = session.run(query)
        for record in result:
            return record["id"], record["distance"]


def get_closer_station_to_ending(driver):
    query = """
        MATCH(from:Target {nom: "Final Position"})
        MATCH (other: Station)
        WITH sqrt((other.latitude - from.latitude)^2 + (other.longitude - from.longitude)^2) as distance, other
        ORDER BY distance ASC
        LIMIT 1
        WITH other, distance
        RETURN other.id as id, distance
    """

    with driver.session() as session:
        result = session.run(query)
        for record in result:
            return record["id"], record["distance"]


def create_link_from_starting(driver, station_id, distance):
    query = """
     MATCH(from:Origin {nom: "Current Position"})
     MATCH (other: Station {id: $station_id})
     MERGE (from)-[:Walk {distance: $distance, time: (($distance / 1000) / 4)*60}]->(other)
    """
    with driver.session() as session:
        session.run(query, station_id=station_id, distance=distance)


def create_link_to_ending(driver, station_id, distance):
    query = """
     MATCH(from:Target {nom: "Final Position"})
     MATCH (other: Station {id: $station_id})
     MERGE (from)-[:Walk {distance: $distance, time: (($distance / 1000) / 4)*60}]->(other)
    """
    with driver.session() as session:
        session.run(query, station_id=station_id, distance=distance)


def compute_itinerary(driver):
    query = """
        MATCH (start: Origin {nom:"Current Position"})
        MATCH (end:Target {nom: "Final Position"})
        CALL gds.alpha.shortestPath.stream({
          nodeQuery: 'MATCH (n) RETURN id(n) as id',
          relationshipQuery: 'MATCH (n1)-[r]-(n2) RETURN id(r) as id, id(n1) as source, id(n2) as target, r.time as time',
          startNode: start,
          endNode: end,
          relationshipWeightProperty: 'time'
        })
        YIELD nodeId, cost
        WITH nodeId, cost as Duration, gds.util.asNode(nodeId).nom AS Location, gds.util.asNode(nodeId).ligne AS Means
        RETURN Duration, Location,( CASE Means WHEN null THEN 'Walk' ELSE "Line: " + Means  END) AS Means
    """
    steps = []
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            location = record['Location']
            duration = record['Duration']
            means = record['Means']
            step = {'location': location, 'duration': duration, 'means': means}
            steps.append(step)
    return steps


def delete_itinerary(driver):
    query = """
    MATCH(start:Origin {nom: "Current Position"})
    MATCH(end:Target {nom: "Final Position"})
    DETACH DELETE start, end; 
    """
    with driver.session() as session:
        session.run(query)
