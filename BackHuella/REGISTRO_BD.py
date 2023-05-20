import CONEXION_BD
from datetime import datetime
import hashlib
import sys

#LLAMAR A LA BASE DE DATOS
cursora = CONEXION_BD.cur

#CREAR NUEVO USUARIO Y INSERTAR DATOS
Rut = int(input("Introduce rut: "))
Nombre = str(input("Introuce el nombre: "))
Nombre2 = str(input("Introuce el segundo nombre: "))
Apellido = str(input("Introduce primer apellido: "))
Apellido2 = str(input("Introduce segundo apellido: "))
Edad = int(input("Introduce edad: "))
Telefono = int(input("Introduce telefono: "))
Email = str(input("Introuce el email: "))
Comuna = int(input("Introduce comuna: "))
Direccion = str(input("Introuce el direccion: "))
Tipo_cuenta = int(input("Introduce el tipo de cuenta a adquirir: [1]gratis [2]individual [3]pyme_pequeña [4]pyme_mediana [5]empresarial "))
Contraseña = str(input("Introduce contraseña: "))
Contraseña2 = str(input("Vuelve a introducir la contraseña: "))

if Contraseña == Contraseña2 :
        hash_object = hashlib.sha256(Contraseña.encode())
        Contraseña = hash_object.hexdigest()
        print(Contraseña)
else:
        print("Contraseña no coincide adios")
        sys.exit()

TimeStamp = datetime.now()
TimeStamp = TimeStamp.strftime("%y-%m-%d %H:%M:%S")
print("Usuario creado a las ", TimeStamp)

sql = "INSERT INTO TRANSACCION(TIEMPO_TRANSACCION, FK_VALOR_CUENTA) VALUES(%s,%s)"
val = (TimeStamp,Tipo_cuenta)
cursora.execute(sql,val)
cursora.connection.commit()
sql = "SELECT ID_TRANSACCION FROM TRANSACCION WHERE TIEMPO_TRANSACCION = %s"
val = (TimeStamp)
cursora.execute(sql,val)
Transaccion = cursora.fetchall()
sql = "INSERT INTO USUARIO(RUT_USUARIO, NOMBRE_USUARIO, NOMBRE2_USUARIO, APELLIDO_USUARIO, APELLIDO2_USUARIO, TELEFONO, EMAIL, DIRECCION_USUARIO, FK_TRANSACCION, FK_TIPO_CUENTA, FK_COMUNA, EDAD, CONTRASEÑA) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
val = (Rut, Nombre, Nombre2, Apellido, Apellido2, Telefono, Email, Direccion, Transaccion, Tipo_cuenta, Comuna, Edad, Contraseña)
cursora.execute(sql,val)
cursora.connection.commit()

