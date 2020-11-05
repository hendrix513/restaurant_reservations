import falcon
from .endpoints import AvailableTables, Reservation, CancelReservation, ReservationLock, TABLE_SIZES

import redis
import os


def create_app():
    api = falcon.API()

    r = redis.Redis(host=os.environ.get('REDIS_HOST'))
    r.flushall()

    ReservationLock.init_lock(r)
    available_tables = AvailableTables(r)
    available_tables.release_tables(list(TABLE_SIZES.keys()))

    api.add_route('/available_tables', available_tables)
    api.add_route('/reservation', Reservation(r, available_tables))
    api.add_route('/cancel_reservation', CancelReservation(r, available_tables))

    return api
