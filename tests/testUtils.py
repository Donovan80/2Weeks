import json, string, random, unittest

DEFAULT_ALPHABET_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_ALPHABET_LOWER = "abcdefghijklmnopqrstuvwxyz"
DEFAULT_ALPHABET_NUMERIC = "0123456789"
DEFAULT_ALPHABET_SPECIAL = "!#$%&'*+-/=?^_`{|}~@^%()<>.,"

DEFAULT_ALPHABET_ALPHA = DEFAULT_ALPHABET_UPPER+DEFAULT_ALPHABET_LOWER
DEFAULT_ALPHABET_ALPHANUMERIC = DEFAULT_ALPHABET_UPPER+DEFAULT_ALPHABET_LOWER+DEFAULT_ALPHABET_NUMERIC
DEFAULT_ALPHABET_ALL = DEFAULT_ALPHABET_UPPER+DEFAULT_ALPHABET_LOWER+DEFAULT_ALPHABET_NUMERIC+DEFAULT_ALPHABET_SPECIAL

def random_string_generator(alphabet, string_length):
    mypw = ""
    for i in range(string_length):
        next_index = random.randrange(len(alphabet))
        mypw = mypw + alphabet[next_index]
    return mypw

def random_password_generator():
    alphabet = DEFAULT_ALPHABET_ALL
    return random_string_generator(alphabet, 16)

def random_name_generator():
    alphabet = DEFAULT_ALPHABET_ALPHA
    return random_string_generator(alphabet, 12)

def random_email_generator():
    alphabet = DEFAULT_ALPHABET_ALPHANUMERIC+"!#$%&'*+-/=?^_`{|}~"
    return random_string_generator(alphabet, 12)+str('@mixfin.com')

def random_number_generator(max=None):
    if max is None:
        max = 1000
    return random.randint(1,max)

def dump_datetime(value):
    if value is None:
        return None
    return value.strftime("%Y-%m-%d") + "T" + value.strftime("%H:%M:%S")

def dump_date(value):
    if value is None:
        return None
    return value.strftime("%Y-%m-%d")

def percent_difference(baseValue, compareValue):
    return (float(compareValue - baseValue) / baseValue)*100


