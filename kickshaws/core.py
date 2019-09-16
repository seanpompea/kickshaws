from __future__ import division
from __future__ import print_function
from collections import *
from functools import *
from itertools import *

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import smtplib
from email.mime.text import MIMEText
import json
import platform
import codecs
import datetime
import re
import time
import csv
import cStringIO

__all__ = ['smart_logger'
          ,'send_email'
          ,'slurp'
          ,'slurp_json'
          ,'slurp_csv'
          ,'spit'
          ,'spit_csv'
          ,'get_hostname'
          ,'today_as_str'
          ,'ts'
          ,'select'
          ,'select_indices'
          ,'enum'
          ,'fix_nbsp'
          ,'into_unicode'
          ,'verify_response_content_length'
          ,'seq_of_maps_into_csv_data'
          ,'csv_data_into_seq_of_maps'
          ]

#------------------------------------------------------------------------------

_instantiated_loggers = {}

def smart_logger(tag='default'):
  '''Returns a logger object with the following features:
    - writes to a file './log/'+tag+'.log'
    - facilitates rolling logfiles: up to 16 files, max 32MB each
    - prepends timestamp to all messages
    - prepends filename and function name to messages passed
      into info(), error()
    - calling smart_logger multiple times with the same tag
      returns the _same_ logger object.'''
  global _instantiated_loggers
  logdir = 'log' + os.sep
  if not tag:
    raise ValueError('tag needs to be a non-empty string')
  # create logdir if needed.
  if not os.path.exists(logdir): os.makedirs(logdir)
  # return preexisting logger if exists
  if _instantiated_loggers.has_key(tag):
    return _instantiated_loggers.get(tag)
  # otherwise, instantiate a new one and also store for future.
  else:
    # Instantiate/get logging.Logger object via standard library call.
    x = logging.getLogger(tag)
    # Set level of logging.
    x.setLevel(logging.INFO)
    # Set up logfile cleanup behavior via handler object.
    logpath = logdir + tag + '.log'
    handler = RotatingFileHandler(logpath
                                 ,maxBytes=33554432
                                 ,backupCount=16)
    # Set up log format.
    fmt = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] ' \
            '[%(filename)s:%(lineno)s %(funcName)s] %(message)s')
    handler.setFormatter(fmt)
    x.addHandler(handler)
    _instantiated_loggers[tag] = x
    return x

#------------------------------------------------------------------------------

def send_email(from_addr, to_addr, subj, body):
  '''Sends an email message. Assumes environment has smtp server running.
  Arguments:
    - from-addr: email address as a string
    - to-addr: can be either...
        -- a string with a single address or multiple addresses (if the latter,
           they should be comma-separated);
        -- a list data structure containing one or more separate addresses
           as strings.
    - body and subj should both be strings.
  Regarding errors:
    o All exceptions are passed up to the caller.
    o Specifically, will throw _socket.error_ if the local environment does 
      not provide smtp.'''
  try:
    COMMASPACE = ', '
    msg = MIMEText(body)
    msg['Subject'] = subj
    msg['From'] = from_addr
    if type(to_addr) is list:
      msg['To'] = COMMASPACE.join(to_addr)
    else:
      msg['To'] = to_addr
    # Send the message via our own SMTP server.
    s = smtplib.SMTP('localhost')
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()
  except:
    raise
  return

#------------------------------------------------------------------------------

def slurp(filepath):
  with open(filepath, 'r') as f:
    return f.read()

def slurp_json(filepath):
  with open(filepath, 'r') as f:
    return json.load(f)

def slurp_csv(filepath):
  return csv_data_into_seq_of_maps(slurp(filepath))

def spit(fname, data):
  '''Write to file.
  See also:
  https://clojure.github.io/clojure/clojure.core-api.html#clojure.core/spit
  '''
  if type(data) not in (str, unicode):
    raise TypeError
  prepped = ''
  if type(data) == unicode:
    prepped = data.encode('utf_8')
  else:
    prepped = data
  with open(fname, 'w') as f:
    f.write(prepped)

def spit_csv(fname, data):
  if not isinstance(data, Sequence):
    raise TypeError
  cstringio_obj = seq_of_maps_into_csv_data(data)
  preppedstr = cstringio_obj.getvalue()
  spit(fname, preppedstr)

def get_hostname():
  '''Get hostname for the machine this program is running on.'''
  return platform.node()

def today_as_str():
  '''Current date as a string: yyyy-mm-dd'''
  return datetime.date.today().strftime("%Y-%m-%d")

def ts():
  '''Return current timestamp in milliseconds (as an int).'''
  return int(round(time.time() * 1000))

#------------------------------------------------------------------------------
# data operations

