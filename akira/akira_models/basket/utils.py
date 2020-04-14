
def get_model(model_id):
    if model_id == "bmk":
        from baskets.src.passive_model import BasketModel
        return BasketModel

    elif model_id == "factor":
        from baskets.src.passive_model import FactorDynamicBasketModel
        return FactorDynamicBasketModel

    elif model_id == "tvols":
        from baskets.src.passive_model import TVOLS
        return TVOLS

    elif model_id == "mv":
        from baskets.src.passive_model import MinimizeVolatilityModel
        return MinimizeVolatilityModel
    else:
        raise ValueError(f"model_id={model_id} not Found.")