import pymysql

conexion = pymysql.connect(
    host = 'localhost',
    user = 'root',
    password = '',
    db = 'notpaper',
    port = 3306
)

cur = conexion.cursor()
