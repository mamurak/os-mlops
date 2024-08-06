from pandas import read_csv, to_numeric


print("Loading raw data.")

# Load the raw data
data = read_csv("raw_data.csv")

# Display summary statistics similar to skim()
print(data.describe(include='all'))

print("Cleaning data...")

# Drop duplicate rows based on 'id' column
data = data.drop_duplicates(subset='id')

# Select specific columns
columns_to_keep = [
    'diagnosis',
    'radius_mean',
    'area_mean',
    'radius_worst',
    'area_worst',
    'perimeter_worst',
    'perimeter_mean'
]
data = data[columns_to_keep]

# Convert all columns except 'diagnosis' to numeric
cols_to_convert = data.columns.difference(['diagnosis'])
data[cols_to_convert] = data[cols_to_convert].apply(
    to_numeric, errors='coerce'
)

print("Data cleaning done, saving file.")

# Save the cleaned data to a new CSV file
data.to_csv("cleaned_data.csv", index=False)