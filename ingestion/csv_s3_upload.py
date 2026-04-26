import boto3
import datetime
import requests
from os import getcwd

#Path to the csv file 
csv_folder_path = getcwd() + "/data"

# Initialize S3 client
s3 = boto3.client('s3', region_name='us-east-1')

current_date_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

# Mapping of file names to their target S3 folders
folder_map = {
    "stores.csv": "stores",
    "fact.csv": "fact",
    "department.csv": "department"
}

def lambda_handler(event, context):
    """
    Lambda-style function to generate pre-signed URLs for multiple files.
    """
    results = []


    for file_path in event['files']:
        file_name = file_path.split('/')[-1]

        if file_name not in folder_map:
            print(f"Warning: {file_name} not recognized. Skipping.")
            continue

        folder = folder_map[file_name]

        base_name = file_name.split('.')[0]
        timestamped_name = f"{base_name}_{current_date_time}.csv"
        s3_key = f"{folder}/{timestamped_name}"

        # Generate pre-signed URL
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': 'wallmart-pipeline-data',
                'Key': s3_key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=300  # 5 minutes
        )
    
        # Upload file directly using requests
        with open(file_path, 'rb') as f:
            response = requests.put(url, data=f, headers={"Content-Type": "text/csv"})
            if response.status_code == 200:
                print(f"Uploaded {file_name} successfully!")
            else:
                print(f"Failed to upload {file_name}: {response.text}")

        results.append({
            "file_name": file_name,
            "s3_path": s3_key,
            "upload_url": url,
            "status_code": response.status_code
        })

    return results


if __name__ == "__main__":
    # Pass local paths here
    event = {
        "files": [
            f"{csv_folder_path}/stores.csv",
            f"{csv_folder_path}/fact.csv",
            f"{csv_folder_path}/department.csv"
        ]
    }

    urls = lambda_handler(event, None)