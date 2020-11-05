import itertools

import falcon
import json
import logging

TABLES_KEY = 'tables'
RESERVATION_LOCK_KEY = 'reservation_lock'
RESERVATION_NUM_KEY = 'reservation_num'
TABLE_SIZES = {'table1': 1, 'table2': 2, 'table3': 3, 'table4': 4}
MAX_RESERVATION_SIZE = sum(TABLE_SIZES.values())
MAX_UNLOCK_TRIES = 1000
RESERVATIONS_KEY = 'reservations'

log = logging.getLogger(__name__)


class ReservationLock(object):
    def __init__(self, redis_conn):
        self.redis_conn = redis_conn
        self.reservation_num = None

    def __enter__(self):
        for _ in range(MAX_UNLOCK_TRIES):
            if self.redis_conn.lpop(RESERVATION_LOCK_KEY):
                return
        raise Exception()

    def __exit__(self, type, value, traceback):
        self.__class__.init_lock(self.redis_conn)

    @classmethod
    def init_lock(cls, redis_conn):
        redis_conn.lpush(RESERVATION_LOCK_KEY, 1)


class RedisConnected(object):
    def __init__(self, redis_conn):
        self.redis_conn = redis_conn


class AvailableTables(RedisConnected):
    def on_get(self, req, resp):
        resp.body = json.dumps({name: TABLE_SIZES[name] for name in self.get_available_tables()})

    def get_available_tables(self):
        return [name.decode('utf-8') for name in self.redis_conn.smembers(TABLES_KEY)]

    def release_tables(self, table_names):
        self.redis_conn.sadd(TABLES_KEY, *table_names)


class Reservation(RedisConnected):
    def __init__(self, redis_conn, available_tables):
        super().__init__(redis_conn)
        self.available_tables = available_tables

    def on_post(self, req, resp):
        data = json.loads(req.stream.read(req.content_length or 0))
        try:
            size = data['size']
        except KeyError:
            raise falcon.HTTPBadRequest('\'size\' parameter missing',
                                        '\'size'
                                        '\' parameter not found')

        if size > MAX_RESERVATION_SIZE:
            raise falcon.HTTPBadRequest('\'size\' parameter exceeds maximum',
                                        '\'size'
                                        '\' parameter too high')

        reservation_num = self.reserve(size)
        resp.body = json.dumps({'success': bool(reservation_num), 'reservation_num': reservation_num})

    def reserve(self, size):
        with ReservationLock(self.redis_conn):
            tables = self.available_tables.get_available_tables()
            num_tables = len(tables)
            for k in range(num_tables):
                for table_group in itertools.combinations(tables, k+1):
                    if sum([TABLE_SIZES[table] for table in table_group]) == size:
                        self.redis_conn.srem(TABLES_KEY, *table_group)
                        reservation_num = self.redis_conn.incr(RESERVATION_NUM_KEY)
                        self.redis_conn.hset(RESERVATIONS_KEY, str(reservation_num), ', '.join(table_group))
                        return reservation_num

        return None


class CancelReservation(RedisConnected):
    def __init__(self, redis_conn, available_tables):
        super().__init__(redis_conn)
        self.available_tables = available_tables

    def on_post(self, req, resp):
        data = json.loads(req.stream.read(req.content_length or 0))
        try:
            reservation_num = data['reservation_num']
        except KeyError:
            raise falcon.HTTPBadRequest('\'reservation_num\' parameter missing',
                                        '\'reservation_num\' parameter not found')

        tables_str = self.redis_conn.hget(RESERVATIONS_KEY, str(reservation_num)).decode('utf-8')
        if tables_str:
            tables = tables_str.split(', ')
            self.redis_conn.hdel(RESERVATIONS_KEY, str(reservation_num))
            self.available_tables.release_tables(tables)




