#!/usr/bin/env python3

import logging
import subprocess
import time

from boto3 import session
from botocore.config import Config


class LoggerConfig:
    LOG_LEVEL = "INFO"

    def __init__(self, class_name):
        self.handler = logging.StreamHandler()
        self.logger = logging.getLogger(class_name)

    def return_logger(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_level = logging.getLevelName(self.LOG_LEVEL)
        self.handler.setFormatter(formatter)
        self.handler.setLevel(log_level)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(log_level)
        return self.logger


class PutUpsMetricsToCloudWatch:
    BOTO_PROFILE = "cloudwatch"
    BOTO_CONFIG = Config(
        region_name='eu-west-1'
    )
    UPS_PARAMS = ["LINEV", "OUTPUTV", "LOTRANS", "HITRANS", "BATTV", "NOMOUTV", "NOMBATTV", "TIMELEFT", "LOADPCT",
                  "ITEMP", "BCHARGE"]
    PUBLISH_INTERVAL_IN_SECONDS = 300

    def __init__(self):
        self.logger = LoggerConfig(class_name=self.__class__.__name__).return_logger()
        self.session = session.Session(profile_name=self.BOTO_PROFILE)
        self.cw = self.session.client('cloudwatch', config=self.BOTO_CONFIG)

    @staticmethod
    def __get_ups_metrics():
        apcaccess_output = subprocess.check_output("apcaccess", shell=True, encoding='utf8')
        apcaccess_result = {}
        for row in apcaccess_output.split('\n'):
            if ': ' in row:
                key, value = row.split(': ')
                apcaccess_result[key.strip(' .')] = value.strip()
        return apcaccess_result

    def put_ups_metrics(self, ups_params=UPS_PARAMS):
        ups_metrics = self.__get_ups_metrics()
        for param in ups_params:
            value = float(ups_metrics[param].split(" ", 1)[0])
            unit = ups_metrics[param].split(" ", 1)[1]
            self.logger.debug(f"Unit for {param}: {unit}")
            if unit == "Percent":
                unit_for_metric = "Percent"
            else:
                unit_for_metric = "None"
            response = self.cw.put_metric_data(
                Namespace='Home/UPS/APC',
                MetricData=[
                    {
                        'MetricName': param,
                        'Dimensions': [
                            {
                                'Name': 'Units',
                                'Value': unit
                            },
                        ],
                        'Value': value,
                        'Unit': unit_for_metric,
                    },
                ]
            )
            self.logger.info(f"Putting metric for param: {param} with unit: {unit_for_metric} and value: {value}")
            self.logger.debug(f"API response: {response}")


while True:
    PutUpsMetricsToCloudWatch().put_ups_metrics()
    time.sleep(PutUpsMetricsToCloudWatch.PUBLISH_INTERVAL_IN_SECONDS)
