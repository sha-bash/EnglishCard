from application.get_tokens import GetTokens
import requests


class WordnikAPI:
    def __init__(self):
        self.api_url = 'http://api.wordnik.com/v4'
        self.api_key = GetTokens.get_wordnik_token()
        self.headers = {'Accept': 'application/json'}
        self.params = {
            'api_key': self.api_key,
            'hasDictionaryDef': 'true',
            'minDictionaryCount': '1',
            'minLength': '5'
        }

    def get_random_words(self, limit=10):
        params = self.params.copy()
        params.update({'limit': limit})
        response = requests.get(f'{self.api_url}/words.json/randomWords', params=params, headers=self.headers)
        response.raise_for_status()
        return [item['word'] for item in response.json()]