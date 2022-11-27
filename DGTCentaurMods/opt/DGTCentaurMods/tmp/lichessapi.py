import berserk
import os
import sys

token = open(os.path.expanduser("~")+'/.lichesstoken').read().strip()

session = berserk.TokenSession(token)
client = berserk.Client(session=session)

try:
	who = client.account.get()
	player = str(who.get('username'))
except:
	print('no token')

print(who)
print(player)
