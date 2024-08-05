library(tidyverse)
library(skimr)
library(dplyr)

getwd()
data <- read.csv("BreastCancerWisconsinDataSet.csv", header = TRUE)

skim(data)

###ta bort dubplicata IDs, kolumner vi inte använder, kolla numeriska värden
print("Cleaning data...")

data <- data %>%
  dplyr::distinct(id, .keep_all = TRUE) %>%
  dplyr::select(c(diagnosis, 
                  radius_mean, 
                  area_mean, 
                  radius_worst,
                  area_worst,
                  perimeter_worst,
                  perimeter_mean)) %>%
  dplyr::mutate(across(-c(diagnosis), as.numeric)) #%>%
#dplyr::select(-X)

print("Data cleaning done, saving file.")

###spara ny fil
write.csv(data, file = "data_cleaned.csv", row.names = FALSE)
