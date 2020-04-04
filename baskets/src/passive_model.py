import os
import os.path
# os.environ['R_HOME'] = "C:/Users/i6800309/DOCUME~1/R/R-34~1.4"

from scipy import optimize
import numpy as np
import pandas as pd
import statsmodels.api as sm
# from statsmodels.sandbox.tsa import garch

import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri

# gapping the ds
from rpy2.robjects import default_converter
from rpy2.robjects.conversion import localconverter

from .portfolio_opt import optimize_portfolio


class DCCGARCH(object):
    """
    y_{t} = y_{mu} + \espisilon_{t}

    \espisilon_{t} = \v_{t} * \sqrt(\sigma^2_{t}); v_{t} ~ N(0, 1)

    # Variance Model(uGARCH)
    \sigma^2_{t} = \alpha_{0} + \sum^{p}_{i=1}\alpha_{i} * sigma^2_{t-i} + \
        \sum^{q}_{i=1}\beta_{i} * \espsilon^2_{t-i}

    # Correlation Coefficient Model

    """

    def __init__(self, p=1, q=1, VAR_lag=1, model="dcc"):
        self.p = p
        self.q = q
        self._lag = VAR_lag  # if lag == 0 the do not fit the garch model with VAR
        if model not in ["dcc", "bekk"]:
            raise NotImplementedError(
                "Only model=[bekk, dcc] {} is not supported".format(
                    model))
        else:
            self.model = model

    def fit(self, assets_returns, inplace=False):
        with open(os.path.dirname(__file__)+"./R/var1mgarch_dcc1.R") as f:
            r_script = "".join(f.readlines())
            vargarch_fit = robjects.r(r_script)
            print("{0} from python: \n {1}".format(
                type(assets_returns), assets_returns.head()))

            with localconverter(default_converter + pandas2ri.converter):
                r_object = pandas2ri.py2ri(assets_returns)

            # calling the R function
            self.result = vargarch_fit(r_object)
            self.n_assets = len(assets_returns.columns)
            rcov = robjects.r("rcov")
            rcor = robjects.r("rcor")

            cov = np.array(rcov(garch.result[-1]))
            cor = np.array(rcor(garch.result[-1]))

            all_cov = []
            for k, id_ in enumerate(fx_rate_return_mid.index):
                c = pd.DataFrame(cov[:, :, k], columns=fx_rate_return_mid.columns,
                                 index=pd.MultiIndex.from_tuples([(id_, i) for i in fx_rate_return_mid.columns]))
                all_cov.append(c)
            cov_all = pd.concat(all_cov, axis=0)

            self.covs = cov_all
            all_cor = []
            for k, id_ in enumerate(fx_rate_return_mid.index):
                c = pd.DataFrame(cor[:, :, k], columns=fx_rate_return_mid.columns,
                                 index=pd.MultiIndex.from_tuples([(id_, i) for i in fx_rate_return_mid.columns]))
                all_cor.append(c)
            cor_all = pd.concat(all_cor, axis=0)

            self.corrs = cor_all
            if inplace:
                pass
            else:
                return self.result

    def predict(self, n_step_ahead, n_roll):
        with open(op.path.dirname(__file__) + "./R/var1mgarch_forcast.R") as f:
            r_script = "".join(f.readlines())
            garch_forcast = robjects.r(r_script)
            if self.result is not None:
                # var_fit = self.result[0]
                garch_fit = self.result[-1]
            else:
                print("{} haven't been fitted".format(self.__class__.__name__))
            # calling the R function
            result = garch_forcast(garch_fit, n_step_ahead, n_roll)
            H = np.array(result.do_slot('mforecast')[0][0]).reshape(
                self.n_assets, self.n_assets, n_step_ahead)
            H = np.rollaxis(H, 2)
            mu = np.array(result.do_slot('mforecast')[4]).reshape(
                n_step_ahead, self.n_assets)
            return H, mu


class MinimizeVolatilityModel(object):
    def __init__(self, **kwargs):
        self._mgarch_model = DCCGARCH(**kwargs)

    def fit(self, assets_return, implied_rate, target_asset="TWD Curncy"):
        #new_older = [target_asset]+[i for i in assets_return.columns if i != target_asset]
        #assets_return = assets_return[[target_asset, ]]
        assert assets_return.columns[0] == target_asset

        self._mgarch_model.fit(assets_return)

        self.expected_covs, self.expected_mus = self._mgarch_model.predict(
            n_step_ahead=1, n_roll=0)

        s = np.diag(1/np.sqrt(np.diag(self.expected_covs[0])))

        self.expect_rho = pd.DataFrame(s.dot(self.expected_covs[0]).dot(s),
                                       index=assets_return.columns, columns=assets_return.columns)

        # k - 1 instrument(beside the target ccy)
        k = self._mgarch_model.n_assets - 1

        w0 = np.random.normal(size=k)
        self.results = []
        for cov, mu in zip(self.expected_covs, self.expected_mus):
            self.results.append(hedge_portfolio(w0, cov,
                                                implied_rate, mu))
        self.weighs = pd.Series(self.results[-1].x,
                                index=implied_rate.index[1:])
        return self.weighs


