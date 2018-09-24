#!/usr/bin/python

import os
import json
import re
import subprocess
import sys
import getopt


if  len(sys.argv) != 2 :
	print "usage: " + sys.argv[0] + " <subscription_name>"
	sys.exit()
subscription = sys.argv[1]

subprocess.call(['az', 'account','set', '--subscription' , subscription])
proc = subprocess.Popen(['az', 'account','show', '--query', 'name', '-o', 'json' ] , stdout=subprocess.PIPE)
newsub = proc.stdout.read().replace('"','').rstrip()
if subscription != newsub:
	print "usage: " + sys.argv[0] + " <subscription_name>"
	print "failed to switch to "+sys.argv[1]
	sys.exit()
print 'Subscription:' + subscription
print ""

##### List Database Accounts.
proc = subprocess.Popen(["az", "cosmosdb","list", "--query", "[].{name:name,rg:resourceGroup,location:readLocations[].locationName}", "-o", "json" ] , stdout=subprocess.PIPE)
db_accounts_string = proc.stdout.read()
db_accounts = json.loads(db_accounts_string)
total_cost=0
for db_account in db_accounts :
	sys.stdout.flush()
	region_count=len(db_account['location'] )
	print "\tDBAccount:%s Region: %s" %( db_account['name'] , str( db_account['location'] ) )
	##### List Databases.
	proc = subprocess.Popen(["az", "cosmosdb","database","list", "-n",db_account['name'],"-g", db_account['rg'] , "--query", "[].{id:id}", "-o", "json" ] , stdout=subprocess.PIPE)
	dbs_string= proc.stdout.read()
	dbs = json.loads(dbs_string )
	db_account_total_ru=0
	for db in dbs :
		print "\t\tDatabase:%s" %(db['id'] )
		##### List Collections.
		proc = subprocess.Popen(["az", "cosmosdb","collection","list", "-d", db['id'], "-n",db_account['name'],"-g", db_account['rg'] , "--query", "[].{id:id}", "-o", "json" ] , stdout=subprocess.PIPE)
		colls_string= proc.stdout.read()
		colls = json.loads(colls_string )
		total_ru=0
		for coll in colls :
			##### Get Collection RU.
			proc = subprocess.Popen(["az", "cosmosdb","collection","show", "-c",coll['id'],"-d", db['id'], "-n",db_account['name'],"-g", db_account['rg'] , "--query", "offer.content.offerThroughput", "-o", "json" ] , 
				stdout=subprocess.PIPE)
			ru=int(proc.stdout.read().rstrip())
			print "\t\t\tCollection:%s RU:%d" %(coll['id'], ru)
			total_ru = total_ru + ru
		db_total_ru = total_ru * region_count
		print "\t\tDatabase:%s Total RU(%d) *Region count(%d) = %d" % (db['id'],total_ru,region_count, db_total_ru )
		print "\t\tDatabase:%s Total Monthly Cost: (%d / 100) * 0.008 * 24 * 30 =  %d" % (db['id'], db_total_ru,int( (db_total_ru / 100) * 0.008 * 24 * 30  )  )
		
		sys.stdout.flush()
		db_account_total_ru=db_account_total_ru + db_total_ru
	print "\tDBAccount:%s Total RU:%d Total Monthly Cost:%d" % (  db_account['name'] , db_account_total_ru, int( (db_account_total_ru / 100) * 0.008 * 24 * 30  )  )
	print
	total_cost = total_cost +  int( (db_account_total_ru / 100) * 0.008 * 24 * 30  )  

print 'Subscription:%s Total Monthly Cost:%d' % ( subscription,total_cost)

quit()

