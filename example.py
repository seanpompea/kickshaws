import kickshaws
import sys

'''
# Testing with example.py

Use `example.py` to test the functions and see example log output in
`testlog.txt`.

`example.py` takes two command-line arguments: a "from" email address  and a
"to" email address; as part of testing the ability to pass a list of addresses,
it will also send emails to two nonsense email addresses.

:warning: **Warning:** `example.py` will attempt to send real email via the
local SMTP service if one exists (both to the two passed-in addresses, as well
as two made-up addresses). To avoid this, edit `example.py` and comment out the
relevant lines of code.

Example:

    $ python example.py foo@foo foo@foo

'''

def main():
  '''Run tests of API functions. View results in testlog.txt.
  Takes two command-line arguments: two email addresses (can be fake).
  Note: will attempt to send emails via local SMTP!
  '''
  if len(sys.argv) != 3:
    print 'Takes two email addresses as command-line args (can be fake).' \
          '\nNote: will attempt to use smtp to send to these addresses.'
    sys.exit(1)
  print 'Command-line arguments are: ' + str(sys.argv)
  print 'Will write logs to testlog.txt'

  # create_logger tests
  # -------------------
  print "Testing create_logger function."
  logger = kickshaws.create_logger('testlog.txt', 'Test')
  # strings
  logger.info('Kickshaws library!')
  logger.error('An error! Don\'t worry!')
  # integers
  logger.info(1147)
  logger.error(1147)
  # exception
  try:
    raise Exception("Raising exception on purpose.")
  except Exception, ex:
    logger.error(ex)

  # send_email tests
  # ----------------
  print "Testing send_email function."
  from_addr = sys.argv[1]
  to_addr = sys.argv[2]
  try:
    kickshaws.send_email(from_addr, to_addr, "Kickshaws Test"
                        , "Lorem Ipsum")
  except Exception, e:
    logger.error('Got exception (might not have smtp on this machine): ' + str(e))
  # Now try with a list.
  to_addr = ['foo@bar', 'baz@faz']  
  try:
    logger.info("Test the passing of a list of addresses " \
                "(They're made up this time).")
    kickshaws.send_email(from_addr, to_addr, "X", "Y")
  except Exception, e:
    logger.error('Got exception (might not have smtp on this machine): ' + str(e))
  print 'Done! Exiting.'

if __name__ == '__main__':
  main()

