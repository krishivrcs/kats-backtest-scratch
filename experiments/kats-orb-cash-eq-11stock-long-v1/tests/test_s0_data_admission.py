import csv, gzip, hashlib, importlib.util, io, json, tempfile, unittest, zipfile
from datetime import date, datetime, timezone
from pathlib import Path

ROOT=Path(__file__).parents[1]; MOD=ROOT/"s0"/"audit.py"
spec=importlib.util.spec_from_file_location("s0audit",MOD); a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

def payload(rows):
    b=io.StringIO(); w=csv.writer(b); w.writerow(a.EXPECTED_COLUMNS); w.writerows(rows)
    return gzip.compress(b.getvalue().encode())

def row(dt,o=100,h=101,l=99,c=100,v=10):
    return [int(dt.replace(tzinfo=timezone.utc).timestamp()),o,h,l,c,"","",v]

class S0Tests(unittest.TestCase):
    def setUp(self):
        self.parts={"qa":["2024-04-01","2024-10-14"],"development":["2024-10-15","2024-10-31"],"validation":["2024-11-01","2025-10-31"],"sealed_holdout":["2025-11-01","2026-04-30"]}
    def zipstats(self, rows):
        with tempfile.TemporaryDirectory() as d:
            z=Path(d)/"x.zip"
            with zipfile.ZipFile(z,"w") as f:f.writestr("stocks/SBIN_1m.csv.gz",payload(rows))
            with zipfile.ZipFile(z) as f:return a.audit_member(f,"stocks/SBIN_1m.csv.gz",self.parts)
    def test_epoch_utc_to_ist(self): self.assertEqual(a.to_ist("0").strftime("%H:%M"),"05:30")
    def test_member_resolution(self):
        with tempfile.TemporaryDirectory() as d:
            z=Path(d)/"x.zip"
            with zipfile.ZipFile(z,"w") as f:f.writestr("x/HAL_1m.csv.gz",b"x")
            with zipfile.ZipFile(z) as f:self.assertEqual(a.locate_members(f,["HAL"])["HAL"],"x/HAL_1m.csv.gz")
    def test_duplicate_and_missing_minute(self):
        base=datetime(2024,4,1,3,45); rows=[row(base),row(base),row(base.replace(minute=47))]
        x=self.zipstats(rows); self.assertEqual(x["duplicates"],1); self.assertGreater(x["partitions"]["qa"]["missing_minutes"],0)
    def test_invalid_ohlcv(self): self.assertFalse(a.valid_ohlcv(100,99,101,100,1))
    def test_nonfinite(self): self.assertFalse(a.valid_ohlcv(100,101,99,float("nan"),1))
    def test_off_grid(self):
        x=self.zipstats([row(datetime(2024,4,1,3,45,1))]); self.assertEqual(x["off_grid"],1)
    def test_holdout_strategy_guard(self):
        with self.assertRaises(a.HoldoutAccessError): a.assert_strategy_access_allowed(date(2025,11,1),self.parts)
    def test_holdout_output_guard(self):
        with self.assertRaises(AssertionError): a.ensure_holdout_safe({"sealed_holdout":{"entry_price":1}})
        a.ensure_holdout_safe({"sealed_holdout":{"rows":1,"missing_minutes":2}})
    def test_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); z=d/"x.zip"; z.write_bytes(b"bad")
            cfg=d/"c.json"; cfg.write_text(json.dumps({"archive_sha256":"0","symbols":[],"partitions":{},"archive_url":"x","corporate_actions":{}}))
            with self.assertRaises(SystemExit): a.run(z,cfg,d/"o")
    def test_entry_timing_blocker_is_frozen(self):
        cfg=json.loads((ROOT/"s0"/"source_expected.json").read_text()); self.assertEqual(cfg["entry_timing_status"],"REQUIRED_BEFORE_SIMULATION")
    def test_no_strategy_engine_import(self):
        source=MOD.read_text(); self.assertNotIn("backtest import",source); self.assertNotIn("calculate_pnl",source)
    def test_expected_universe_exact(self):
        cfg=json.loads((ROOT/"s0"/"source_expected.json").read_text()); self.assertEqual(len(cfg["symbols"]),11); self.assertIn("HAL",cfg["symbols"]); self.assertIn("TATAMOTORS",cfg["symbols"])

if __name__=="__main__": unittest.main()
