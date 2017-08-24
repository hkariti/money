from __future__ import unicode_literals,print_function
import time
import csv
import re
import json


fieldnames_translation = {
        "תאריך": "date",
        "אסמכתא": "confirmation",
        "זכות": "gain",
        "חובה": "loss",
        "יתרה בש\"ח": "balance",
        "תיאור": "description",
        }

def to_date(format):
    def to_date_with_format(date_string):
        return time.strptime(date_string, format)
    return to_date_with_format

def to_float(float_string):
    if not float_string:
        return 0
    return float(float_string)

fields_info = {
        "date": { "type": to_date("%d/%m/%y") },
        "deal_date": { "type": to_date("%d/%m/%Y") },
        "charge_date": { "type": to_date("%d/%m/%Y") },
        "confirmation": { "type": str },
        "gain": { "type": to_float },
        "loss": { "type": to_float },
        "amount": { "type": to_float },
        "amount_ils": { "type": to_float },
        "balance": { "type": to_float },
        "description": { "type": str },
        "notes": { "type": str },
        "currency": { "type": str },
        }

def translate_fieldnames(fields, translation):
    new_names = []
    for i in fields:
        if i in translation:
            new_names.append(translation[i])
        else:
            new_names.append(i)
    return new_names

def convert_types(csv_line):
    for k, v in csv_line.items():
        if k in fields_info:
            try:
                csv_line[k] = fields_info[k]["type"](v)
            except:
                print("Failed to convert {} field value {}".format(k, v))
                raise

def get_movement_type(movement):
    desc = movement['description']
    if re.match('כספומט|בנקט|כספון|סניפומט', desc):
        return 'cash'
    if 'ויזה' in desc:
        return 'visa'
    if 'ךאומי קארד' in desc:
        return 'leumi card'
    if 'ישראכרט' in desc:
        return 'isracard'
    if 'מסטרקארד' in desc:
        return 'mastercard'
    if 'שיק ' in desc:
        if movement['loss'] > 1000 and movement['loss'] < 2000:
            return 'liat'
        return 'cheque'
    if 'העברת משכורת' in desc:
        return 'paycheck'
    if 'הוראת קבע' in desc:
        if movement["loss"] == 2400:
            return 'rent'
    if ' מס' in desc:
        return 'tax'
    if 'נ"ע' in desc or 'בורסה' in desc:
        return 'investment'
    if desc.endswith(' US'):
        return "us trip"
    #return 'other'
    return movement['description']

def get_movement_type_credit(movement, types):
    desc = type_filter(movement['description'])
    return types.get(desc, desc).split('.')[0]

def cluster(movements, ignored_movements=[]):
    cluster='bank'
    clustered = {}
    total_gain = 0
    total_loss = 0
    track = {}
    for l in movements:
        convert_types(l)
        movement_type = get_movement_type(l)
        if movement_type in ignored_movements:
            continue
        if movement_type not in track:
            track[movement_type] = {"gain": 0, "loss": 0}
        total_gain += l['gain']
        total_loss += l['loss']
        track[movement_type]["gain"] += l["gain"]
        track[movement_type]["loss"] += l["loss"]
    for k,v in track.items():
        v['gain_pct'] = v['gain']/total_gain
        v['loss_pct'] = v['loss']/total_loss
        v['type'] = k
        v['cluster'] = cluster
    clustered['track'] = track
    clustered['total_gain'] = total_gain
    clustered['total_loss'] = total_loss
    return clustered

def type_filter(type):
    table = { ord('"'): None, ord('\\'): None }
    return type.translate(table)
def parse_types_file(filename):
    types_file = csv.DictReader(open(filename), ('desc', 'value'))
    types = { type_filter(x['desc']): x['value'] for x in types_file }
    return types

def cluster_credit(movements, ignored_movements=[]):
    cluster='credit'
    clustered = {}
    total_gain = 0
    total_loss = 0
    track = {}
    types = parse_types_file('types')
    for l in movements:
        convert_types(l)
        movement_type = get_movement_type_credit(l, types)
        if movement_type in ignored_movements:
            continue
        if movement_type not in track:
            track[movement_type] = {"gain": 0, "loss": 0}
        total_loss += l['amount_ils']
        track[movement_type]["loss"] += l["amount_ils"]
    for k,v in track.items():
        v['gain_pct'] = 0
        v['loss_pct'] = v['loss']/total_loss
        v['type'] = k
        v['cluster'] = cluster
    clustered['track'] = track
    clustered['total_gain'] = total_gain
    clustered['total_loss'] = total_loss
    return clustered
filename="movements.filtered.csv"
filename_credit="./credit.filtered.csv"

bank = csv.DictReader(open(filename))
credit = csv.DictReader(open(filename_credit))
bank.fieldnames = translate_fieldnames(bank.fieldnames, fieldnames_translation)

ignored_movements = [ 'investment' ]
bank_clustered = cluster(bank, ignored_movements)
credit_clustered = cluster_credit(credit)
for k,v in bank_clustered['track'].items():
    print(json.dumps(v))
for k,v in credit_clustered['track'].items():
    print(json.dumps(v))
