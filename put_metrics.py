import boto3
from botocore.config import Config
import logging
import subprocess
import time

my_config = Config(
    region_name='eu-west-1'
)

params = ["LINEV", "OUTPUTV", "LOTRANS", "HITRANS", "BATTV", "NOMOUTV", "NOMBATTV", "TIMELEFT", "LOADPCT"]

logging.basicConfig(level=logging.INFO)
session = boto3.session.Session(profile_name='cloudwatch')
cw = session.client('cloudwatch', config=my_config)


def get_ups_data():
    apcaccess_output = subprocess.check_output("apcaccess", shell=True, encoding='utf8')
    apcaccess_result = {}
    for row in apcaccess_output.split('\n'):
        if ': ' in row:
            key, value = row.split(': ')
            apcaccess_result[key.strip(' .')] = value.strip()
    return apcaccess_result


def put_ups_metrics(params):
    values = get_ups_data()
    for param in params:
        value = float(values[param].split(" ", 1)[0])
        unit = values[param].split(" ", 1)[1]
        logging.info(f"Unit for {param}: {unit}")
        if unit == "Percent":
            unit_for_metric = "Percent"
        else:
            unit_for_metric = "None"
        response = cw.put_metric_data(
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


while True:
    put_ups_metrics(params)
    time.sleep(300)
