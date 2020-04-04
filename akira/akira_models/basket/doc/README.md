# Basket Hedge

## Proxy Heding Tool for currency hedging

### Model

- Benchmark
- Minimize Volatility
- Factor Adjustment

#### Optimization

Benchmark Model

$$
\begin{aligned}
R_{target, t} &= R_{proxy, t}W_{t} + \epsilon_{t} \\
\epsilon_{t} &\sim N(0, \sigma)
\end{aligned}
$$
estimation: 

OLS
$$
\begin{aligned}
min_{W} \frac{1}{N} \sum_{t}(R_{target, t} - R_{proxy,t}W)^{2}
\end{aligned}
$$

Minimize Volatility

$$
\begin{aligned}
R_{target, t} = R_{proxy, t}W_{t} + \epsilon_{t} \\
R_{t} = \sum^{p}_{i=0} R_{t-i}\alpha_{t-i} + \eta_{t}
\end{aligned}
$$

Factor Dynamic Model


#### Positioning


#### Reproduce Ability