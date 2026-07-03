from mca_model.model.profit_loss import entries as pnl


def test_pnl(model):
    """dummy - test if functions exist"""
    

    
    model.compute(pnl.EBITDA)
    model.compute(pnl.EBIT)
    model.compute(pnl.EBT)
    model.compute(pnl.net_result)


     
