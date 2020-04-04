import pandas as pd
from scipy.stats import chi2
from scipy import stats
import numpy as np
import click
from functools import wraps
from collections import deque


@click.option('-f', "--freq", type=str)
def resample_return(input, freq):
    ''' percentile transformation
    '''
    return input.pct_change().resample(freq).sum()


@click.option('-c', "--columns", "col", multiple=True, type=str)
@click.option('-l', "--level", "level", multiple=True, type=int)
def columns_selector(input, col, level):
    ''' percentile transformation
    '''
    n_level = max(level) + 1
    idx = np.argsort(level)
    sorted_level = deque(np.sort(level))
    
    selector = []
    for n in range(n_level):
        if sorted_level[0] == n:
            sorted_level.popleft()
            selector.append(col[len(sorted_level)])
        else:
            selector.append(slice(None))
    return input.loc[:, tuple(selector)]


@click.option('-w', "--window-size")
def percentile_score(input, window_size):
    ''' percentile transformation
    '''
    x = input
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


@click.option('-w', "--window-size", default=150, type=int)
def chi2normal_transformation(input, window_size):
    ''' chi2noraml transformation
    '''
    df = input
    risk_factor = pd.DataFrame(
        chi2.cdf(df, df.rolling(window_size).mean()),
        columns=df.columns,
        index=df.index)
    risk_factor = (risk_factor - risk_factor.expanding().mean()
                   ) / risk_factor.expanding().std()
    return risk_factor


@click.option("--how", type=str)
def dropna(input, how):
    ''' chi2noraml transformation
    '''
    df = input
    output = df.dropna()
    return output

def stdout(input):
    ''' chi2noraml transformation
    '''
    df = input
    click.echo(input)
