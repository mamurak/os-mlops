import pandas as pd

df_epis = pd.read_csv('sensor-training-data.csv')

# Extract feature columns
feature_cols = list(df_epis.columns[:-1])

# Extract target column 'label'
target_col = df_epis.columns[-1]

# Show the list of columns
print("Feature columns:\n{}".format(feature_cols))
print("\nTarget column: {}".format(target_col))

# Separate the data into feature data and target data (X_all and y_all, respectively)
X_all = df_epis[feature_cols]
y_all = df_epis[target_col]

# Show the feature information by printing the first five rows
print("\nFeature values:")
print(X_all.head())

print(y_all)

X_all.to_pickle('features.pickle')
y_all.to_pickle('labels.pickle')
