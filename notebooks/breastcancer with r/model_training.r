library(tidymodels)
library(xgboost)
#library(caret)

train <- read.csv("train.csv", header = TRUE)
test <- read.csv("test.csv", header = TRUE)

#Remove labels 
train_data <- train %>% select(-diagnosis)
test_data <- test %>% select(-diagnosis)

#create target 
train_label <- train %>%
                select(diagnosis) %>%
                is.na() %>%
                magrittr::not()

test_label <- test %>%
              select(diagnosis) %>%
              is.na() %>%
              magrittr::not()


#convert to matrices
train_matrix <- as.matrix(train_data)
train_target <- as.numeric(train_label)

test_matrix <- as.matrix(test_data)
test_target <- as.numeric(test_label)


#Create DMatrix
dtrain <- xgb.DMatrix(data = train_matrix, label = train_target)
dtest <- xgb.DMatrix(data = test_matrix, label = test_target)


breastcancer_model <-xgboost(data = dtrain, 
                              nround = 2,
                              objective = "binary:logistic")

xgb.save(breastcancer_model, "breastcancerXGBmodel")