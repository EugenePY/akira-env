# AKIRA-Data

The purpose of AKIRA-DATA is to provide a data management tool for <b/> Large-Scale Cross Country Macro</b> Modeling. One main of requirements for factor modeling is to use factor to quantize strength of a country, country strength, which is reflating on the relative strength of it's currency. Building a factor and linking which country it measure is impoortant. AKIRA-DATA is providing a framework to handle this kind of problem.
The Proccess can be decompose into datasource and it's metadata, which indicating which country it evaluate and other infoamtion, like how to create the factor.

## Installation

```
git clone https://github.com/EugenePY/akira-data.git
cd akira-data
python setup.py install
```

## API

## Variable

```python

Variable(symbol, metadata, libname) # storage information

```

## VairablePool: Define API to Variable Maps

```
VariablePool
VariablePool.get
VariablePool.get_batch
```

### Writing new DataTask

```python
from akira_data.db.variables import VariablePool
from akira_data.base import API

class MyAPI(API):
    def get(self, variable, start, end):
        pass

class MyPool(VariablePool):
    con = my_api(host="localhost") # define how to get data

    @classmethod
    def make_variables(cls):
        pass

```


#### Commandline tool

1. Update by VaraibalePool Id

```bash
python -m akira_data update_pool 1 \'20200101\' \'20200201\'
```


#### Kafka

1. Topics
    - Ticker Topic
    - Metadata Topic
    - Dataask Topic[Data-updating]