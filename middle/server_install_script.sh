sudo pip install tensorflow tensorflow-serving-api redis Flask

# redis install
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
make test
## if test pass, ignore the latter
## <ignore>
wget http://downloads.sourceforge.net/tcl/tcl8.6.1-src.tar.gz
sudo tar xzvf tcl8.6.1-src.tar.gz  -C /usr/local/
cd  /usr/local/tcl8.6.1/unix/
sudo ./configure
sudo make
sudo make install 
## </ignore>
sudo cp src/redis-server /usr/local/bin/
sudo cp src/redis-cli /usr/local/bin/


# Flask
cd flaskr
sudo apt-get install sqlite3
sqlite3 database/flaskr.db < schema.sql
# python
# # <python>
# from flaskr import init_db
# init_db()
# # </python>