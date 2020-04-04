# https://rdrr.io/cran/mgarchBEKK/man/BEKK.html
var1mgarch_bekk1 <- function(variables, VAR.fit = NA) {
  
  mgarch_fit = BEKK(eps, order = c(1, 1), params = NULL, fixed = NULL, method = "BFGS",
     verbose = F)
}