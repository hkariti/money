from bs4 import BeautifulSoup

class FetchException(Exception):
    def __init__(self, message, response):
        self.message = message
        self.response = response


def get_input_tag(raw_html, name):
    if isinstance(raw_html, BeautifulSoup):
        parsed_html = raw_html
    else:
        parsed_html = BeautifulSoup(raw_html, 'html.parser')
    selected_tags = parsed_html.find_all(name='input', attrs=dict(name=name))
    tags_dict = { x.get('name'): x.get('value') for x in selected_tags }

    return tags_dict
