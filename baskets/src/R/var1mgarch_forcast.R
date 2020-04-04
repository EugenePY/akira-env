library(rmgarch)

var1mgarch_forcast <- function(mgarch_fit, num_steps, n_roll){
  print(str(mgarch_fit))
  if (is(mgarch_fit, "DCCfit")){
    var = dccforecast(mgarch_fit, n.ahead = num_steps, n.roll = n_roll)
    return(var)
    } else if(is(mgarch_fit, "uGARCHmultifit")) {
    # handling non-converge DCC-MGARCH forecast.
    #print("uGARCHmultifit")
    var = multiforecast(multifitORspec = mgarch_fit, n.ahead = num_steps, n.roll = n_roll)
    #print(var)
    #var = dccforecast(mgarch_fit, n.ahead = num_steps, n.roll = n_roll)
    return(var)
  }

}