class BasketModel(object):
    """Basic passive model"""

    def __init__(self, target="USD/TWD",
                 portfolio=['USD/{}'.format(curncy) for curncy
                            in ['EUR', 'JPY', 'CCY']]):
        self._portfolio = portfolio
        self._target = target
        self.reset(len(self._portfolio))

    def __str__(self):
        return f"<{self.__class__.__name__}:target={self._target}, "\
            f"proxy={self._portfolio}>"

    def reset(self, input_size):
        self._weights = np.random.normal(size=input_size)

    @property
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self, new_weights):
        """Just flush out the old one"""
        assert self._weights.shape == new_weights.shape
        self._weights = new_weights

    @staticmethod
    def mse_loss(weights, portfolio, target):
        return np.square(
            target - np.dot(portfolio, weights))

    def predict(self, data):
        # predicting the position
        out = pd.DataFrame(
            [self.weights]*len(data.index),
            index=data.index)
        return out

    def fit(self, data, method="OLS", *arg, **kwargs):
        # result = optimize.minimize(fun=lambda x, *arg: \
        #         np.mean(self.mse_loss(x, arg[0], arg[1])), x0=self.weights,
        #         args=(proxy, target), bounds=[(-0.5, 0.5)]*proxy.shape[1])
        # self.weights = result['x']
        target = data[self._target]
        proxy = data[self._portfolio]

        if method == "lsq":
            b = np.array([(-0.5, 0.5)]*proxy.shape[1])
            result = optimize.lsq_linear(proxy, target,
                                         bounds=[b[:, 0], b[:, 1]])
            self._weights = result['x']
        else:
            if method == "OLS":
                model = sm.OLS(target, proxy)
            elif method == "WLS":
                model = sm.WLS(target, proxy)
            res = model.fit()
            self.fitted_model = {"model": model, "result": res}
            self._weights = res.params

    def process_batch(self, batch):
        data = batch["obs"].astype(np.float64)
        target = data[self._target]
        proxy = data[self._portfolio]
        assert proxy.ndim == 2
        self.fit(target, proxy)

    @classmethod
    def make(cls, env, algo, **kwarg):
        return cls(**kwarg)

    def residual_bound(self, target, proxy, weights, bendwidth=1.96):
        z = weights.sum() + 1
        res = self.fitted_model['result'].resid / z
        mu = np.mean(res)
        std = np.std(res)
        return mu - bendwidth * std, mu + bendwidth * std

    def reward(self, target, proxy, weights):
        z = (np.sum(weights) + 1)
        return ((target - np.dot(proxy, weights))/z).sum()


class TVOLS(BasketModel):
    """
    y_{t} = X_{t} \beta_{t} + \espisilon_{t}


    """

    def __init__(self, bandwidth=0.1, kernel="gaussian", **kwargs):
        super(TVOLS, self).__init__(**kwargs)
        self.kernel = kernel
        self.bandwidth = bandwidth

    def fit(self, basket, target, inplace=False):
        with open("C:/Users/i6800309/PassiveModel/model/R/tvOLSfit.R") as f:
            r_script = "".join(f.readlines())
            tvols_fit = robjects.r(r_script)
            # print("Using {} as Basket.".format(", ".join(basket.columns.tolist())))
            with localconverter(default_converter + pandas2ri.converter):
                basket_r_object = pandas2ri.py2ri(basket)
                target_r_object = pandas2ri.py2ri(target)

            # calling the R function
            self.result = tvols_fit(basket_r_object,
                                    target_r_object)
            self._weights = np.array(self.result[0])[-3:].mean(0)

            if inplace:
                pass
            else:
                return self.result


