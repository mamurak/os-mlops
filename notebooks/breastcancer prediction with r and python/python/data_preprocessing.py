from numpy import number
from numpy.random import seed
from pandas import read_csv
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


# Set the random seed
seed(1)
print("Set seed 1")

print("Load cleaned data")
data_cleaned = read_csv("cleaned_data.csv")

# Standardize the numeric columns
scaler = StandardScaler()
numeric_cols = data_cleaned.select_dtypes(include=number).columns
data_cleaned[numeric_cols] = scaler.fit_transform(data_cleaned[numeric_cols])

print("Creating train and testing files")
# Use 70% of dataset as training set and remaining 30% as testing set
train_set, test_set = train_test_split(
    data_cleaned, test_size=0.3, random_state=1
)

print("Writing to csv files.")
train_set.to_csv("train.csv", index=False)
test_set.to_csv("test.csv", index=False)
print("Done.")