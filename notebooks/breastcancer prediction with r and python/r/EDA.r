library(tidyverse)
library(ggridges)
library(tidymodels)
library(aws.s3)

Sys.setenv("AWS_ACCESS_KEY_ID"="minio",
           "AWS_SECRET_ACCESS_KEY"="minio123",
           "AWS_S3_ENDPOINT"="minio-default-api-minio.apps.cluster-nhhgn.nhhgn.sandbox1471.opentlc.com",
           "AWS_DEFAULT_REGION"="")


save_object("BreastCancerWisconsinDataSet.csv", file = "BreastCancerWisconsinDataSet.csv", bucket = "sarasbucket", region ="")




#---------------------Load and skim data--------------------------------------
data <- read.csv("BreastCancerWisconsinDataSet.csv", header = TRUE, sep = ",")
summary_data <- skimr::skim(data)
summary_data


#----------------------Check for duplicate IDs--------------------------------
duplicates <- data %>%
  group_by(id) %>%
  filter(n() > 1) %>%
  distinct(id) %>%
  pull()

duplicates

#Drop id column since we don't need it
data <- data %>%
  dplyr::select(-id)

#Check occurences of diagnosises
table(data$diagnosis)


#----------Creating distribution plot---------
pdf_file <- "distribution_plots.pdf"

# Create a PDF file for saving the plots
pdf(pdf_file)

# Loop through each column in the data frame
for (col in names(data)) {
  p <- ggplot(data, aes(x = data[[col]], y = diagnosis, fill = diagnosis)) +
    geom_density_ridges() +
    labs(title = col) +
    theme_minimal()
  
  print(p)
}

# Close the PDF device
dev.off()


#--------Normalize data-------------------
data_normalized <- data %>%
  dplyr::select(-diagnosis)

data_normalized <- scale(data_normalized)


#------------Check for multicolinearity---------------
library(ggcorrplot)

norm_data_matrix <- cor(data_normalized)

norm_data_pvalues <- cor_pmat(data_normalized)

matrix_plot <- ggcorrplot(norm_data_matrix,
                          #correlation_matrix, 
                          method = "square", 
                          #hc.order = TRUE, 
                          #type = "lower"
)
matrix_plot

pvalues_plot <- ggcorrplot(norm_data_pvalues,
                           #correlation_pvalues, 
                           method = "square", 
                           #hc.order = TRUE, 
                           #type = "lower"
)
pvalues_plot

#------------------Check Variance Inflation Factor---------------
library(car)
library(lmtest)

#test all variables 
model <- glm(factor(diagnosis) ~ ., data = data, family = binomial)
#a hint when the algorithm doesn't converge
summary(model)

#Check for normality
shapiro.test(rstandard(model)) #reject the null hypothesis of normality

#resettest(model)
summary(model)

vif(model)

#-------Feature selection using Principal Component Analysis------------------
library(FactoMineR)
library(factoextra)
library(caret)
library(e1071)


pca.data <- princomp(norm_data_matrix)
summary(pca.data)

scree_plot <- fviz_eig(pca.data, addlabels = TRUE)
scree_plot

pca.data$loadings[, 1:7]

# Graph of the variables
variable_graph<- fviz_pca_var(pca.data, col.var = "cos2",
                              gradient.cols = c("black", "orange", "green"),
                              repel = TRUE)
variable_graph

model_features <- fviz_cos2(pca.data, choice = "var", axes = 1:6)
model_features
#Vi har våra features

#-----Split training and test data----------------

set.seed(1)

model_data <- data %>%
  mutate_if(is.numeric, scale) %>%
  as.data.frame()


#Use 70% of dataset as training set and remaining 30% as testing set
sample <- sample(c(TRUE, FALSE), nrow(model_data), replace=TRUE, prob=c(0.7,0.3))
train  <- model_data[sample, ]
test   <- model_data[!sample, ]

#Create logistic spec
logistic_spec <- logistic_reg(
  mode = "classification",
  engine = "glm"
)

#fit data
first_try <- logistic_spec%>%
  fit(factor(diagnosis) ~ radius_mean + area_mean + radius_worst + perimeter_mean + area_worst + perimeter_worst,
      data = train)
first_try

predictions <- first_try %>%
  predict(test) %>%
  pull(.pred_class)

table(predictions, test$diagnosis)
#--------Få ut metrics av regressionen--------------------------------------

# Convert test$diagnosis to a factor with specified levels
test$diagnosis <- factor(test$diagnosis, levels = c("M", "B"))


confusion <- confusionMatrix(predictions, test$diagnosis)

# Extract precision, recall, and F1-Score
precision <- confusion$byClass["Pos Pred Value"]
recall <- confusion$byClass["Sensitivity"]
f1_score <- confusion$byClass["F1"]

# Display the results
cat("Precision:", precision)
cat("Recall (Sensitivity):", recall)
cat("F1-Score:", f1_score)

