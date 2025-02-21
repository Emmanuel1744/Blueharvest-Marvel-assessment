import os
import json
import asyncio
from botocore.exceptions import ClientError
from helper.main import main, logger, get_secrets, upload_to_s3, BUCKET_NAME

SECRET_NAME = os.environ.get('SECRET_NAME')
REGION_NAME = os.environ.get('REGION_NAME')


# #def lambda_handler(event, context):

#     try:
#         public_key, private_key = get_secrets()
#         comic_df, character_df = asyncio.run(main(public_key, private_key))
#         upload_to_s3(character_df, BUCKET_NAME, 'characters_data.csv')
#         upload_to_s3(comic_df, BUCKET_NAME, 'comics_data.csv')
#     except ClientError as e:
#         logger.error(f"Failed to retrieve secret: {e}")
#         raise e

#     return {
#         "statusCode": 200,
#         "body": json.dumps("Data uploaded successfully!")
#     }

