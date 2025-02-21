import time
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from urllib.parse import urlencode
import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses
from hashlib import md5
from helper.main import get_all_comics_for_characters, get_all_characters, get_characters, get_comics, get_secrets


@pytest.mark.asyncio
async def test_get_characters():
    public_key = "7ce94c5faeb5b8f8c9af500ff2411891"
    private_key = "835fa1e84a80eceae1473e2a79d81d9bdff7ad77"
    timestamp = "1629469956"
    offset = 0

    hash_str = md5(f"{timestamp}{private_key}{public_key}".encode("utf8")).hexdigest()

    mock_response = {
        "code": 200,
        "status": "Ok",
        "data": {
            "offset": 0,
            "limit": 100,
            "total": 1,
            "count": 1,
            "results": [
                {
                    "id": 1011334,
                    "name": "3-D Man",
                    "description": "",
                }
            ]
        }
    }

    base_url = 'http://gateway.marvel.com/v1/public/characters'
    params = {
        "apikey": public_key,
        "ts": timestamp,
        "hash": hash_str,
        "orderBy": "name",
        "limit": 100,
        "offset": offset
    }
    url_with_params = f"{base_url}?{urlencode(params)}"

    with aioresponses() as m:
        m.get(url_with_params, payload=mock_response)

        async with ClientSession() as session:
            response = await get_characters(session, public_key, private_key, timestamp, offset)
            assert response == mock_response


@pytest.mark.asyncio
async def test_get_comics():
    public_key = "7ce94c5faeb5b8f8c9af500ff2411891"
    private_key = "835fa1e84a80eceae1473e2a79d81d9bdff7ad77"
    timestamp = "1629469956"
    character_id = 1011334

    hash_str = md5(f"{timestamp}{private_key}{public_key}".encode("utf8")).hexdigest()

    # Mock the response data
    mock_response = {
        "code": 200,
        "status": "Ok",
        "data": {
            "offset": 0,
            "limit": 100,
            "total": 1,
            "count": 1,
            "results": [
                {
                    "id": 82967,
                    "title": "Avengers: The Initiative (2007) #19",
                    "description": "The Initiative faces the Skrulls!",
                }
            ]
        }
    }

    base_url = f'http://gateway.marvel.com/v1/public/characters/{character_id}/comics'
    params = {
        "apikey": public_key,
        "ts": timestamp,
        "hash": hash_str,
        "orderBy": "title",
        "limit": 100
    }
    url_with_params = f"{base_url}?{urlencode(params)}"

    with aioresponses() as m:
        m.get(url_with_params, payload=mock_response)

        async with ClientSession() as session:
            response = await get_comics(session, public_key, private_key, timestamp, character_id)
            assert response == mock_response


@pytest.mark.asyncio
async def test_get_all_characters():
    public_key = "7ce94c5faeb5b8f8c9af500ff2411891"
    private_key = "835fa1e84a80eceae1473e2a79d81d9bdff7ad77"
    timestamp = str(time.time())

    initial_mock_response = {
        "code": 200,
        "status": "Ok",
        "data": {
            "offset": 0,
            "limit": 100,
            "total": 300,
            "count": 100,
            "results": [{"id": i, "name": f"Character {i}", "description": ""} for i in range(100)]
        }
    }

    additional_mock_responses = [
        {
            "code": 200,
            "status": "Ok",
            "data": {
                "offset": offset,
                "limit": 100,
                "total": 300,
                "count": 100,
                "results": [{"id": i, "name": f"Character {i}", "description": ""} for i in range(offset, offset + 100)]
            }
        }
        for offset in range(100, 300, 100)
    ]

    with patch('helper.main.get_characters', new_callable=AsyncMock) as mock_get_characters:
        mock_get_characters.side_effect = [initial_mock_response] + additional_mock_responses

        characters = await get_all_characters(public_key, private_key)

        expected_character_count = initial_mock_response['data']['total']

        assert len(characters) == expected_character_count

        for i in range(expected_character_count):
            assert characters[i]["id"] == i
            assert characters[i]["name"] == f"Character {i}"


@pytest.mark.asyncio
async def test_get_all_characters():
    public_key = "7ce94c5faeb5b8f8c9af500ff2411891"
    private_key = "835fa1e84a80eceae1473e2a79d81d9bdff7ad77"
    timestamp = str(time.time())

    initial_mock_response = {
        "code": 200,
        "status": "Ok",
        "data": {
            "offset": 0,
            "limit": 100,
            "total": 300,
            "count": 100,
            "results": [{"id": i, "name": f"Character {i}", "description": ""} for i in range(100)]
        }
    }

    additional_mock_responses = [
        {
            "code": 200,
            "status": "Ok",
            "data": {
                "offset": offset,
                "limit": 100,
                "total": 300,
                "count": 100,
                "results": [{"id": i, "name": f"Character {i}", "description": ""} for i in range(offset, offset + 100)]
            }
        }
        for offset in range(100, 300, 100)
    ]

    with patch('helper.main.get_characters', new_callable=AsyncMock) as mock_get_characters:
        mock_get_characters.side_effect = [initial_mock_response] + additional_mock_responses

        characters = await get_all_characters(public_key, private_key)

        assert len(characters) == initial_mock_response['data']['total']

        for i in range(initial_mock_response['data']['total']):
            assert characters[i]["id"] == i
            assert characters[i]["name"] == f"Character {i}"


@pytest.mark.asyncio
async def test_get_all_comics_for_characters():
    public_key = "7ce94c5faeb5b8f8c9af500ff2411891"
    private_key = "835fa1e84a80eceae1473e2a79d81d9bdff7ad77"
    timestamp = str(time.time())

    characters = [
        {"id": 1, "name": "Character 1"},
        {"id": 2, "name": "Character 2"},
        {"id": 3, "name": "Character 3"}
    ]

    mock_responses = [
        {
            "code": 200,
            "status": "Ok",
            "data": {
                "offset": 0,
                "limit": 100,
                "total": 10,
                "count": 10,
                "results": [{"id": i, "title": f"Comic {i}", "description": ""} for i in range(10)]
            }
        }
        for _ in range(len(characters))
    ]

    with patch('helper.main.get_comics', new_callable=AsyncMock) as mock_get_comics:
        mock_get_comics.side_effect = mock_responses

        comics_data = await get_all_comics_for_characters(public_key, private_key, characters)

        for i, character_comics in enumerate(comics_data):
            assert len(character_comics['data']['results']) == mock_responses[i]['data']['total']
            for j, comic in enumerate(character_comics['data']['results']):
                assert comic['title'] == f"Comic {j}"


class TestGetSecrets(unittest.TestCase):

    def test_get_secrets_success(self):
        secrets_manager_client_mock = MagicMock()
        secrets_manager_client_mock.get_secret_value.return_value = {
            'SecretString': '{"public_key": "mock_public_key", "private_key": "mock_private_key"}'
        }

        with unittest.mock.patch('helper.main.secrets_manager_client', secrets_manager_client_mock):
            public_key, private_key = get_secrets()

        self.assertEqual(public_key, "mock_public_key")
        self.assertEqual(private_key, "mock_private_key")




if __name__ == "__main__":
    pytest.main()
