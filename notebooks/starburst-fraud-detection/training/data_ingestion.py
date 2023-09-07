from os import environ

from pandas import DataFrame
from trino import dbapi, auth


def ingest_data(
        data_folder='./data', trino_host='', trino_port='',
        trino_user='', trino_password=''):
    print('ingesting data')

    connection = _get_connection(
        trino_host, trino_port, trino_user, trino_password
    )
    query = _get_query()
    data = _request_data(query, connection)

    data.to_parquet(f'{data_folder}/data.parquet')

    print('data ingestion done')


def _get_connection(trino_host, trino_port, trino_user, trino_password):

    TRINO_USERNAME = environ.get('TRINO_USERNAME', trino_user)
    TRINO_PASSWORD = environ.get('TRINO_PASSWORD', trino_password)
    TRINO_HOSTNAME = environ.get('TRINO_HOSTNAME', trino_host)
    TRINO_PORT = environ.get('TRINO_PORT', trino_port)

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
      transactions.time,
      transactions.v1,
      transactions.v2,
      transactions.v3,
      transactions.v4,
      transactions.v5,
      transactions.v6,
      transactions.v7,
      transactions.v8,
      transactions.v9,
      transactions.v10,
      transactions.v11,
      transactions.v12,
      transactions.v13,
      transactions.v14,
      transactions.v15,
      transactions.v16,
      transactions.v17,
      transactions.v18,
      transactions.v19,
      transactions.v20,
      transactions.v21,
      transactions.v22,
      transactions.v23,
      transactions.v24,
      transactions.v25,
      transactions.v26,
      transactions.v27,
      transactions.v28,
      transactions.amount,
      labels.label
    FROM
      fd_data_bucket."transaction-data"."transaction-data" transactions
      JOIN fd_data_bucket."transaction-labels"."transaction-labels" labels ON
          CAST(transactions.id AS VARCHAR) = labels.transaction_id
    ORDER BY
      transactions.time ASC
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
