# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2
import pickle as pkl
import tqdm
from model.passive_model import BasketModel, FactorDynamicBasketModel, TVOLS
import datetime

with open("../sythesis/excels/EWS_MAIN.xlsx", "rb") as f:
    modeldaily_fx_rate = pd.read_excel(f, sheet_name="FX_RATE").dropna()
    modeldaily_fx_rate.set_index("DATE", 1, inplace=True)

with open("./pkls/curncy_vix.pkl", "rb") as f:
    curncy_vix = pkl.load(f, encoding="latin1")
    curncy_vix.columns = curncy_vix.columns.levels[0][curncy_vix.columns.labels[0]]

with open("./pkls/basket_data.pkl", "rb") as f:
    basket_data = pkl.load(f, encoding="latin1")

# get the workdays
workday_index = modeldaily_fx_rate.index
basket_data.columns = [i.replace(" Curncy", "").replace("USD", "")
                       for i in basket_data.columns.levels[0][basket_data.columns.labels[0]]]

# Features transform
# Percentile score


def percentile_score(x, window_size):
    all_ = []
    for i in range(window_size, x.shape[0]):
        rows = []
        for j in range(x.shape[1]):
            rows.append(stats.percentileofscore(x.iloc[:i, j], x.iloc[i, j]))
        all_.append(rows)
    res = pd.DataFrame(np.array(all_)/100,
                       index=x.index[window_size:], columns=x.columns)
    return res

# Chi-Square Transform


def chi2normal_transformation(df):
    risk_factor = pd.DataFrame(
        chi2.cdf(df, pd.rolling_mean(df, 150)),
        columns=df.columns,
        index=df.index)
    risk_factor = (risk_factor - pd.expanding_mean(risk_factor)) / \
        pd.expanding_std(risk_factor)
    return risk_factor


# Perparse dataset
# loading data
excel_pd = basket_data.loc[workday_index].dropna()
currency_vix = curncy_vix

# seting plot
meta_setup = {"figsize": (15, 5), "grid": True}

# select valid data
data = excel_pd.loc[excel_pd.index >= pd.to_datetime("1999-01-01")]

# Prepare the factors
# forward shift the factors for one week
all_vix = currency_vix
all_vix = all_vix.loc[all_vix.index >=
                      pd.to_datetime("1999-01-01")].shift(1)

sigma_vix = ['VIX Index'] + \
    [col for col in all_vix.columns if "V1M" in col]  # Factor Names
x_base_cncy = ["USD", "AUD", "EUR", "GBP"]
portfolio = ["JPY", "AUD", "KRW", "EUR", "SGD", "GBP"]

# transform into USD/X format
for asset in portfolio:
    if asset not in x_base_cncy:
        data.loc[:, asset] = 1./data.loc[:, asset]
montly_price = data

# monthly adjusted model
monthly_return = ((montly_price - montly_price.shift(22)) /
                  montly_price.shift(22)).dropna()  # align with the current BMK model

# change TWD into USD
monthly_return["TWD"] = - monthly_return["TWD"]
monthly_return.rename(columns={"TWD": "USD"}, inplace=True)


# Raw data
curncy_vix = all_vix[sigma_vix]
# Transform the data points
ps_score = percentile_score(curncy_vix, window_size=30)
chinorm = chi2normal_transformation(curncy_vix)

# estimation the parameters

initial_size = 50
factor_target = monthly_return.join(ps_score).dropna()
monthly_return = factor_target[monthly_return.columns]
risk_factor = factor_target[ps_score.columns]

portfolio = ["JPY", "AUD", "KRW", "EUR", "SGD", "GBP"]
target = "USD"

factor_maps = {
    "JPY": ['USDJPYV1M Curncy'],
    "AUD": ['AUDUSDV1M Curncy', 'USDTWDV1M Curncy'],
    "KRW": ['USDKRWV1M Curncy', 'USDTWDV1M Curncy'],
    "EUR": ['EURUSDV1M Curncy'],
    "SGD": ['USDSGDV1M Curncy'],
    "GBP": ['USDTWDV1M Curncy']
}
hist_weights = {}

agent1 = BasketModel(target="USD",
                     portfolio=portfolio)

agent2 = FactorDynamicBasketModel(target="USD",
                                  portfolio=portfolio,
                                  factor_maps=factor_maps)
agent3 = TVOLS(target="USD",
               portfolio=portfolio)

agents = [agent1, agent2, agent3]

time_index = []
rewards_dy = []
weighs_dy = []
bound_dy = []

for agent in agents:
    r_temp = []
    w_temp = []
    stamp_temp = []
    b_temp = []
    for step in tqdm.tqdm(range(monthly_return.shape[0] - initial_size)):
        # prepare data
        if agent.__class__.__name__ == "BasketModel":
            batch_return = monthly_return.iloc[:step + initial_size]
            agent.train(batch_return[agent._target],
                        batch_return[agent._portfolio])
            weight = agent.weights

        elif agent.__class__.__name__ == "FactorDynamicBasketModel":
            batch_return = monthly_return.iloc[:step + initial_size]
            batch_factor = risk_factor.iloc[:step + initial_size]
            proxy_list = agent.making_features(portfolio_returns=batch_return[agent._portfolio],
                                               factors=batch_factor)
            target_proxy = pd.concat([batch_return, proxy_list], 1).dropna()
            agent.train(target_proxy[agent._target],
                        target_proxy.drop(agent._target, 1))

        elif agent.__class__.__name__ == "TVOLS":
            batch_return = monthly_return.iloc[:step + initial_size]
            res = agent.fit(batch_return[agent._portfolio],
                            batch_return[[agent._target]])

        # New data point
        new_state = monthly_return.iloc[step+initial_size]
        new_risk = risk_factor.iloc[:step+initial_size+1]
        proxy = new_state[agent._portfolio]
        target = new_state[agent._target]

        if agent.__class__.__name__ == "FactorDynamicBasketModel":
            w = agent.dynamic_weights(new_risk)
            weight = w.iloc[-1]

        elif agent.__class__.__name__ == "BasketModel":
            weight = agent._weights

        elif agent.__class__.__name__ == "TVOLS":
            weight = np.array(res[0])[-1]

        r = agent.reward(target, proxy, weight)
        #bound = agent.residual_bound(target, proxy, weight, norm.interval(0.68)[1])
        r_temp.append(r)
        w_temp.append(weight)
        stamp_temp.append(monthly_return.index[step+initial_size])
        # b_temp.append(bound)
    hist_weights[agent.__class__.__name__] = [stamp_temp, w_temp]

with open("./pkls/hist_weights.{}.pkl".format(datetime.date.today().strftime("%Y%m%d")),
          "wb") as f:
    pkl.dump(hist_weights, f)

# update the weight excel file
for name in hist_weights.keys():
    m = hist_weights[name]
    weights_all = pd.DataFrame(m[1],
                               index=pd.DatetimeIndex(m[0]),
                               columns=monthly_return.columns[1:])
    weights_all.to_excel("./excels/{}.xlsx".format(name))