class FactorDynamicBasketModel(BasketModel):
    """Danamical adjusting passive model"""

    def __init__(self, factor_maps, **kwargs):
        super(FactorDynamicBasketModel, self).__init__(**kwargs)
        assert isinstance(factor_maps, dict)
        self._factor_maps = factor_maps
        self._weights = np.random.normal(
            size=len(self._portfolio) + np.sum([len(val) for val in
                                                factor_maps.values()]))

    def making_features(self, portfolio_returns, factors):
        features = []
        for curncy in self._factor_maps.keys():
            if curncy != self._target:
                d = pd.concat([portfolio_returns[[curncy]],
                               factors[self._factor_maps[curncy]]], 1)
                f = pd.DataFrame(
                    d[[curncy]].values * d[self._factor_maps[curncy]].values,
                    index=d.index, columns=["{} dot {}".format(
                        curncy, fact) for fact in self._factor_maps[curncy]])
                features.append(f)
        features = pd.concat(features, 1)
        self._weight_names = portfolio_returns.columns.tolist() + features.columns.tolist()
        return features

    @classmethod
    def make(cls, env, algo, **kwarg):
        return cls(**kwarg)

    def debug(self):
        """
        This should return the period that the model doing bad
        """
        pass

    def dynamic_weights(self, factors):
        dynamic_weights = np.tile(self.weights[:len(self._portfolio)],
                                  (factors.shape[0], 1))
        name_maps = {n: i for i, n in enumerate(self._portfolio)}
        for i, name in enumerate(self._weight_names):
            if name not in self._portfolio:
                factor_name = name.split("dot")[-1][1:]
                asset_name = name.split("dot")[0][:-1]
                dy_w = self._weights[i] * factors[factor_name]
                dynamic_weights[:, name_maps[asset_name]] = \
                    dynamic_weights[:, name_maps[asset_name]] + dy_w

        dw = pd.DataFrame(dynamic_weights, columns=self._portfolio,
                          index=factors.index)
        return dw


class HybridInstrumentBasket(object):
    """Using Option and NDF as Instrument of proxy hedge.

    Arguments:
        object {[type]} -- [description]
    """
    pass


class EnhencedBasketModel(object):
    """Basic passive model with covariance enchenced"""

    def __init__(self, update_freq=10, portfolio=['USD/{}'.format(curncy) for
                                                  curncy in ['EUR', 'JPY', 'CCY']]):
        self._portfolio = portfolio
        # self._swap_points =
        self._target = 'USD/TWD'
        self._weights = np.random.normal(
            size=len(self._portfolio))
        self._update_freq = update_freq

    @property
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self, new_weights):
        """Just flush out the old one"""
        self._weights = new_weights

    @staticmethod
    def volatility(weights, cov):
        return np.dot(np.dot(cov, weights), weights)

    def get_cov_estimation(self, batch):
        pass

    @classmethod
    def make(cls, env, algo):
        return cls()


class BasketNDFModel(BasketModel):
    """
    This model can be seen an alternative basket model:
        we make the agent can have ndf as additional asset to operate. 
            original Basket model:
                y_{t}  = constant + x_{t}\beta +  \episilon_{t}
                min (y_{t} - x\beta)'(y - x\beta); solve this by minimize the loss functio
                s.t some carry constraints and weight constraints 

            Basket NDF model:
                y_{t}  = constant + x_{t}\beta + \alpha\y_{t} +\episilon_{t}
                max reward; if U(x) = log(x); 
                    we take first order Taylor expainsion 
                        max E(x) - 0.5*var(x) or min - E(x) + 0.5 * var(x)
                the object function becomes as follow:
                    min -(basket's return + cost of contract) + (y_{t} - x\beta)'(y - x\beta);
                    s.t some carry constraints and weight constraints.
    """

    def __init__(self, target, basket, option_contract):
        super(BasketNDFModel, self).__init__(target=target, basket=basket)
        self._ndf = option_contract  # Non-delivery forward

    def train(self, target, basket, option_contract):
        pass


class BetaNeturalModel(BasketModel):
    """
    Valuation Model:
        USDTWD = \beta * euqity_factor + \sum_{i}\alpha_{i} * EWS_{i} + \epsilon_{a}
        USDKRW = \beta_{2} * equity_factor + \sum_{i} \alpha_{i} * EWS_{krw_{i}} + \epsilon_{b}
        min Var(USDTWD + \Weight * USDKRW); s.t constraints, equity netural
        This cannot give better performace to the current passive model since 
        min Var(USDTWD + \Weight * USDKRW) dosen't change, however the \beta will change 
        overtime, and has momentumn(market attention), some we can adjust the input. 
        If we can foracast beta ganna be low we reduce the proxy hedge ratio. 
    """

    def __init__(self, target, basket, option_contract):
        super(BasketNDFModel, self).__init__(target=target, basket=basket)
        self._ndf = option_contract  # Non-delivery forward

    def train(self, target, basket, option_contract):
        pass


