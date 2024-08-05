library(tidyverse)
library(skimr)
library(dplyr)

print("Loading raw data.")

data <- read.csv("raw_data.csv", header = TRUE)
skim(data)

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

print("Data cleaning done, saving file.")

write.csv(data, file = "cleaned_data.csv", row.names = FALSE)
