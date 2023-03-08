import os

import pandas
import trino


TRINO_USERNAME = os.environ.get('TRINO_USERNAME')
TRINO_PASSWORD = os.environ.get('TRINO_PASSWORD')
TRINO_HOSTNAME = os.environ.get('TRINO_HOSTNAME')
TRINO_PORT = os.environ.get('TRINO_PORT')


conn = trino.dbapi.connect(
    host=TRINO_HOSTNAME,
    port=TRINO_PORT,
    user=TRINO_USERNAME,
    http_scheme='http',
)


def get_sql(sql, connector):
    """Return pandas DataFrame."""

    cur = connector.cursor()
    cur.execute(sql)
    response = pandas.DataFrame(
        cur.fetchall(), columns=[c[0] for c in cur.description]
    )
    return response


column_data_types = {
    'customer_id': 'int64',
    'snapshotdate': 'string',
    'label': 'int64',
    'feature_0': 'float64',
    'feature_1': 'float64',
    'feature_2': 'float64',
    'feature_3': 'float64',
    'feature_4': 'float64',
    'feature_5': 'float64',
    'feature_6': 'float64',
    'feature_7': 'float64',
    'feature_8': 'float64',
    'feature_9': 'float64',
}

table_to_columns = {
    'accounts': ('customer_id', 'snapshotdate', 'feature_9'),
    'demographics': ('customer_id', 'snapshotdate', 'feature_5', 'feature_6', 'feature_7', 'feature_8'),
    'creditcards': ('customer_id', 'snapshotdate', 'feature_2', 'feature_3', 'feature_4'),
    'loans': ('customer_id', 'snapshotdate', 'feature_0', 'feature_1'),
    'labels': ('customer_id', 'snapshotdate', 'label'),
}

for table_name in table_to_columns.keys():
    sql = f'SELECT * FROM hive.{table_name}.raw_{table_name}'
    print(f'Running query: {sql}')
    df = get_sql(sql, conn)


    column_names = table_to_columns[table_name]
    type_mapping = {
        column_name: column_data_types[column_name]
        for column_name in column_names
    }
    mapped_df = df.astype(type_mapping)

    values_sql = tuple([
        tuple(row) for row in mapped_df.values
    ])
    for row in values_sql:
        sql = f'INSERT INTO postgresql.{table_name}.fact_{table_name} VALUES {tuple(row)}'
        print(f'Running query: {sql}')
        df = get_sql(sql, conn)
