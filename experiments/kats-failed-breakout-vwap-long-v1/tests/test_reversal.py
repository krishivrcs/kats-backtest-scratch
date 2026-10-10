import sys
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import reversal


def five_series(day=date(2024, 5, 2)):
    start=datetime.combine(day,time(9,15),reversal.infra.IST)
    bars=[]
    for i in range(75):
        bars.append(reversal.infra.FiveBar(start+timedelta(minutes=5*i),100,100.5,99.2,100,1000))
    bars[6]=reversal.infra.FiveBar(start+timedelta(minutes=30),99.2,99.3,98.5,98.8,1300)
    bars[7]=reversal.infra.FiveBar(start+timedelta(minutes=35),98.8,100.1,98.6,99.5,1000)
    bars[8]=reversal.infra.FiveBar(start+timedelta(minutes=40),99.4,100,99,99.8,1000)
    return bars


def minute_lookup(day=date(2024, 5, 2)):
    start=datetime.combine(day,time(9,15),reversal.infra.IST)
    return {start+timedelta(minutes=i): reversal.infra.MinuteBar(start+timedelta(minutes=i),99.6,100,99,99.7,200) for i in range(375)}


class ReversalTests(unittest.TestCase):
    def test_reuses_frozen_integrity_module(self):
        self.assertEqual(reversal.infra.ARCHIVE_SHA256, "20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2")

    def test_vwap_is_completed_bar_cumulative_only(self):
        bars=five_series(); values=reversal.cumulative_vwap(bars[:2])
        expected=((bars[0].high+bars[0].low+bars[0].close)/3*bars[0].volume+(bars[1].high+bars[1].low+bars[1].close)/3*bars[1].volume)/(bars[0].volume+bars[1].volume)
        self.assertAlmostEqual(values[-1],expected)

    def test_requires_twenty_prior_sessions(self):
        self.assertIsNone(reversal.candidate_from_five("SBIN",date(2024,5,2),five_series(),[3000]*19,minute_lookup()))

    def test_breakdown_recovery_entry_is_next_bar(self):
        bars=five_series(); c=reversal.candidate_from_five("SBIN",date(2024,5,2),bars,[3000]*20,minute_lookup())
        self.assertIsNotNone(c)
        self.assertEqual(c.recovery_time.time(),time(9,55))
        self.assertEqual(c.entry_time.time(),time(9,56))
        self.assertEqual(c.entry_raw,99.6)

    def test_breakdown_volume_filter(self):
        bars=five_series(); bars[6]=reversal.infra.FiveBar(bars[6].timestamp,99.2,99.3,98.5,98.8,1100)
        self.assertIsNone(reversal.candidate_from_five("SBIN",date(2024,5,2),bars,[3000]*20,minute_lookup()))

    def test_recovery_window_expires(self):
        bars=five_series()
        for i in (7,8,9): bars[i]=reversal.infra.FiveBar(bars[i].timestamp,98.8,99,98,98.7,1000)
        self.assertIsNone(reversal.candidate_from_five("SBIN",date(2024,5,2),bars,[3000]*20,minute_lookup()))

    def candidate(self,target=105,stop=98):
        day=date(2025,1,2); stamp=datetime.combine(day,time(10),reversal.infra.IST)
        return reversal.Candidate(day,"SBIN",1.5,.01,stamp,stamp,stamp,100,stop,target)

    def test_reward_gate_accepts_only_cost_adjusted_ratio(self):
        self.assertGreater(reversal.size_and_reward(20000,self.candidate(105),5)["quantity"],0)
        rejected=reversal.size_and_reward(20000,self.candidate(101),5)
        self.assertEqual(rejected["reason"],"PROSPECTIVE_REWARD")

    def test_risk_and_cash_gate(self):
        sizing=reversal.size_and_reward(20000,self.candidate(105),5)
        self.assertLessEqual(sizing["planned_loss"],200)
        self.assertLessEqual(sizing["quantity"]*sizing["entry"]+reversal.infra.side_costs(sizing["quantity"]*sizing["entry"],buy=True,day=date(2025,1,2))["total"],20000)

    def test_ambiguous_path_is_stop_first(self):
        c=self.candidate(); bar=reversal.infra.MinuteBar(c.entry_time,100,106,97,101,100)
        _,_,reason=reversal.simulate_exit(c,[bar],5)
        self.assertEqual(reason,"AMBIGUOUS_STOP_FIRST")

    def test_gap_through_stop(self):
        c=self.candidate(); bar=reversal.infra.MinuteBar(c.entry_time,97,98,96,97,100)
        _,price,reason=reversal.simulate_exit(c,[bar],5)
        self.assertEqual(reason,"STOP_GAP"); self.assertLess(price,c.stop)

    def test_development_gate_fails_small_sample(self):
        metric={"trades":29,"net_pnl":100,"profit_factor":2,"expectancy":1,"max_drawdown":100,"positive_month_share":1,"net_ex_top_3":1}
        self.assertFalse(reversal.development_pass(metric,metric))

    def test_validation_gate_requires_combined_fifty(self):
        metric={"trades":20,"net_pnl":100,"profit_factor":2,"expectancy":1,"max_drawdown":100,"positive_month_share":1,"net_ex_top_3":1}
        self.assertFalse(reversal.validation_pass(metric,metric,29))


if __name__ == "__main__": unittest.main()

