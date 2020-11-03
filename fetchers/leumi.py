import csv
import datetime
import requests
from transactions.models import Transaction

from retry import retry

from .utils import get_input_tag, FetchException

def parseBankinDat(accounts, bankin):
    c = csv.reader(bankin)
    get_date = lambda d: datetime.datetime.strptime(d, '%d%m%y').date()
    get_account = lambda a: next(filter(lambda x: x.backend_id == a, accounts))
    def parse_entry(e):
        try:
            amount = float(e[3])
            if amount < 0:
                return Transaction(from_account=get_account(e[6]),
                                   transaction_date=get_date(e[1]),
                                   bill_date=get_date(e[1]),
                                   transaction_amount=abs(amount),
                                   billed_amount=abs(amount),
                                   description=e[2],
                                   confirmation=int(e[0]))
            return Transaction(to_account=get_account(e[6]),
                               transaction_date=get_date(e[1]),
                               bill_date=get_date(e[1]),
                               transaction_amount=abs(amount),
                               billed_amount=abs(amount),
                               description=e[2],
                               confirmation=int(e[0]))
        except:
            return None

    transactions = ( parse_entry(l) for l in c )

    return list(filter(None, transactions))

def requests_movements_page(s, data=None, timeout=10):
    url = 'https://hb2.bankleumi.co.il/ebanking/Accounts/ExtendedActivity.aspx?WidgetPar=1'
    marker_phrase = 'תנועות בחשבון'
    if data is None:
        r =  s.get(url, timeout=timeout)
    r = s.post(url, data=data, timeout=timeout)
    if not r.ok or marker_phrase not in r.text:
        raise FetchException("Failed to fetch transactions", response=r)

    return r

def fetch_csv(s, from_date, to_date, encoding='cp862'):
    def query(movements_page):
        d1 = get_input_tag(movements_page.text, '__VIEWSTATE')
        d2 = get_input_tag(movements_page.text, '__EVENTVALIDATION')
        d3 = {
                'ddlTransactionType': '001',
                'ddlTransactionPeriod': '004',
                'dtFromDate$textBox': from_date,
                'dtToDate$textBox': to_date,
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                'hidSaveAsChoice': '',
                'AjaxSaveAS': '',
                'btnDisplayDates.x': '9',
                'btnDisplayDates.y': '10'
            }
        post_data = { **d1, **d2, **d3 }

        return requests_movements_page(s, post_data)

    def get_csv(movements_page):
        url = 'https://hb2.bankleumi.co.il/ebanking/Accounts/ExtendedActivity.aspx?WidgetPar=1'
        d1 = get_input_tag(movements_page.text, '__VIEWSTATE')
        d2 = get_input_tag(movements_page.text, '__EVENTVALIDATION')
        d3 = {
                '__EVENTTARGET': 'BTNSAVE',
                '__EVENTARGUMENT': '',
                'hidSaveAsChoice': 'HASHAVSHEVET',
            }
        post_data = { **d1, **d2, **d3 };

        response = s.post(url=url, data=post_data, cookies=dict(SaveFormat='HASHAVSHEVET'), stream=True)
        if not response.ok:
            raise FetchException("Failed to fetch csv", response=response)

        return response

    csv_response = get_csv(query(requests_movements_page(s)))
    chunk_size = int(csv_response.headers['Content-Length'].split(',')[0].strip())
    content_iter = csv_response.iter_content(chunk_size=chunk_size)
    content_bytes = next(content_iter)
    content_text = content_bytes.decode(encoding)
    content_lines = list(filter(None, content_text.split('\r\n')))

    return content_lines

@retry(requests.ReadTimeout, tries=3, delay=1)
def login(user, passwd, timeout=10):
    url = 'https://hb2.bankleumi.co.il/authenticate'
    url_expires_soon = 'https://hb2.bankleumi.co.il/gotolandingpage'
    marker_phrase = 'ברוך הבא, כניסתך האחרונה'
    expires_soon_phrase = 'תוקף סיסמתך עומד לפוג בקרוב'

    s = requests.sessions.Session()
    login_data = dict(uid=user, password=passwd)
    login_response = s.post(url, data=login_data, timeout=timeout, stream=True)

    if expires_soon_phrase in login_response.text:
        login_response = s.post(url_expires_soon, timeout=timeout, stream=True)

    if not login_response.ok or marker_phrase not in login_response.text:
        raise FetchException("login failed", response=login_response)

    return s

def get_month_transactions(s, month, year, accounts):
    from_date = datetime.date(year, month, 1).strftime('%d/%m/%y')
    inc_month = 1 + (month % 12)
    inc_year = year + month // 12
    to_date = (datetime.date(inc_year, inc_month, 1) - datetime.timedelta(days=1)).strftime('%d/%m/%y')
    
    csv = fetch_csv(s, from_date, to_date)
    return parseBankinDat(accounts, csv)
