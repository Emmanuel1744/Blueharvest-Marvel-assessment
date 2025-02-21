import asyncio
import aiohttp
import time
import logging
import json
import os
import boto3
import pandas as pd
from hashlib import md5
from botocore.exceptions import ClientError

# API_PUBLIC_KEY = os.environ.get("PUBLIC_KEY")
# API_PRIVATE_KEY = os.environ.get("PRIVATE_KEY")
# BUCKET_NAME = os.environ.get("BUCKET_NAME")
# s3_client = boto3.client('s3')
# secrets_manager_client = boto3.client('secretsmanager')
API_PUBLIC_KEY = "bb48bfb3bc2678f6b8beffa7d4392587"
API_PRIVATE_KEY = "5888027da25ee05452edf19ae437c1e68bed4e30"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_characters(async_session, public_key, private_key, timestamp, offset=0):
    """
    Fetch Marvel characters from the API.

    Args:
        async_session (aiohttp.ClientSession): Asynchronous session object.
        public_key (str): Marvel API public key.
        private_key (str): Marvel API private key.
        timestamp (str): Current timestamp.
        offset (int): Offset for pagination.

    Returns:
        dict: JSON response containing Marvel characters data.
    """
    hash_str = md5(f"{timestamp}{private_key}{public_key}".encode("utf8")).hexdigest()
    url = 'http://gateway.marvel.com/v1/public/characters'
    params = {
        "apikey": public_key,
        "ts": timestamp,
        "hash": hash_str,
        "orderBy": "name",
        "limit": 100,
        "offset": offset
    }
    async with async_session.get(url, params=params, ssl=False) as response:
        return await response.json()


async def get_comics(async_session, public_key, private_key, timestamp, character_id):
    """
    Fetch comics for a specific Marvel character.

    Args:
        async_session (aiohttp.ClientSession): Asynchronous session object.
        public_key (str): Marvel API public key.
        private_key (str): Marvel API private key.
        timestamp (str): Current timestamp.
        character_id (int): ID of the Marvel character.

    Returns:
        dict: JSON response containing comics data for the character.
    """
    hash_str = md5(f"{timestamp}{private_key}{public_key}".encode("utf8")).hexdigest()
    url = f'http://gateway.marvel.com/v1/public/characters/{character_id}/comics'
    params = {
        "apikey": public_key,
        "ts": timestamp,
        "hash": hash_str,
        "orderBy": "title",
        "limit": 100
    }
    async with async_session.get(url, params=params, ssl=False) as response:
        return await response.json()


async def get_all_characters(public_key, private_key):
    """
    Fetch all Marvel characters asynchronously.

    Args:
        public_key (str): Marvel API public key.
        private_key (str): Marvel API private key.

    Returns:
        list: List of dictionaries containing Marvel characters data.
    """
    async with aiohttp.ClientSession(trust_env=True) as async_session:
        timestamp = str(time.time())

        # Fetch the first 100 characters to know the total amount available
        response = await get_characters(async_session, public_key, private_key, timestamp)
        total = response['data']['total']
        characters = response['data']['results']

        # Fetch remaining characters asynchronously
        tasks = []
        for offset in range(100, total, 100):
            tasks.append(get_characters(async_session, public_key, private_key, timestamp, offset))

        additional_characters = await asyncio.gather(*tasks)
        for data in additional_characters:
            characters.extend(data['data']['results'])

        return characters


async def get_all_comics_for_characters(public_key, private_key, characters):
    """
    Fetch comics for all Marvel characters asynchronously.

    Args:
        public_key (str): Marvel API public key.
        private_key (str): Marvel API private key.
        characters (list): List of dictionaries containing Marvel characters data.

    Returns:
        list: List of dictionaries containing comics data for all characters.
    """
    async with aiohttp.ClientSession(trust_env=True) as async_session:
        timestamp = str(time.time())
        tasks = []
        for character in characters:
            tasks.append(get_comics(async_session, public_key, private_key, timestamp, character['id']))
            logger.info(tasks)

        comics_data = await asyncio.gather(*tasks)
        return comics_data


def get_secrets():
    """
    Retrieve Marvel API keys from AWS Secrets Manager.

    Returns:
        tuple: Public and private keys.
    """
    secret_name = 'MarvelAPISecrets'
    try:
        response = secrets_manager_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        public_key = secret['public_key']
        private_key = secret['private_key']
        return public_key, private_key
    except ClientError as e:
        logger.error(f"Failed to retrieve secrets: {e}")
        raise e


def upload_to_s3(df, bucket_name, key):

    """
    Upload a DataFrame to an S3 bucket as a CSV file.

    Args:
        df (pd.DataFrame): DataFrame to upload.
        bucket_name (str): S3 bucket name.
        key (str): S3 object key.
    """
    csv_buffer = pd.io.common.StringIO()
    df.to_csv(csv_buffer, index=False)
    response = s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=csv_buffer.getvalue()
    )
    logger.info(f"Uploaded {key} to S3 bucket {bucket_name}")

def save_to_local(df, file_path):
    """
    Save a DataFrame to a local file as a CSV.

    Args:
        df (pd.DataFrame): DataFrame to save.
        file_path (str): Path to the local file.
    """
    df.to_csv(file_path, index=False)
    logger.info(f"Saved DataFrame to {file_path}")


async def main(public_key, private_key):
    """
    Main function to fetch Marvel characters and their comics data.

    Args:
        public_key (str): Marvel API public key.
        private_key (str): Marvel API private key.
    """
    logger.info("Function Started Successfully")
    characters = await get_all_characters(public_key, private_key)
    comics_data = await get_all_comics_for_characters(public_key, private_key, characters)

    character_columns = ["Character ID", 'Character Name', 'Comic Count']
    comic_columns = ["Character ID", "Comic ID", "Comic Title", "Comic Issue Number"]

    character_data = [(item['id'], item['name'], item['comics']['available']) for item in characters]
    comic_data = []
    for char_index, character in enumerate(characters):
        for comic in comics_data[char_index]['data']['results']:
            comic_data.append((character['id'], comic['id'], comic['title'], comic['issueNumber']))

    character_df = pd.DataFrame(character_data, columns=character_columns)
    comic_df = pd.DataFrame(comic_data, columns=comic_columns)
    logger.info(comic_df)
    logger.info(character_df)

    logger.info("Run Successful")

    return comic_df, character_df


# run this to test locally
if __name__ == "__main__":
    comic_df, character_df = asyncio.run(main(API_PUBLIC_KEY, API_PRIVATE_KEY))
    save_to_local(character_df, 'characters_data.csv')
    save_to_local(comic_df,'comics_data.csv')