def select(mps, k, v):
  '''Given a list of maps and a key-value pair, return a 
  list (possibly empty) of maps having that key-value 
  pair.'''
  return [mp for mp in mps if mp.get(k) == v]

def select_indices(mps, k, v):
  '''Given a list of maps and a key-value pair, return a 
  list of indices of all the maps containing that
  key-value pair.'''
  return [idx for idx, mp in enumerate(mps) if mp.get(k) == v]

def enum(*items):
  '''Variadic function where all arguments should be
  strings which will become the enum's data members.'''
  key_value_pairs = dict(zip(items, range(len(items))))
  return type('', (), key_value_pairs)

#------------------------------------------------------------------------------
# strings

def fix_nbsp(us):
  '''Convert non-breaking spaces into regular spaces. (Excel is one
  program that sometimes introduces such characters into a file.)'''
  if type(us) is not unicode:
    raise TypeError
  return us.replace(u'\xa0', u' ')

# Regex object for spotting unicode escapes in a raw string.
re_unicode_escapes = re.compile(r'\\u[0-9A-Fa-f]{4}')

def into_unicode(s):
  '''Attempts to convert a raw string into a unicode string
  via a handful of potential encodings. (If you need a more
  thorough approach, try the 'chardet' Python package.)
  Might raise an exception.
  '''
  if type(s) is not str:
    raise TypeError
  UTF_8_SIG = 'utf_8_sig' # handles BOM if present (but works either way)
  UTF_16 = 'utf_16'
  UNICODE_ESCAPE = 'unicode_escape'
  CP1252 = 'cp1252' # For the most part, equiv to Latin1.
  try:
    return unicode(s, encoding=UTF_8_SIG)
  except UnicodeDecodeError:
    pass
  try:
    return unicode(s, encoding=UTF_16)
  except UnicodeDecodeError:
    pass
  try:
    # See if s contains unicode escapes (e.g., '\u00f8')
    if re.search(re_unicode_escapes, s):
      return s.decode(UNICODE_ESCAPE)
  except UnicodeDecodeError:
    pass
  return unicode(s, encoding=CP1252)

#------------------------------------------------------------------------------
# http

def verify_response_content_length(resp):
  '''The requests library honors incomplete reads; use this
  function to check for this. The resp argument should be
  of type requests.models.Response or equivalent. Returns
  boolean. The code for this function (and further
  discussion) comes from:
  https://blog.petrzemek.net/2018/04/22/on-incomplete-http-reads-and-the-requests-library-in-python/
  ''' 
  expected_length = resp.headers.get('Content-Length')
  if expected_length is not None:
    actual_length = resp.raw.tell()
    expected_length = int(expected_length)
    return actual_length == expected_length

#------------------------------------------------------------------------------
# csv data

def csv_data_into_seq_of_maps(data):
  '''data should be a raw string of text representing the equivalent of
  the text in a CSV file.  Returns a sequence of maps.
  A few additional notes:
  DictReader cannot 'do' Unicode, so you cannot pass it an io.StringIO 
  object. Instead, pass raw bytes (data arg)
  into a cStringIO constructor (which can handle raw byte
  strings) and pass that to DictReader.
  Afterward, convert everything into unicode strings, one
  value at a time, as we assemble the final list of maps.
  '''
  if type(data) != str:
    raise TypeError('The function csv_data_into_seq_of_maps expects a raw str.')
  cstringio_obj = cStringIO.StringIO(data)
  reader = csv.DictReader(cstringio_obj)
  out = []
  for row in reader:
    out.append({into_unicode(k) : into_unicode(v) for (k,v) in row.items()})
  return out

def seq_of_maps_into_csv_data(data, include_bom=False):
  '''Takes a sequences of maps. Assumes that all maps have the same keys
  (works OK if a row has fewer keys than the zeroth row; will throw
  a ValueError if any row has a key that the zeroth row doesn't).
  Returns a cStringIO object containing UTF-8-encoded string bytes
  representing the data as it would appear in a CSV file.
  Note that including the BOM helps Excel open the CSV correctly.'''
  cstrio = cStringIO.StringIO()
  if include_bom:
    # (This helps Excel open the CSV correctly).
    cstrio.write(codecs.BOM_UTF8)
  w = csv.DictWriter(cstrio, fieldnames=data[0].keys(),
                     lineterminator=os.linesep)
  w.writeheader()
  for row in data:
    # Python's csv lib cannot 'do' Unicode; convert to UTF-8 first.
    w.writerow({k:v.encode('utf_8') if isinstance(v, unicode)
                else str(v).encode('utf_8')
                for (k,v) in row.items()})
  # Lastly, the writer will leave the buffer pointer pointing to the
  # end of the stream; reset before returning.
  cstrio.seek(0)
  return cstrio

