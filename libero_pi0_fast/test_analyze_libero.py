import unittest
from analyze_libero import summarize, wilson

class TestLiberoAudit(unittest.TestCase):
    def test_fifty_rollouts(self):
        data=[{'suite':'libero_spatial','task_id':str(i),'successes':'25','trials':'50'} for i in range(10)]
        got=summarize(data)
        self.assertEqual(got['suites']['libero_spatial']['trials'],500)
        self.assertEqual(got['suites']['libero_spatial']['pooled_success_rate'],.5)
        self.assertTrue(got['suites']['libero_spatial']['all_50_trials'])
    def test_zero_success(self):
        self.assertGreater(wilson(0,50)[1],0)
    def test_duplicate(self):
        row={'suite':'libero_10','task_id':'0','successes':'0','trials':'50'}
        with self.assertRaises(ValueError): summarize([row,row])
    def test_incomplete(self):
        row={'suite':'libero_goal','task_id':'0','successes':'10','trials':'50'}
        self.assertFalse(summarize([row])['overall']['complete_four_suites'])
if __name__ == '__main__': unittest.main()