if __name__ == "__main__":
    def test_tvols():
        data = np.random.normal(size=(100, 3))
        fake_data = pd.DataFrame(data,
                                 columns=['USD/{}'.format(curncy) for
                                          curncy in ['EUR', 'JPY', 'CCY', 'TWD']], index=pd.date_range("2011/01/02", periods=100))
        basket = fake_data.drop("TWD", 1)
        target = fake_data[["TWD"]]
        model = TVOLS(bw=0.1, kernel="gaussian")
        res = model.fit(basket, target)

    def test_():
        agnet = BasketModel()
        true_w = np.array([0.23, -0.12, 0.33])
        x = np.random.normal(size=(100, 3))
        data = np.hstack([x, np.dot(x, true_w).reshape(x.shape[0], 1)])
        fake_data = pd.DataFrame(data,
                                 columns=['USD/{}'.format(curncy) for
                                          curncy in ['EUR', 'JPY', 'CCY', 'TWD']])
        agnet.process_batch(fake_data)

    def test_2():
        agent = EnhencedBasketModel()
        true_w = np.array([[0.2, 1.2], [0.32, 0.1]])

        x = np.random.normal(size=(100, 3))
        data = np.hstack([x, np.dot(x, true_w).reshape(x.shape[0], 1)])
        fake_data = pd.DataFrame(data,
                                 columns=['USD/{}'.format(curncy) for
                                          curncy in ['EUR', 'JPY', 'CCY', 'TWD']])

        agent.process_batch(fake_data)

    def gen_ar(alpha, init, size):
        data = [init]
        for i in range(1, size):
            data.append(data[i-1]*alpha + np.random.chisquare(1))
        return data

    def test():
        excel_file = pd.ExcelFile("../data/raw_M.xlsx")
        excel_pd = excel_file._parse_excel("daily_data").set_index("Date")

        twd_vix = pd.read_excel("../vix_tw.xlsx", "vix").set_index("Date")
        currency_vix = pd.read_excel("../currency_vix.xlsx").set_index("Date")

        data = excel_pd.loc[excel_pd.index >= pd.to_datetime("1999-01-01")]
        daily_return = data.pct_change()
        all_vix = pd.concat([twd_vix, currency_vix], 1)
        all_vix = all_vix.loc[all_vix.index >= pd.to_datetime(
            "1999-01-01")].shift(-1).pct_change()

        portfolio = ["JPY", "AUD", "KRW", "XEU", "SGD", "GBP"]
        factor_maps = {
            "JPY": ['VIX Index  (R2)', 'USDJPYV1M Curncy  (R2)'],
            "AUD": ['VIX Index  (R2)', 'AUDUSDV1M Curncy  (R2)'],
            "KRW": ['VIX Index  (R2)', 'USDKRWV1M Curncy  (R2)'],
            "XEU": ['VIX Index  (R2)', 'EURUSDV1M Curncy  (L1)'],
            "SGD": ['VIX Index  (R2)', 'USDSGDV1M Curncy  (L1)'],
            "GBP": ['VIX Index  (R2)']
        }

        agent = FactorDynamicBasketModel(target="USD",
                                         portfolio=portfolio, factor_maps=factor_maps)
        proxy = daily_return[portfolio]
        proxy_list = agent.making_features(
            portfolio_returns=proxy, factors=all_vix)
        target_proxy = pd.concat([daily_return, proxy_list], 1).dropna()
        agent.train(target_proxy[agent._target],
                    target_proxy.drop(agent._target, 1))
        print(agent.weights)
        print(target_proxy.columns[1:])
        print(agent.dynamic_weights(all_vix.loc[target_proxy.index]))

    # test the FactorDynamicBasketModel
    def test_basket():
        excel_file = pd.ExcelFile("../data/raw_M.xlsx")
        excel_pd = excel_file._parse_excel("daily_data").set_index("Date")

        twd_vix = pd.read_excel("../vix_tw.xlsx", "vix").set_index("Date")
        currency_vix = pd.read_excel("../currency_vix.xlsx").set_index("Date")
        data = excel_pd.loc[excel_pd.index >= pd.to_datetime("1999-01-01")]
        daily_return = data.pct_change()
        all_vix = pd.concat([twd_vix, currency_vix], 1)
        all_vix = all_vix.loc[all_vix.index >=
                              pd.to_datetime("1999-01-01")].shift(1)

        portfolio = ["JPY", "AUD", "KRW", "XEU", "SGD", "GBP"]

        agent = BasketModel(target="USD",
                            portfolio=portfolio)
        proxy = daily_return[portfolio]
        target = daily_return[agent._target]
        target_proxy = pd.concat([target, proxy], 1).dropna()
        # res = agent.train(target_proxy[agent._target], target_proxy.drop(agent._target, 1))
        print(agent.weights)
        print(target_proxy.columns[1:])
