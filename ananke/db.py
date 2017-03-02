
from twisted.enterprise import adbapi

# https://notoriousno.blogspot.co.uk/2016/08/twisted-klein-database-usage.html

class Database(object):
    
    dbpool = adbapi.ConnectionPool('sqlite3', 'AsyncDB.sqlite', check_same_thread=False)
    
    def _create_db(self, cursor):
        create_stmt = 'CREATE TABLE IF NOT EXISTS slaves (ip TEXT)'
        cursor.execute(create_stmt)

    def create_db(self):
        return self.dbpool.runInteraction(self._create_db)

    def _insert_slave(self, cursor, ip):
        insert_stmt = 'INSERT INTO slaves(ip) VALUES ("%s")' % ip
        cursor.execute(insert_stmt)

    def insert_slave(self, ip):
        return self.dbpool.runInteraction(self._insert_slave, ip)
        
    def _drop_slave(self, cursor, ip):
        del_stmt = 'DELETE FROM slaves WHERE ip="%s"' % ip
        cursor.execute(del_stmt)

    def drop_slave(self, ip):
        return self.dbpool.runInteraction(self._drop_slave, ip)

    def count_slaves(self, cursor):
        return self.dbpool.runQuery('SELECT COUNT(*) FROM slaves')
        
    def _purge_slaves(self,cursor):
        create_stmt = 'DELETE FROM slaves'
        cursor.execute(create_stmt)

    def purge_slaves(self):
        return self.dbpool.runInteraction(self._purge_slaves)    
        
    def get_slaves(self):    
        return self.dbpool.runQuery('SELECT ip FROM slaves')   
        
    