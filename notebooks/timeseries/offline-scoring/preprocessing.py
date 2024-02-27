import pandas as pd
import numpy as np


df = pd.read_csv('raw-data.csv')
df['time'] = pd.to_datetime(df['ts'], unit='ms')
df.set_index('time', inplace=True)
df.drop(columns=['ts'], inplace=True)

df1 = df.loc[df['id'] == 'pump-1']
df1 = df1.drop(columns=['id', 'label'])

df2 = df.loc[df['id'] == 'pump-2']
df2 = df2.drop(columns=['id', 'label'])

#
# Few helper functions
#

# Get list with column names: F1, F2, Fn, L


def get_columns(n):
    f = []
    for x in range(1, n+1):
        f.append("F"+str(x))
    f.append("L")
    return f


# Create empty data frame
def create_empty_df(n):
    d = ([0.]*n)
    d.append(0)
    dfx = pd.DataFrame([d], columns=get_columns(n))
    dfx.drop(dfx.index[0], inplace=True)
    return dfx


# Create data frame with one row
def create_df(vals: list, label: int = 0):
    if not isinstance(vals, list):
        raise TypeError
    dfx = pd.DataFrame([vals+[label]], columns=get_columns(len(vals)))
    return dfx


length = 5  # Episode length

df_epis = create_empty_df(length)

for id in df.id.unique():
    print("Convert data for: ", id)

    df2 = df.loc[df['id'] == id]

    epi = []
    for index, row in df2.iterrows():
        # print('%6.2f, %d' % (row['value'], row['label']))
        epi.append(row['value'])
        if len(epi) == length:
            df_row = create_df(epi, row['label'])
            df_epis = df_epis.append(df_row, ignore_index=True)
            del (epi[0])

df_epis.head(20)

df_epis.describe()

# Calculate number of episodes
n_episodes = df_epis.shape[0]

# Calculate number of features
n_features = df_epis.shape[1] - 1

n_anomaly = df_epis[df_epis['L'] == 1].shape[0]

n_normal = df_epis[df_epis['L'] == 0].shape[0]

anomaly_rate = n_anomaly / float(n_episodes) * 100

# Print the results
print("Total number of episodes: {}".format(n_episodes))
print("Number of features: {}".format(n_features))
print("Number of episodes with anomaly: {}".format(n_anomaly))
print("Number of episodes witManipulatehout anomaly: {}".format(n_normal))
print("Anomaly rate in dataset: {:.2f}%".format(anomaly_rate))

factor = 5  # Number of copies
dfr = df_epis.copy()
for i in range(1, factor):

    f = 0.5 + ((i - 1) * 0.5 / (factor-1))  # vary the anomaly by a factor

    dfi = df_epis.copy()
    dfi['F5'] = np.where(dfi['L'] == 1, dfi['F5']*f, dfi['F5'])
    dfr = dfr.append(dfi)

df_epis = dfr.copy()

# Calculate number of episodes
n_episodes = df_epis.shape[0]

# Calculate number of features
n_features = df_epis.shape[1] - 1

n_anomaly = df_epis[df_epis['L'] == 1].shape[0]

n_normal = df_epis[df_epis['L'] == 0].shape[0]

anomaly_rate = n_anomaly / float(n_episodes) * 100

# Print the results
print("Total number of episodes: {}".format(n_episodes))
print("Number of features: {}".format(n_features))
print("Number of episodes with anomaly: {}".format(n_anomaly))
print("Number of episodes without anomaly: {}".format(n_normal))
print("Anomaly rate in dataset: {:.2f}%".format(anomaly_rate))

df_epis.to_csv(
    'preprocessed-data.csv', index=False, header=True, float_format='%.2f'
)
