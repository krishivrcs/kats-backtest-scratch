"""Minimum anti-overclaim tests for the frozen INR300 intraday research model."""
import importlib.util
import sys
import unittest
from datetime import date,datetime
from pathlib import Path

source=Path(__file__).resolve().parents[1]/"system.py"
sys.path.insert(0,str(source.parent))
import system as m

class Tests(unittest.TestCase):
    def setup(self,long=True,range_=6.,stop=None):
        d=date(2024,6,6)
        t=datetime.fromisoformat("2024-06-06T10:06:00+05:30")
        return m.Setup(d,"SBIN",1 if long else -1,t,100.,
                       stop if stop is not None else (99. if long else 101.),
                       1.4,range_,t)

    def test_cost_brokerage_plus_and_gst(self):
        d=date(2025,6,6)
        actual=m.fee_side(100.,100,d,True)
        brokerage=min(30.,10000*.001)
        self.assertGreater(actual,brokerage)
        self.assertGreater(m.fee_side(100.,100,d,False),actual)
        self.assertLess(m.fee_side(100.,100,d,True),30)

    def test_plus_brokerage_cap(self):
        d=date(2025,1,1)
        self.assertAlmostEqual(min(30.,.001*50000),30.)

    def test_risk_target_long(self):
        setup=self.setup()
        plan,state=m.size_and_target(setup,20000,5)
        self.assertEqual(state,"ELIGIBLE")
        self.assertGreater(plan["quantity"],0)
        self.assertLessEqual(plan["planned_risk"],200.000001)
        self.assertGreaterEqual(plan["planned_reward"],300.-1e-6)
        self.assertLessEqual(plan["quantity"]*plan["entry"]+m.fee_side(
            plan["entry"],plan["quantity"],setup.day,True),20000.000001)

    def test_risk_target_short(self):
        s=self.setup(long=False)
        plan,state=m.size_and_target(s,20000,5)
        self.assertEqual(state,"ELIGIBLE")
        self.assertLess(plan["target_raw"],plan["entry"])
        self.assertLessEqual(plan["planned_risk"],200.000001)
        self.assertGreaterEqual(plan["planned_reward"],300-1e-6)

    def test_large_target_refused(self):
        plan,state=m.size_and_target(self.setup(range_=.15),20000,5)
        self.assertIsNone(plan)
        self.assertEqual(state,"TARGET_BEYOND_PRECOMMITTED_RANGE")

    def test_stop_wrong_side_refused(self):
        plan,state=m.size_and_target(self.setup(stop=101),20000,5)
        self.assertIsNone(plan)
        self.assertEqual(state,"INVALID_STOP")

    def test_adverse_slippage_more_costly(self):
        self.assertGreater(m.execute(100,"BUY",15),m.execute(100,"BUY",5))
        self.assertLess(m.execute(100,"SELL",15),m.execute(100,"SELL",5))

    def test_ambiguous_stop_first(self):
        s=self.setup()
        plan={"target_raw":104.}
        raw=m.infra.MinuteBar(s.entry_time,100.,110.,90.,100.,10000.)
        dt,px,reason=m.exit_trade(s,plan,[raw],5.)
        self.assertEqual(reason,"AMBIGUOUS_STOP_FIRST")
        self.assertLessEqual(px,99.)

    def test_mandatory_eod_exit(self):
        s=self.setup()
        minute=datetime.fromisoformat("2024-06-06T15:10:00+05:30")
        raw=m.infra.MinuteBar(minute,101.,101.,101.,101.,1000.)
        dt,price,reason=m.exit_trade(s,{"target_raw":110},[raw],5.)
        self.assertEqual(reason,"TIME_15_10")
        self.assertEqual(dt,minute)

    def test_zero_volume_exit_fail_closed(self):
        s=self.setup()
        raw=m.infra.MinuteBar(s.entry_time,100.,110.,90.,100.,0.)
        with self.assertRaisesRegex(RuntimeError,"DATA_UNSCORABLE"):
            m.exit_trade(s,{"target_raw":104},[raw],5.)

    def test_profit_target_is_net_of_fees(self):
        s=self.setup()
        p,_=m.size_and_target(s,20000,5)
        self.assertGreaterEqual(m.net_profit(p["entry"],p["target_fill"],p["quantity"],s.day,1),300-1e-6)

    def test_no_winners_when_zero_trades(self):
        x=m.metrics([])
        self.assertEqual(x["net_pnl"],0)
        self.assertEqual(x["target_wins"],0)

    def test_no_leakage_partitions(self):
        self.assertLess(m.DEV_END,m.VAL_START)
        self.assertEqual(m.VAL_END,date(2025,10,31))

    def test_no_broker_orders(self):
        t=source.read_text().lower()
        self.assertNotIn("place_order",t)
        self.assertNotIn("upstox_client",t)
        self.assertNotIn("requests.post",t)

if __name__=="__main__":unittest.main()
