import os
import subprocess
import boto3
from urllib.parse import unquote_plus

s3_client = boto3.client('s3')

def video_splitting(event, context):
    input_bucket = '1230683898-input' 
    output_bucket = '1230683898-stage-1'  

    for record in event['Records']:
        if record['s3']['bucket']['name'] == input_bucket:
            object_key = unquote_plus(record['s3']['object']['key'])
            download_path = f'/tmp/{object_key}'
            output_filename = f'{object_key.rsplit(".", 1)[0]}.jpg'  
            output_path = f'/tmp/{output_filename}'

            s3_client.download_file(input_bucket, object_key, download_path)

            ffmpeg_cmd = f"/usr/bin/ffmpeg -i {download_path} -vf 'select=eq(n\\,0)' -vframes 1 {output_path} -y"
            try:
                subprocess.check_call(ffmpeg_cmd, shell=True)
                s3_client.upload_file(
                    Filename=output_path,
                    Bucket=output_bucket,
                    Key=output_filename
                )
            except subprocess.CalledProcessError as e:
                print(f"Error executing FFmpeg: {e}")
                return