import configparser

class GetTokens:

    def get_tokentg():
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config.get('Telegram', 'tg_token')
 
    def get_wordnik_token():
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config.get('Wordnik', 'wordnik_token')


