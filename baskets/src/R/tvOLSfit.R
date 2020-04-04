library(zoo)
library(tvReg)

tvm_fit <- function(basket, target) {
  x <- zoo(basket, order.by=as.Date(strptime(as.character(row.names(basket)), "%Y-%m-%d")))
  y <- zoo(target, order.by=as.Date(strptime(as.character(row.names(target)), "%Y-%m-%d")))
  res <- tvOLS(x = x, y = y, bw = 0.3)

  coef.tvlm <- res$tvcoef
  return(c(res, coef.tvlm))
}