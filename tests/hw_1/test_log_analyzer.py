"""
Test suites for `LogAnalyzer` class.

Author: Nikolay Lysenko
"""


import unittest
import logging
import os

from otus_python_homeworks.hw_1.log_analyzer import LogAnalyzer


class TestLogAnalyzer(unittest.TestCase):
    """
    Tests of `LogAnalyzer` class.
    """

    def test_analyze_logs(self):
        config = {
            "report_size": 1000,
            "report_dir": "./reports",
            "log_dir": "./log",
            "ts_path": "/var/tmp/log_analyzer.ts",
            "save_results_as_attr": True
        }
        log_analyzer = LogAnalyzer(**config)
        log_analyzer.analyze_logs()

        self.assertEqual(
            log_analyzer.stats[0]['url'],
            "/api/v2/internal/html5/phantomjs/queue/?wait=1m"
        )
        self.assertEqual(log_analyzer.stats[0]['count'], 2767)
        self.assertAlmostEqual(log_analyzer.stats[0]['count_perc'], 0.106)
        self.assertAlmostEqual(log_analyzer.stats[0]['time_avg'], 62.995)
        self.assertAlmostEqual(log_analyzer.stats[0]['time_max'], 9843.569)
        self.assertAlmostEqual(log_analyzer.stats[0]['time_med'], 60.073)
        self.assertAlmostEqual(log_analyzer.stats[0]['time_perc'], 9.043)
        self.assertAlmostEqual(log_analyzer.stats[0]['time_sum'], 174306.352)

        self.assertEqual(
            log_analyzer.stats[7]['url'],
            "/api/v2/group/7123018/banners"
        )
        self.assertEqual(log_analyzer.stats[7]['count'], 784)
        self.assertAlmostEqual(log_analyzer.stats[7]['count_perc'], 0.03)
        self.assertAlmostEqual(log_analyzer.stats[7]['time_avg'], 13.071)
        self.assertAlmostEqual(log_analyzer.stats[7]['time_max'], 9811.46)
        self.assertAlmostEqual(log_analyzer.stats[7]['time_med'], 0.537)
        self.assertAlmostEqual(log_analyzer.stats[7]['time_perc'], 0.532)
        self.assertAlmostEqual(log_analyzer.stats[7]['time_sum'], 10247.771)

        result_path = os.path.join(
            config['report_dir'], 'report-2017.06.30.html'
        )
        self.assertTrue(os.path.isfile(result_path))
        os.unlink(result_path)


def main():
    msg_format = '[%(asctime)s] %(levelname).1s %(message)s'
    datetime_fmt = '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(
        format=msg_format,
        datefmt=datetime_fmt,
        level=logging.INFO
    )

    test_loader = unittest.TestLoader()
    suites_list = []
    testers = [
        TestLogAnalyzer()
    ]
    for tester in testers:
        suite = test_loader.loadTestsFromModule(tester)
        suites_list.append(suite)
    overall_suite = unittest.TestSuite(suites_list)
    unittest.TextTestRunner().run(overall_suite)


if __name__ == '__main__':
    main()
