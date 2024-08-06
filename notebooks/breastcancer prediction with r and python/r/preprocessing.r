library(dplyr)

set.seed(1)
print("Set seed 1")
print("Load cleaned data")

data_cleaned <- read.csv("cleaned_data.csv", header = TRUE)

model_data <- data_cleaned %>%
  mutate_if(is.numeric, scale) %>%
  as.data.frame()


#Use 70% of dataset as training set and remaining 30% as testing set
print("Creating train and testing files")
sample <- sample(c(TRUE, FALSE), nrow(model_data), replace=TRUE, prob=c(0.7,0.3))
train  <- model_data[sample, ]
test   <- model_data[!sample, ]

print("Writing to csv files.")
write.csv(train, "train.csv", row.names = FALSE)
write.csv(test, "test.csv", row.names = FALSE)
print("Done.")
