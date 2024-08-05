library(shiny)
library(jsonlite)
library(httr)
ui <- fluidPage(
  titlePanel("Breastcancer Prediction"),
  sidebarLayout(
    sidebarPanel(
      numericInput("radius_mean", "Radius Mean:", value = 1.0, step = 0.01),
      numericInput("area_mean", "Area Mean:", value = 1.0, step = 0.01),
      numericInput("radius_worst", "Radius Worst:", value = 1.0, step = 0.01),
      numericInput("area_worst", "Area Worst:", value = 1.0, step = 0.01),
      numericInput("perimeter_worst", "Perimeter Worst:", value = 1.0, step = 0.01),
      numericInput("perimeter_mean", "Perimeter Mean:", value = 1.0, step = 0.01),
      actionButton("predict", "Get Prediction")
    ),
    mainPanel(
      h3("Prediction Result:"),
      verbatimTextOutput("prediction")
    )
  )
)
server <- function(input, output) {
  observeEvent(input$predict, {
    # Construct the payload with specific details
    payload <- list(
      inputs = list(
        list(
          name = 'dense_input',
          shape = c(1, 6),
          datatype = 'FP32',
          data = c(
            input$radius_mean,
            input$area_mean,
            input$radius_worst,
            input$area_worst,
            input$perimeter_worst,
            input$perimeter_mean
          )
        )
      )
    )
    # Convert the payload to JSON format
    json_payload <- toJSON(payload, auto_unbox = TRUE)
    print("hello")
    print(json_payload)
    print("goodbye")
    # Send POST request to the API
    response <- POST(
      url = "https://model-24081535-r-demo.apps.cluster-nhhgn.nhhgn.sandbox1471.opentlc.com/v2/models/model-24081535/infer",
      body = json_payload,
      encode = "json",
      content_type_json()
    )
    print(response)
    print(content(response, as = "text"))
    # Check response status
    if (status_code(response) == 200) {
      # Parse and display the prediction
      result <- content(response, as = "parsed")
      output$prediction <- renderText({
        paste("Prediction:", result)
      })
    } else {
      output$prediction <- renderText({
        "Error: Unable to get prediction from the API."
      })
    }
  })
}
shinyApp(ui = ui, server = server)