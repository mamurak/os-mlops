from os import environ

from pandas import DataFrame
from trino import dbapi, auth


TRINO_USERNAME = environ.get('TRINO_USERNAME', 'trino')
TRINO_PASSWORD = environ.get('TRINO_PASSWORD', 'trino')
TRINO_HOSTNAME = environ.get('TRINO_HOSTNAME', 'trino-service')
TRINO_PORT = environ.get('TRINO_PORT', '8080')


def ingest_data(data_folder='./data'):
    print('ingesting data')

    connection = _get_connection()
    query = _get_query()
    data = _request_data(query, connection)

    data.to_parquet(f'{data_folder}/data.parquet')

    print('data ingestion done')


def _get_connection():
    connection = dbapi.connect(
        host=TRINO_HOSTNAME,
        port=TRINO_PORT,
        user=TRINO_USERNAME,
        http_scheme='https',
        auth=auth.BasicAuthentication(TRINO_USERNAME, TRINO_PASSWORD),
    )
    return connection


def _get_query():
    query = """
    SELECT
        transactions.timestamp,
        transactions.user_id,
        transactions.amount,
        transactions.trans_type,
        transactions.foreign,
        transactions.interarrival,
        labels.label
    FROM fd_data_bucket.fd_data.transactions transactions
    JOIN TABLE (gsheets.system.sheet(id => '1jW1oEQlYuaC53lCFIPe-qXJHa73E4wl7BliJhI8Vq6o')) labels
    ON CAST (transactions.transaction_id AS VARCHAR) = labels.transaction_id
    ORDER BY transactions.timestamp ASC
    """
    return query


def _request_data(sql, connector):
    """Return pandas DataFrame."""

    cur = connector.cursor()
    cur.execute(sql)
    response = DataFrame(
        cur.fetchall(), columns=[c[0] for c in cur.description]
    )
    return response


if __name__ == '__main__':
    ingest_data(data_folder='/data')
