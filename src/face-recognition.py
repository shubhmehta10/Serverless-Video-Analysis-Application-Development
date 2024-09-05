import os
import subprocess
import boto3
import numpy as np
import cv2
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

s3_client = boto3.client('s3')

os.environ['TORCH_HOME'] = '/tmp/model_data'

mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

def load_image(bucket_name, image_file_name):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=image_file_name)
        image_data = response['Body'].read()
        image_np = np.frombuffer(image_data, np.uint8)
        image_cv = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        image_pil = Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))
        logging.info(f"Image {image_file_name} loaded successfully.")
        return image_pil
    except Exception as e:
        logging.error(f"Failed to load image {image_file_name} from bucket {bucket_name}: {e}")
        return None

def save_results(bucket_name, file_name, data):
    try:
        s3_client.put_object(Body=data.encode('utf-8'), Bucket=bucket_name, Key=file_name)
        logging.info(f"Results saved to {bucket_name}/{file_name} successfully.")
    except Exception as e:
        logging.error(f"Failed to save results to {bucket_name}: {e}")

def process_image(img):
    try:
        face, prob = mtcnn(img, return_prob=True)
        if face is not None and prob is not None:
            emb = resnet(face.unsqueeze(0)).detach()
            logging.info("Face detected and processed successfully.")
            return emb
        else:
            logging.info("No face detected.")
    except Exception as e:
        logging.error(f"Error processing image: {e}")
    return None

def face_recognition(event, context):
    try:
        for record in event['Records']:
            input_bucket = record['s3']['bucket']['name']  
            image_key = record['s3']['object']['key']  
            output_bucket = '1230683898-output' 

            img = load_image(input_bucket, image_key)
            if img is not None:
                emb = process_image(img)
                if emb is not None:
                    saved_data = torch.load('/home/app/tmp/data.pt')  
                    embedding_list, name_list = saved_data
                    dist_list = [torch.dist(emb, emb_db).item() for emb_db in embedding_list]
                    min_idx = dist_list.index(min(dist_list))
                    recognized_name = name_list[min_idx]
                    result_file_name = f"{os.path.splitext(image_key)[0]}.txt"
                    save_results(output_bucket, result_file_name, recognized_name)
                else:
                    logging.info(f"No face detected in {image_key}")
            else:
                logging.error(f"Failed to load and process image {image_key}")
    except KeyError as e:
        logging.error(f"KeyError encountered in event processing: {e}")
        raise

event = {
    "input_bucket": "1230683898-stage-1",
    "output_bucket": "1230683898-output"
}
context = {}
