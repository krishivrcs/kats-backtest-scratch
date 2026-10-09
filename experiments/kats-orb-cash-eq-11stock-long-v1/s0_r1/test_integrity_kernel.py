import importlib.util, math, unittest
from pathlib import Path
P=Path(__file__).with_name("source_recovery.py")
S=importlib.util.spec_from_file_location("r",P); r=importlib.util.module_from_spec(S); S.loader.exec_module(r)
FROZEN=P.parents[1]/"s0"/"audit.py"
FS=importlib.util.spec_from_file_location("frozen_s0",FROZEN); frozen=importlib.util.module_from_spec(FS); FS.loader.exec_module(frozen)

class IntegrityKernelTests(unittest.TestCase):
    def test_valid(self): self.assertTrue(r.strict_valid(100,101,99,100,1))
    def test_zero_price(self): self.assertFalse(r.strict_valid(0,101,0,100,1))
    def test_negative_price(self): self.assertFalse(r.strict_valid(-1,101,-2,100,1))
    def test_nonfinite_price(self): self.assertFalse(r.strict_valid(100,math.inf,99,100,1))
    def test_nonfinite_volume(self): self.assertFalse(r.strict_valid(100,101,99,100,math.nan))
    def test_bad_high(self): self.assertFalse(r.strict_valid(100,99,98,100,1))
    def test_bad_low(self): self.assertFalse(r.strict_valid(100,101,101,100,1))
    def test_negative_volume(self): self.assertFalse(r.strict_valid(100,101,99,100,-1))
    def test_legacy_accepts_zero_price_gap(self): self.assertTrue(r.legacy_valid(0,1,0,1,0)); self.assertFalse(r.strict_valid(0,1,0,1,0))
    def test_frozen_s0_accepts_zero_ohlc(self): self.assertTrue(frozen.valid_ohlcv(0,1,0,1,0))
    def test_frozen_s0_accepts_consistent_negative_ohlc(self): self.assertTrue(frozen.valid_ohlcv(-2,-1,-3,-2,0))
    def test_frozen_s0_rejects_nonfinite_and_negative_volume(self):
        self.assertFalse(frozen.valid_ohlcv(1,2,0.5,1,math.nan)); self.assertFalse(frozen.valid_ohlcv(1,2,0.5,1,-1))
    def test_frozen_s0_rejects_invalid_relationship(self): self.assertFalse(frozen.valid_ohlcv(2,1,0,2,1))
    def test_frozen_s0_does_not_gate_duplicates_or_ordering(self):
        source=FROZEN.read_text()
        blocked=source.split("blocked=[",1)[1].split("]",1)[0]
        self.assertNotIn('x["duplicates"]',blocked)
        self.assertNotIn("out_of_order",source)

if __name__=="__main__": unittest.main()
