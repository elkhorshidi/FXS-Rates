import unittest
from fx_core import parse_rates,latest_rates,compare,route_label

class RatesTests(unittest.TestCase):
    def test_sheet_serial_and_bank_fee(self):
        values=[["timestamp","kind","source","raw","fee","effective","ref","note"],
                [46313.87394016204,"بانک","ملی",247000,0.6,245518],
                [46313.877403101855,"بازار آزاد","بازار",262000,0,262000],
                [46313.88093322917,"کوتاژ","بازار",246000,0,246000]]
        raw,warnings=parse_rates(values)
        self.assertFalse(warnings)
        latest=latest_rates(raw)
        result, market=compare(latest,"بازار",100000)
        self.assertEqual(market,262000)
        self.assertEqual(result.iloc[0]["label"],"کوتاژ")
        bank=result[result["kind"]=="بانک"].iloc[0]
        self.assertAlmostEqual(bank["effective_rate"],245518)
        self.assertAlmostEqual(bank["gap_toman"],16482)
        self.assertAlmostEqual(bank["gap_pct"],16482/262000*100)
        self.assertEqual(route_label("بانک","ملی"),"بانک ملی")
    def test_latest_by_timestamp_not_row_position(self):
        values=[["timestamp","kind","source","raw","fee"],
                ["19/10/2026 12:00","بانک","ملی",200,1],
                ["18/10/2026 12:00","بانک","ملی",300,1],
                ["19/10/2026 13:00","بازار آزاد","بازار",350,0]]
        raw,warnings=parse_rates(values)
        latest=latest_rates(raw)
        self.assertEqual(float(latest[latest["kind"]=="بانک"].iloc[0]["raw_rate"]),200)
    def test_persian_digits(self):
        raw,warnings=parse_rates([["a","b","c","d","e"],["۲۰۲۶/۱۰/۱۸ ۱۲:۰۰","بانک","ملی","۲۴۷٬۰۰۰","۰٫۶"]])
        self.assertEqual(len(raw),1)
        self.assertAlmostEqual(float(raw.iloc[0]["effective_rate"]),245518)
    def test_missing_bank_fee_invalid(self):
        raw, warnings=parse_rates([["a","b","c","d","e"],["2026-10-18","بانک","ملی",250000,""]])
        self.assertTrue(raw.empty)
        self.assertTrue(warnings)

if __name__=="__main__": unittest.main()
