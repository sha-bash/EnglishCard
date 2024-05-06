import configparser

class GetTokens:
    @staticmethod
    def get_tokentg():
        config = configparser.ConfigParser()
        config.read('application\config.ini')
        return config.get('Telegram', 'tg_token')
    
    @staticmethod
    def get_wordnik_token():
        config = configparser.ConfigParser()
        config.read('application\config.ini')
        return config.get('Wordnik', 'wordnik_token')


