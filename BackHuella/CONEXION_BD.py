from flask import Flask, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configura los detalles de tu base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'notpaper'

mysql = MySQL(app)

@app.route('/regiones', methods=['GET'])
def get_regiones():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM region")
    data = cursor.fetchall()
    return jsonify(data)

@app.route('/comunas/<int:id_region>', methods=['GET'])
def get_comunas(id_region):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM comuna WHERE id_region = %s", (id_region,))
    data = cursor.fetchall()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=3306)

"""
import pymysql

conexion = pymysql.connect(
    host = 'localhost',
    user = 'root',
    password = '',
    db = 'notpaper',
    port = 3306
)

cur = conexion.cursor()
"""