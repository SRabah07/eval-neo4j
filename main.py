from fastapi import FastAPI
from pydantic import BaseModel
from neo4j import GraphDatabase
import os
import time
from db.init import init, drop_all
from db.queries import *
import logging

LOGGING_FILE = os.environ.get('LOGGING_FILE', "neo4J_evaluation.log")
NEO4J_HOST = os.environ.get('NEO4J_HOST', '0.0.0.0')
logging.config.fileConfig("logging.config", defaults={"logging_file_name": LOGGING_FILE},
                          disable_existing_loggers=False)
app = FastAPI()

logger = logging.getLogger(__name__)

driver = GraphDatabase.driver(f'bolt://{NEO4J_HOST}:7687',
                              auth=('neo4j', 'neo4j'))

TIME_TO_WAIT_DB = os.environ.get('TIME_TO_WAIT_DB', '20')


class Position(BaseModel):
    latitude: float
    longitude: float


class Itinerary(BaseModel):
    start: Position
    end: Position
    duration: float
    steps: list


@app.get("/")
async def home():
    return {"message": "This Neo4J Evaluation"}


@app.get("/up")
async def up():
    return {"status": "OK", "message": "I am up!"}


@app.put("/itinerary")
async def get_itinerary(start: Position, end: Position):
    """
    Compute The Shortest Itinerary Between two Locations

    :param start: The coordinates of the starting point
    :param end: The coordinates of the ending point
    :return: The shortest path between those two points
    """
    # FIXME to manage concurrent access, use identifier for nodes

    logger.info(f"Compute itinerary from: {start} to {end}")

    # Create starting and ending nodes
    create_starting_location(driver, start.latitude, start.longitude)
    create_ending_location(driver, end.latitude, end.longitude)

    # Get closer stations to those two points
    info_start = get_closer_station_to_starting(driver)
    logger.debug(f"Closer station for starting point is: {info_start}")
    info_end = get_closer_station_to_ending(driver)
    logger.debug(f"Closer station for ending point is: {info_end}")

    # Create links between starting / ending and their closer points
    create_link_from_starting(driver, info_start[0], info_start[1])
    create_link_to_ending(driver, info_end[0], info_end[1])

    # Compute best itinerary
    steps = compute_itinerary(driver)
    if len(steps) == 0:
        raise Exception(f"No Itinerary found for Start: {start} and End: {end}!")

    duration = float(steps[-1]["duration"])
    result = Itinerary(start=start, end=end, duration=duration, steps=steps)

    # Clean
    delete_itinerary(driver)

    return result


@app.on_event("startup")
async def startup():
    logger.info('Application Startup...')
    # FIXME as I am not able to setup a health check on the Neo4j container, no curl...
    time.sleep(int(TIME_TO_WAIT_DB))
    await init(driver)


@app.on_event("shutdown")
async def shutdown():
    logger.info('Application Shutdown...')
    await drop_all(driver)
