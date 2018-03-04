"""
Test suites for `LogAnalyzer` class.

Author: Nikolay Lysenko
"""


import unittest
import logging

from otus_python_homeworks.hw_1.log_analyzer import LogAnalyzer


class TestLogAnalyzer(unittest.TestCase):
    """
    Tests of `CombinedSamplerFromPool` class.
    """

    def test_analyze_logs(self):
        config = {
            "report_size": 1000,
            "report_dir": "./reports",
            "log_dir": "./log"
        }
        log_analyzer = LogAnalyzer(**config)
        log_analyzer.analyze_logs()


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