from bs4 import BeautifulSoup

def get_input_tag(raw_html, name):
    parsed_html = BeautifulSoup(raw_html, 'html.parser')
    selected_tags = parsed_html.find_all(name='input', attrs=dict(name=name))
    tags_dict = { x.get('name'): x.get('value') for x in selected_tags }

    return tags_dict
