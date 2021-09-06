import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions

from transactions.models import Transaction

def parse_transaction(account, value_list):
    date = datetime.datetime.strptime(value_list[0], '%d/%m/%Y').date()
    description = value_list[1].strip()
    confirmation = int(value_list[2])
    income = float(value_list[3].strip().replace(',', '') or 0)
    expense = float(value_list[4].strip().replace(',', '') or 0)

    if income:
        from_account = None
        to_account = account
        amount = income
    elif expense:
        from_account = account
        to_account = None
        amount = expense
    else:
        raise ValueError("Empty transaction")

    return Transaction(from_account=from_account, to_account=to_account, transaction_date=date,
            bill_date=date, transaction_amount=amount, billed_amount=amount,
            original_currency='ILS', description=description, confirmation=confirmation)

def fetch_raw_transactions(driver, month, year):
    movement_link = WebDriverWait(driver, 30).until(lambda d: d.find_element(By.LINK_TEXT, "תנועות בחשבון"))
    try:
        # Close a message popup if it exists
        driver.find_element_by_class_name('ui-dialog').find_element_by_class_name('ui-button').click()
    except NoSuchElementException:
        pass
    movement_link.click()
    #print("Clicked on movement")
    WebDriverWait(driver, 30).until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, "תנועות בטווח תאריכים"))).click()
    #print("Clicked on date range")
    WebDriverWait(driver, 30).until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, "תנועות בטווח תאריכים"))).click()
    from_date = datetime.date(year, month, 1).strftime('%d/%m/%Y')
    inc_month = 1 + (month % 12)
    inc_year = year + month // 12
    to_date = (datetime.date(inc_year, inc_month, 1) - datetime.timedelta(days=1)).strftime('%d/%m/%Y')
    #print("Waiting for date element")
    from_date_element = WebDriverWait(driver, 30).until(expected_conditions.visibility_of_element_located((By.ID, 'fromDate')))
    from_date_element.clear()
    from_date_element.send_keys(from_date)
    till_date_element = driver.find_element_by_id('tillDate')
    till_date_element.clear()
    till_date_element.send_keys(to_date)
    driver.find_element_by_xpath("//input[@value='הצג']").click()

    table = WebDriverWait(driver, 30).until(lambda d: d.find_element(By.ID, "dataTable077"))
    rows = table.find_elements_by_tag_name('tr')[:]
    #time.sleep(1)

    raw_transactions = []
    for r in rows:
        c = [ d.text for d in r.find_elements_by_tag_name('td') ]
        raw_transactions.append(c)

    return raw_transactions

def init():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    return driver

def login(username, password):
    driver = init()
    driver.get("https://www.bankotsar.co.il/wps/portal/")
    driver.find_element(By.LINK_TEXT, "כניסה לחשבונך").click()
    driver.switch_to.frame(1)
    WebDriverWait(driver, 30).until(lambda d: d.find_element(By.ID, "username"))
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    WebDriverWait(driver, 30).until_not(lambda d: driver.find_element(By.ID, "continueBtn").click())
    driver.switch_to.default_content()

    return driver

def get_month_transactions(driver, month, year, accounts):
    raw_transactions = fetch_raw_transactions(driver, month, year)
    account = accounts[0]
    
    transactions = []
    for t in raw_transactions:
        try:
            transactions.append(parse_transaction(account, t))
        except:
            pass
    return transactions
