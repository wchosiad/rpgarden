# This code found in Kathan Shah's answer to
# https://stackoverflow.com/questions/21903411/enable-python-to-connect-to-mysql-via-ssh-tunnelling


import pymysql
import paramiko
import pandas as pd
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder
from os.path import expanduser

home = expanduser('~')
#mypkey = paramiko.RSAKey.from_private_key_file(home + pkeyfilepath)
# if you want to use ssh password use - ssh_password='your ssh password', bellow

sql_hostname = 'something.someserver.org'
sql_username = 'someuser'
sql_password = 'abd123'
sql_main_database = 'somedatabase'
sql_port = 3306
ssh_host = 'somesshhost'
ssh_user = 'somesshuser'
ssh_port = 22
sql_ip = '1.1.1.1.1'

with SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        # ssh_pkey=mypkey,
        ssh_password='W1wrd@tt',
        remote_bind_address=(sql_hostname, sql_port)) as tunnel:
    conn = pymysql.connect(host='127.0.0.1', user=sql_username,
            passwd=sql_password, db=sql_main_database,
            port=tunnel.local_bind_port)
    #query = '''SELECT VERSION();'''
    query = '''SELECT humidity from rpgarden;'''
    data = pd.read_sql_query(query, conn)
    print(data)
    conn.close()