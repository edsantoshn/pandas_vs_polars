import os
import logging
from io import BytesIO


import boto3
import pandas as pd

REGION = os.getenv('REGION', 'us-east-2')

session = boto3.session.Session(
            region_name=REGION)

s3_client = session.client('s3')


def put_csv_file_bucket(filename:str, filecontent:bytes, bucket_name:str):
    try:
        s3_client.put_object(
            Bucket=bucket_name, 
            Key=filename, 
            Body=filecontent,
            ContentType='application/x-parquet')
        return True
    except Exception as exception:
        logging.exception('Putting file to bucket, %s', exception)
        return None


def throw_temp_file(bucket_file_key:str, bucket_name:str):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=bucket_file_key)
        return response['Body'].read()
    except Exception as exception:
        logging.exception('Throwing temp file, %s',exception)
        return None


def delete_file(bucket, key_file):
    try:
        s3_client.delete_object(Bucket=bucket, Key=key_file)
        return True
    except Exception as exception:
        logging.exception('deleting file, %s', exception)
        raise exception


def handler(event, context):
    try:
        file_name_putted = event['Records'][0]['s3']['object']['key']
        bucket = event['Records'][0]['s3']['bucket']['name']
        filecontent = throw_temp_file(bucket_file_key=file_name_putted, bucket_name=bucket)

        dataframe = pd.read_csv(BytesIO(filecontent))

        filecontent_buffer = BytesIO()
        dataframe.to_parquet(filecontent_buffer, engine='pyarrow', compression='zstd')
        filecontent_buffer.seek(0)

        filename = file_name_putted.replace('work/','processed/').replace('.csv', '.parquet')

        put_csv_file_bucket(
            filecontent=filecontent_buffer,
            filename=filename,
            bucket_name=bucket)
        # delete_file(bucket, file_name_putted)
        return True
    except Exception as exception:
        logging.exception('main, %s', exception)
        return None
