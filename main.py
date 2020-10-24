import boto3
from botocore.config import Config
import logging
import subprocess

my_config = Config(
    region_name='eu-west-1'
)

logging.basicConfig(level=logging.INFO)

session = boto3.session.Session(profile_name='cloudwatch')
client = session.client('cloudwatch', config=my_config)
apcaccess_output = subprocess.check_output("apcaccess", shell=True, encoding='utf8')

apcaccess_result = {}
for row in apcaccess_output.split('\n'):
    if ': ' in row:
        key, value = row.split(': ')
        apcaccess_result[key.strip(' .')] = value.strip()

params = ["LINEV", "OUTPUTV", "LOTRANS", "HITRANS", "BATTV", "NOMOUTV", "NOMBATTV", "TIMELEFT", "LOADPCT"]
for param in params:
    value = apcaccess_result[param].split(" ", 1)[0]
    response = client.put_metric_data(
        Namespace='Home/UPS/APC',
        MetricData=[
            {
                'MetricName': param,
                'Value': float(value),
            },
        ]
    )

    logging.info(f"Putting metric for param {param} with value {value}")
    logging.debug(f"API response: {response}")
