# R package
print("Checking Required Libary")
packages_list <- c("rmgarch", "zoo")

new_packages <- packages_list[!(packages_list %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages)
lapply(new_packages, require, character.only = TRUE)
print("Checking Done")

var1mgarch_dcc_predict <- function(rmgarch_model){
  print("Calling R from python")
  print("Checking Input data")
  return(dataframe)
}