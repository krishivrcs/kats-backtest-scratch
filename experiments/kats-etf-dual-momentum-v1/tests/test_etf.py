import importlib.util
import sys
import unittest
from pathlib import Path

src=Path(__file__).resolve().parents[1]/"run.py"
spec=importlib.util.spec_from_file_location("kats_etf",src)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

class TestETF(unittest.TestCase):
    def test_buy_sell_slippage_monotone(self):
        self.assertGreaterEqual(m.price(100,True,15),m.price(100,True,5))
        self.assertLessEqual(m.price(100,False,15),m.price(100,False,5))
    def test_gold_no_sell_stt(self):
        a=m.fees("GOLDBEES",100.,10,False)
        b=m.fees("NIFTYBEES",100.,10,False)
        self.assertAlmostEqual(b-a,.01)
    def test_stamponbuy(self):
        for sym in m.SYMS:
            self.assertGreater(m.fees(sym,100,10,False),m.fees(sym,100,10,True))
    def test_momentum_requires_warmup(self):
        dates=["2022-01-01"]
        self.assertIsNone(m.signal(0,dates,{s:{} for s in m.SYMS}))
    def test_no_live_orders(self):
        t=src.read_text().lower()
        self.assertNotIn("place_order",t)
        self.assertNotIn("upstox_client",t)
    def test_cash_not_leveraged(self):
        self.assertLess(m.fees("NIFTYBEES",100,10,True),5.)
if __name__=="__main__":unittest.main()
