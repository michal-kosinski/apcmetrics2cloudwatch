import logging
import subprocess
import time

from boto3 import session
from botocore.config import Config


class PutUpsMetricsToCloudWatch:
    BOTO_PROFILE = "cloudwatch"
    BOTO_CONFIG = Config(
        region_name='eu-west-1'
    )

    UPS_PARAMS = ["LINEV", "OUTPUTV", "LOTRANS", "HITRANS", "BATTV", "NOMOUTV", "NOMBATTV", "TIMELEFT", "LOADPCT",
                  "ITEMP", "BCHARGE"]

    logging.basicConfig(level=logging.INFO)
    session = session.Session(profile_name=BOTO_PROFILE)
    cw = session.client('cloudwatch', config=BOTO_CONFIG)

    def __get_ups_metrics(self):
        apcaccess_output = subprocess.check_output("apcaccess", shell=True, encoding='utf8')
        apcaccess_result = {}
        for row in apcaccess_output.split('\n'):
            if ': ' in row:
                key, value = row.split(': ')
                apcaccess_result[key.strip(' .')] = value.strip()
        return apcaccess_result

    def put_ups_metrics(self, params):
        ups_metrics = self.__get_ups_metrics()
        for param in params:
            value = float(ups_metrics[param].split(" ", 1)[0])
            unit = ups_metrics[param].split(" ", 1)[1]
            logging.info(f"Unit for {param}: {unit}")
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

            logging.info(f"Putting metric for param: {param} with unit: {unit_for_metric} and value: {value}")
            logging.debug(f"API response: {response}")


if __name__ == '__main__':
    while True:
        PutUpsMetricsToCloudWatch().put_ups_metrics(PutUpsMetricsToCloudWatch.UPS_PARAMS)
        time.sleep(300)
