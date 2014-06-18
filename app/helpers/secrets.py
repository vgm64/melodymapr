import socket
import os

def get_API_key():
  return os.environ.get('GOOGLE_API_KEY') or raw_input("Enter API key: ")

def generate_salted_API_key():
  """ This generates the key that is decoded in generate_API_key"""
  hostname = socket.gethostname()
  hostname = hostname*10
  # Insert real API key here, then run this function and save the result.
  API_KEY = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
  key_len = len(API_KEY)
  salted_key = []
  for i in range(key_len):
    key = ord(API_KEY[i]) - ord(hostname[i])
    salted_key.append(str(key))
  return ",".join(salted_key)

def generate_API_key():
  # Salted Key
  salted_key = '-18,-38,12,-8,-16,38,-31,-58,-26,-7,-22,-30,-6,-5,-2,-34,33,-60,4,-15,4,4,38,-26,-42,5,-49,2,0,-64,-33,-40,-49,-63,-57,-65,-51,-9,57'
  salted_key = eval(salted_key)
  # Subtract API 
  key_len = len(salted_key)
  hostname = socket.gethostname()
  hostname = hostname*10
  hostname = hostname[:key_len]
  API_KEY = []
  for i in range(key_len):
    key = ord(hostname[i]) + salted_key[i]
    API_KEY.append( chr(key % 256) )

  return "".join(API_KEY)
