import pandas as pd


df_epis = pd.read_csv('preprocessed-data.csv')

# Extract feature columns
feature_cols = list(df_epis.columns[:-1])

# Show the list of columns
print("Feature columns:\n{}".format(feature_cols))

X_all = df_epis[feature_cols]

# Show the feature information by printing the first five rows
print("\nFeature values:")
print(X_all.head())

X_all.to_pickle('features.pickle')
