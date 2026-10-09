import importlib.util, math, unittest
from pathlib import Path
P=Path(__file__).with_name("source_recovery.py")
S=importlib.util.spec_from_file_location("r",P); r=importlib.util.module_from_spec(S); S.loader.exec_module(r)

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

if __name__=="__main__": unittest.main()
