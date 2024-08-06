library(tidymodels)
library(xgboost)

max_depth <- as.integer(Sys.getenv('max_depth'))
n_round <- as.integer(Sys.getenv('n_round'))
early_stopping_rounds <- as.integer(Sys.getenv('early_stopping_rounds'))


print('Loading training and test data')
train <- read.csv("train.csv", header = TRUE)
test <- read.csv("test.csv", header = TRUE)

#Remove labels 
train_data <- train %>% select(-diagnosis)
test_data <- test %>% select(-diagnosis)

#create targets

train_label <- train %>%
  select(diagnosis) %>%
  mutate(diagnosis = ifelse(diagnosis == "M", 1, 0)) %>%
  pull(diagnosis)

test_label <- test %>%
  select(diagnosis) %>%
  mutate(diagnosis = ifelse(diagnosis == "M", 1, 0)) %>%
  pull(diagnosis)

#convert to matrices
train_matrix <- as.matrix(train_data)
train_label <- as.numeric(train_label)

test_matrix <- as.matrix(test_data)
test_label <- as.numeric(test_label)


#Create DMatrix
dtrain <- xgb.DMatrix(data = train_matrix, label = train_label)
dtest <- xgb.DMatrix(data = test_matrix, label = test_label)


print('Training model...')
breastcancer_model <-xgboost(data = dtrain, 
                              nround = n_round,
                              max.depth = max_depth,
                              early_stopping_rounds = early_stopping_rounds,
                              verbose = 2,
                              objective = "binary:logistic")

pred <- predict(breastcancer_model, dtest)
err <- mean(as.numeric(pred > 0.5) != test_label)
print(paste("test-error=", err))

print('Saving model')
xgb.save(breastcancer_model, 'model.bst') 
