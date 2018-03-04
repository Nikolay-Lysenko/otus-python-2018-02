#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
This script aggregates statistics from Nginx logs.
You need Python 3.5 or newer to run it (`typing` module is not
included in prior versions).
To study all possible options of calling the script, execute this
from a terminal: `python log_analyzer.py -h`
"""


import argparse
import logging
import warnings
import os
import datetime
from typing import Dict, Any, Optional


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


class LogAnalyzer:
    """
    Parser of Nginx logs in the specified by homework description
    format.
    """

    def __init__(self, report_size: str, report_dir: str, log_dir: str):
        self.report_size = report_size
        self.report_dir = report_dir
        self.log_dir = log_dir
        self.pattern = "nginx-access-ui.log-"
        logging.info("Instance of `LogAnalyzer` has been created.")

    def __find_newest_log_file(self) -> str:
        # Find a proper file with the most recent date in its name.
        try:
            file_names = os.listdir(self.log_dir)
        except FileNotFoundError as e:
            logging.error("Directory with logs not found.")
            raise e
        ui_log_names = [x for x in file_names if x.startswith(self.pattern)]
        try:
            newest_ui_log_name = sorted(ui_log_names)[-1]
        except IndexError as e:
            logging.error("No UI logs in the directory.")
            raise e
        return newest_ui_log_name

    def __create_report_name(self, newest_ui_log_name: str) -> str:
        # Determine the name of the output report.
        date_from_name = newest_ui_log_name[len(self.pattern):].split('.')[0]
        try:
            log_date = datetime.datetime.strptime(date_from_name, '%Y%m%d')
            date_as_str = log_date.strftime("%Y.%m.%d")
        except Exception as e:
            logging.error("Wrong date format in the log file")
            raise e
        report_name = "report-{}.html".format(date_as_str)
        return report_name

    def __is_job_done(self, report_name: str) -> bool:
        # Check whether log file already has been processed.
        report_path = os.path.join(self.report_dir, report_name)
        return os.path.isfile(report_path)

    def analyze_logs(self) -> type(None):
        """
        Analyze logs according to homework specification.

        :return:
            None (a file is created as a result)
        """
        newest_ui_log_name = self.__find_newest_log_file()
        report_name = self.__create_report_name(newest_ui_log_name)
        if self.__is_job_done(report_name):
            logging.info("Report already exists, skipping.")
            return
        else:
            logging.info("Analysis of log is started.")


def parse_cli_args() -> argparse.Namespace:
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
             'REPORT_SIZE, REPORT_DIR, LOG_DIR, LOGGING_FILE'
    )
    cli_args = parser.parse_args()
    return cli_args


def parse_config_from_file(path_to_config: str) -> Dict[str, Any]:
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
        "LOGGING_FILE": None
    }
    if path_to_config:
        if not os.path.isfile(path_to_config):
            raise FileNotFoundError("No such file: {}".format(path_to_config))
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


def coalesce_settings(cli_args: argparse.Namespace) -> Dict[str, Any]:
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
        "LOGGING_FILE": None
    }
    passed_config = parse_config_from_file(cli_args.config)
    config = {k: passed_config[k] or v for k, v in default_config.items()}
    config = {k.lower(): v for k, v in config.items()}
    return config


def set_logging(logging_filename: Optional[str]) -> type(None):
    """
    Set logging according to homework specification.

    :param logging_filename:
        name of file where logs are written
        or `None` if stdout should be used
    :return:
        None
    """
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
    log_analyzer = LogAnalyzer(**config)
    log_analyzer.analyze_logs()


if __name__ == "__main__":
    main()
