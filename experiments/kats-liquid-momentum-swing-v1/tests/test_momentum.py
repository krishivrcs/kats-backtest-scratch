"""Causal sizing, filters and accounting regressions."""
import importlib.util
import sys
import unittest
from datetime import date,timedelta
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]/"run.py"
spec=importlib.util.spec_from_file_location("kats_swing_mom_v1",SRC)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

class SwingTests(unittest.TestCase):
    def test_fees_increase_with_quantity(self):
        d=date(2025,1,15)
        self.assertGreater(m.charges(100,20,d,True),m.charges(100,10,d,True))
        self.assertGreater(m.charges(100,10,d,False),m.charges(100,10,d,True))
    def test_risk_cash_cap(self):
        n=m.quantity(20000,1000.,950.,date(2025,1,1),5)
        self.assertGreaterEqual(n,1)
        e=m.exec_buy(1000.,5)
        s=m.exec_sell(950.,5)
        costs=m.charges(e,n,date(2025,1,1),True)+m.charges(s,n,date(2025,1,1),False)
        self.assertLessEqual((e-s)*n+costs,200.000001)
        self.assertLessEqual(n*e+m.charges(e,n,date(2025,1,1),True),20000.000001)
    def test_no_quantity_if_stop_above_entry(self):
        self.assertEqual(m.quantity(20000,1000,1001,date(2025,1,1),5),0)
    def test_adverse_execution(self):
        self.assertGreater(m.exec_buy(100,10),m.exec_buy(100,5))
        self.assertLess(m.exec_sell(100,10),m.exec_sell(100,5))
    def test_stop_no_same_day_high_lookahead(self):
        self.assertFalse(m.signal_exit_on_close(
            [m.Daily(date(2025,1,1)+timedelta(days=i),100,101,99,100,1e6) for i in range(11)],10,1))
    def test_flat_without_input(self):
        empty={s:[] for s in m.SYMBOLS}
        self.assertIsNone(m.choose(date(2025,1,1),empty,{s:{} for s in m.SYMBOLS}))
    def test_metrics_accounting(self):
        records=[{"net_pnl":10.,"gross_pnl":17.,"costs":7.,"exit_date":"2025-01-01"},
                 {"net_pnl":-5.,"gross_pnl":0.,"costs":5.,"exit_date":"2025-01-08"}]
        x=m.stats(records,2)
        self.assertAlmostEqual(x["net_pnl"],5.)
        self.assertAlmostEqual(x["ending_equity"],20005.)
        self.assertAlmostEqual(x["profit_factor"],2.)
        self.assertEqual(x["trades"],2)
    def test_frozen_periods(self):
        self.assertLess(m.DEV_END,m.VAL_START)
        self.assertEqual(m.VAL_END,date(2025,10,31))
    def test_no_broker_imports(self):
        txt=SRC.read_text()
        self.assertNotIn("place_order",txt)
        self.assertNotIn("upstox_client",txt)

if __name__=="__main__":unittest.main()
