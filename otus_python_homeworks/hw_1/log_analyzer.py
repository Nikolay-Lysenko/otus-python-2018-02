# -*- coding: utf-8 -*-


"""
This script aggregates statistics from Nginx logs.
To study all possible options of calling the script, execute this
from a terminal: `python log_analyzer.py -h`.
To launch this script with default settings, execute:
`python log_analyzer.py`.
"""


import argparse
import logging
import warnings
import os
import re
import time
import datetime
import json
import gzip
from collections import defaultdict


class LogAnalyzer(object):
    """
    Analyzer of Nginx logs in the specified by homework description
    format.
    """

    def __init__(
            self,
            report_size,                   # type: str
            report_dir,                    # type: str
            log_dir,                       # type: str
            ts_path,                       # type: str
            max_unparsed_lines_ratio=0.2,  # type: float
            save_results_as_attr=False     # type: bool
            ):
        self.report_size = report_size
        self.report_dir = report_dir
        self.log_dir = log_dir
        self.ts_path = ts_path
        self.max_unparsed_lines_ratio = max_unparsed_lines_ratio
        self.save_results_as_attr = save_results_as_attr
        self.stats = None
        self.__pattern = "nginx-access-ui.log-"
        self.__n_of_parsed_lines = None
        self.__total_request_time = None
        logging.info("Instance of `LogAnalyzer` has been created.")

    def __find_newest_log_file(self):
        # type: () -> str
        # Find a proper file with the most recent date in its name.
        try:
            file_names = os.listdir(self.log_dir)
        except IOError as e:
            logging.error("Directory with logs not found.")
            logging.exception(e)
            raise e
        ui_log_names = [x for x in file_names if x.startswith(self.__pattern)]
        try:
            newest_ui_log_name = sorted(ui_log_names)[-1]
        except IndexError as e:
            logging.error("No proper UI logs in the directory.")
            logging.exception(e)
            raise e
        return newest_ui_log_name

    def __create_report_path(self, log_name):
        # type: (str) -> bool
        # Determine the name of the output report.
        date_from_name = log_name[len(self.__pattern):].split('.')[0]
        try:
            log_date = datetime.datetime.strptime(date_from_name, '%Y%m%d')
            date_as_str = log_date.strftime("%Y.%m.%d")
        except Exception as e:
            logging.error("Wrong date format in the log file")
            logging.exception(e)
            raise e
        report_name = "report-{}.html".format(date_as_str)
        report_path = os.path.join(self.report_dir, report_name)
        return report_path

    @staticmethod
    def __is_job_done(report_path):
        # type: (str) -> bool
        # Check whether log file already has been processed.
        return os.path.isfile(report_path)

    @staticmethod
    def __generate_lines(file_path):
        # type: (str) -> Generator[str, None, None]
        # Generate lines of a specified file one by one.
        if file_path.endswith('.gz'):
            open_fn = gzip.open
        else:
            open_fn = open
        with open_fn(file_path) as source_file:
            for line in source_file:
                yield str(line)

    def __parse_log_file(self, log_name):
        # type: (str) -> List[Dict[str, Any]]
        # Parse specified file and load result into operating memory.
        log_path = os.path.join(self.log_dir, log_name)
        log_lines = self.__generate_lines(log_path)
        line_pattern = re.compile(
            r"(?P<remote_addr>[\d.]+)\s+"
            r"(?P<remote_user>\S*)\s+"
            r"(?P<http_x_real_ip>\S*)\s+"
            r"\[(?P<time_local>.*?)\]\s+"
            r'"(?P<request>.*?)"\s+'
            r"(?P<status>\d+)\s+"
            r"(?P<body_bytes_sent>\S*)\s+"
            r'"(?P<http_referer>.*?)"\s+'
            r'"(?P<http_user_agent>.*?)"\s+'
            r'"(?P<http_x_forwarded_for>.*?)"\s+'
            r'"(?P<http_X_REQUEST_ID>.*?)"\s+'
            r'"(?P<http_X_RB_USER>.*?)"\s+'
            r"(?P<request_time>\d+\.\d+)\s*"
        )
        log = [
            line_pattern.match(line.lstrip("b\'")).groupdict()
            for line in log_lines
        ]
        logging.info("Logs are loaded to operating memory.")
        return log

    def __get_rid_of_unparsed_lines(self, log):
        # type: (List[Dict[str, Any]]) -> List[Dict[str, Any]]
        # Check that number of unparsed lines is not too big and drop them.
        is_parsed_mask = [x is None for x in log]
        ratio = sum(is_parsed_mask) / len(log)
        if ratio > self.max_unparsed_lines_ratio:
            msg = "{} percent of lines can not be parsed.".format(100 * ratio)
            logging.info(msg)
        log = [x for x in log if x is not None]
        return log

    def __memorize_total_stats(self, log):
        # type: (List[Dict[str, Any]]) -> type(None)
        # Store overall statistics in class attributes.
        self.__n_of_parsed_lines = len(log)
        self.__total_request_time = sum(
            [
                float(x['request_time'])
                for x in log
                if x['request_time'] not in ['-']
            ]
        )

    @staticmethod
    def __extract_url_from_request(log_record):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        # Extract URL from logged request and create a key for it.
        log_record.update(
            {'url':
                log_record['request']
                .replace('GET ', '')
                .replace('POST ', '')
                .split(' ')[0]
             }
        )
        return log_record

    def __group_by_url(self, log):
        # type: (List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Any]]]
        # Change data structure that stores the log in operating memory.
        log = [
            self.__extract_url_from_request(log_record)
            for log_record in log
        ]
        columns = [key for key in log[0].keys() if key != 'url']
        grouped_log = defaultdict(lambda: {col: [] for col in columns})
        for log_line in log:
            for column in columns:
                grouped_log[log_line['url']][column].append(log_line[column])
        logging.info("Log lines are grouped by URL.")
        return grouped_log

    @staticmethod
    def __drop_missing_values(
            log  # type: Dict[str, Dict[str, List[Any]]]
            ):
        # type: (...) -> Dict[str, Dict[str, List[Any]]]
        # Drop placeholders of missings.
        missing_placeholders = ['-']
        log = {
            url: dict(
                **{
                    k: v
                    if k != 'request_time'
                    else [float(x) for x in v if x not in missing_placeholders]
                    for k, v in url_stats.items()
                })
            for url, url_stats in log.items()
        }
        return log

    def __compute_stats(self, log):
        # type: (Dict[str, Dict[str, List[Any]]]) -> List[Dict[str, Any]]
        # Compute required in the task statistics.
        stats = []
        for url, url_stats in log.items():
            stats.append(
                {
                    'url': url,
                    'count': len(url_stats['request']),
                    'count_perc': round(
                        100.0
                        * len(url_stats['request'])
                        / self.__n_of_parsed_lines,
                        3
                     ),
                    'time_sum': sum(url_stats['request_time']),
                    'time_perc': round(
                        100.0
                        * sum(url_stats['request_time'])
                        / self.__total_request_time,
                        3
                    ),
                    'time_avg': round(
                        float(sum(url_stats['request_time']))
                        / len(url_stats['request_time']),
                        3
                    ),
                    'time_max': max(url_stats['request_time']),
                    'time_med': (
                        sorted(url_stats['request_time'])
                        [len(url_stats['request_time']) // 2]
                    )
                }
            )
        logging.info("Statistics are computed.")
        return stats

    def __keep_only_top_urls(self, stats):
        # type: (List[Dict[str, Any]]) -> List[Dict[str, Any]]
        # Reduce size of the report.
        stats = sorted(stats, key=lambda x: x['time_sum'], reverse=True)
        n_urls = min([self.report_size, len(stats)])
        return stats[:n_urls]

    def __save_as_html(
            self,
            stats,                   # type: List[Dict[str, Any]]
            report_path,             # type: str
            sample_report_path=None  # type: Optional[str]
            ):
        # type: () -> type(None)
        # Save results in the required format.
        if sample_report_path is None:
            sample_report_path = os.path.join(self.report_dir, 'report.html')
        with open(sample_report_path) as sample_file:
            template = sample_file.read()
        report = template.replace('$table_json', json.dumps(stats))
        with open(report_path, "w") as out_file:
            out_file.write(report)
        logging.info("Report is saved.")

    def __report_success(self):
        # Create a timestamp file that is a sign of successful exit.
        with open(self.ts_path, 'w') as ts_file:
            ts_file.write(str(time.time()))

    def analyze_logs(self):
        # type: (...) -> type(None)
        """
        Analyze logs according to homework specification.

        :return:
            None (a file is created as a result)
        """
        log_name = self.__find_newest_log_file()
        report_path = self.__create_report_path(log_name)
        if self.__is_job_done(report_path):
            logging.info("Report already exists, skipping.")
            return
        else:
            logging.info("Analysis of log is started.")
        log = self.__parse_log_file(log_name)
        log = self.__get_rid_of_unparsed_lines(log)
        self.__memorize_total_stats(log)
        log = self.__group_by_url(log)
        log = self.__drop_missing_values(log)
        stats = self.__compute_stats(log)
        stats = self.__keep_only_top_urls(stats)
        self.__save_as_html(stats, report_path)
        if self.save_results_as_attr:
            self.stats = stats
        self.__report_success()


def parse_cli_args():
    # type: () -> argparse.Namespace
    """
    Parse arguments passed via Command Line Interface (CLI).

    :return:
        namespace with arguments
    """
    parser = argparse.ArgumentParser(description='Logs statistics')
    parser.add_argument(
        '-c', '--config', type=str, default='',
        help='path to file with configuration, this file must contain lines '
             'of the form: "KEY value" where KEY must be one of these: '
             'REPORT_SIZE (number of top URLS to be included), '
             'REPORT_DIR (directory where report file will be created), '
             'LOG_DIR (directory that contains initial logs), '
             'LOGGING_FILE (full path to file where logs of script execution '
             'will be created, by default stdout is used instead of a file), '
             'TS_PATH (full path to file where timestamp of last successful '
             'call is stored).'
    )
    cli_args = parser.parse_args()
    return cli_args


def parse_config_from_file(path_to_config):
    # type: (str) -> Dict[str, Any]
    """
    Extract settings from a user-defined file.

    :param path_to_config:
        path to user-defined config file
    :return:
        configuration of log analyzer from user-defined file
    """
    passed_config = {
        "REPORT_SIZE": None,
        "REPORT_DIR": None,
        "LOG_DIR": None,
        "MAX_UNPARSED_LINES_RATIO": None,
        "LOGGING_FILE": None,
        "TS_PATH": None
    }
    if path_to_config:
        if not os.path.isfile(path_to_config):
            raise IOError("No such file: {}".format(path_to_config))
        with open(path_to_config, 'r') as config_file:
            for line in config_file:
                split_line = line.split(' ')
                if len(split_line) != 2:
                    warnings.warn(
                        "Found line not in 'KEY value' format, skipping",
                        RuntimeWarning
                    )
                    continue
                key, value = split_line[0], split_line[1]
                passed_config[key] = value
    return passed_config


def coalesce_settings(cli_args):
    # type: (argparse.Namespace) -> Dict[str, Any]
    """
    Override default config values with user-defined ones if there
    are any.

    :param cli_args:
        CLI arguments
    :return:
        final configuration of log analyzer
    """
    default_config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./reports",
        "LOG_DIR": "./log",
        "MAX_UNPARSED_LINES_RATIO": 0.2,
        "LOGGING_FILE": None,
        "TS_PATH": "/var/tmp/log_analyzer.ts"
    }
    passed_config = parse_config_from_file(cli_args.config)
    config = {k: passed_config[k] or v for k, v in default_config.items()}
    config = {k.lower(): v for k, v in config.items()}
    return config


def set_logging(logging_filename):
    # type: (Optional[str]) -> type(None)
    """
    Set logging according to homework specification.

    :param logging_filename:
        name of file where logs are written
        or `None` if stdout should be used
    :return:
        None
    """
    if logging_filename is not None:
        logging_dir = os.path.dirname(logging_filename)
        if not os.path.isdir(logging_dir):
            os.makedirs(logging_dir)
    msg_format = '[%(asctime)s] %(levelname).1s %(message)s'
    datetime_fmt = '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(
        filename=logging_filename,
        format=msg_format,
        datefmt=datetime_fmt,
        level=logging.INFO
    )
    logging.info("Logging is set.")


def main():
    cli_args = parse_cli_args()
    config = coalesce_settings(cli_args)
    logging_filename = config.pop('logging_file')
    set_logging(logging_filename)
    try:
        log_analyzer = LogAnalyzer(**config)
        log_analyzer.analyze_logs()
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
    main()
