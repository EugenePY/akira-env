library(zoo)
library(rmgarch)

var1mgarch_dcc_fit <- function(assets_returns, var_lag=1, garch_order=c(1, 1), mgarch="dcc", verbose=TRUE){
  
   usdx <- assets_returns
   usdx.zoo <- zoo(usdx, order.by=as.Date(strptime(as.character(row.names(usdx)), "%Y-%m-%d")))
   num_var = length(names(usdx))
   cat("NUM of variables: ", num_var, "\n")
   # First GARCH Specs.. Lets use GARCH(1,1) for both of them just to show..
   VAR.fit <- varxfit(usdx, p=1, postpad = "constant")
   uspec <- multispec(replicate(num_var, ugarchspec()))
   #dcc.garch11.spec <- dccspec(uspec, dccOrder = c(1, 1), distribution = c("mvnorm", "mvt", "mvlaplace")[1])
   dcc.garch11.spec <- dccspec(uspec, VAR = TRUE,
                                robust = TRUE, lag = var_lag,
                                dccOrder = garch_order, distribution = "mvnorm")
   mgarch.fit <- dccfit(dcc.garch11.spec, usdx, VAR.fit = VAR.fit)
     
  
   if(verbose){
     print(VAR.fit)
     print(mgarch.fit)
   } 
   return(c(VAR.fit, mgarch.fit))
}
