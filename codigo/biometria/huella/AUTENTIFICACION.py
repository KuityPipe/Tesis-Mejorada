"""
LEGACY / DEPRECADO (Fase 3): este script sigue dependiendo de `CONEXION_BD.cur`
(que no existe realmente, ver CODE_ANALYSIS_FINDINGS.md) y es un flujo CLI
con `input()`, no un endpoint real. La decisión de arquitectura (Fase 2) es
consolidar el envío del código de verificación como una vista Django, no
seguir manteniendo este script aparte — ver docs/NEW_CODE_CREATED.md.

Lo único que se corrigió acá, porque no podía esperar a esa migración: tenía
una contraseña de correo real en texto plano hardcodeada en el código fuente
(un secreto de verdad, no un placeholder). Ahora se lee desde variables de
entorno — ver `.env.example` (SMTP_USER/SMTP_PASSWORD). Si ves esto y las
variables no están seteadas, el script falla al loguearse al SMTP en vez de
usar un secreto expuesto.
"""
from email.message import EmailMessage
from datetime import datetime
import smtplib
import random
import hashlib
import os
import CONEXION_BD

#LLAMAR A LA BASE DE DATOS
cursora = CONEXION_BD.cur
cursorS = CONEXION_BD.cur

#Funcion codigo aleatorio
Codigop1 = (random.randint(0,9))
Codigop2 = (random.randint(0,9))
Codigop3 = (random.randint(0,9))
Codigop4 = (random.randint(0,9))
Codigop5 = (random.randint(0,9))
print("Tu codigo aleatorio es: ", Codigop1, Codigop2, Codigop3, Codigop4, Codigop5)
print(Codigop1, Codigop2, Codigop3, Codigop4, Codigop5)
CodigoAl = [Codigop1, Codigop2, Codigop3, Codigop4, Codigop5]


#Funcion seleccion mail en base de datos utilizar ID#17
usuarioid = int(input("Introduce el numero de ID del usuario a seleccionar: "))
sql = "SELECT EMAIL FROM USUARIO WHERE ID_USUARIO = %s"
val = (usuarioid)
cursorS.execute(sql,val)
seleccion = cursorS.fetchall()


#Seleccionar desde la base de datos mail del cliente solicitado
# Antes: email personal hardcodeado en el código fuente. Ahora sale de .env.
remitente = os.environ.get('SMTP_USER')
destinatario = seleccion
mensaje = CodigoAl
hash_object = hashlib.md5(str(mensaje).encode('utf-8'))
CodigoProcesado = hash_object.hexdigest()
print(CodigoProcesado)

#Funcion para enviar el mail desde la 
email = EmailMessage()
email["From"] = remitente
email["To"] = destinatario
email["Subject"] = "¡Enviado desde Python!"
email.set_content(str(CodigoProcesado) + " Tu codigo es : " + str(CodigoAl))

#Protocolo SMTP con modulo smtplimb, creando una conexion con el servidor necesario atravez del dominio o ip que tenga el servidor
#smtp = smtplib.SMTP("smtp.outlook.com")

#Si se usa el protocolo TLS:
# El puerto del protocolo TLS es generalmente 587.
smtp = smtplib.SMTP("smtp.outlook.com", port=587)
# Iniciar la conexión segura vía TLS.
smtp.starttls()

#smtp = smtplib.SMTP_SSL("smtp.outlook.com")

smtp.login(remitente, os.environ.get('SMTP_PASSWORD'))
smtp.sendmail(remitente, destinatario, email.as_string())
smtp.quit()

TimeStamp = datetime.now()
TimeStamp = TimeStamp.strftime("%y-%m-%d %H:%M:%S")
print("Autentificacion a las ", TimeStamp)

codigop1 = int(input("ingresa el primer digito: "))
codigop2 = int(input("ingresa el segundo digito: "))
codigop3 = int(input("ingresa el tercer digito: "))
codigop4 = int(input("ingresa el cuarto digito: "))
codigop5 = int(input("ingresa el quinto digito: "))
codigoAl = [codigop1, codigop2, codigop3, codigop4, codigop5]
print(codigoAl)
print(codigop1, codigop2, codigop3, codigop4, codigop5)

if CodigoAl == codigoAl:
    #Resultado bueno
    sql = "INSERT INTO AUTENTIFICACION(CODIGO_AUTENTIFICACION, FECHA_AUTENTIFICACION, FK_USUARIO_AUTENTIFICACION, FK_ESTADO_AUTENTIFICACION) VALUES(%s,%s,%s,1)"
    val = (CodigoProcesado,TimeStamp,usuarioid)
    cursora.execute(sql,val)
    cursora.connection.commit()
if CodigoAl != codigoAl:
    #Resultado con codigo erroneo
    sql = "INSERT INTO AUTENTIFICACION(CODIGO_AUTENTIFICACION, FECHA_AUTENTIFICACION, FK_USUARIO_AUTENTIFICACION, FK_ESTADO_AUTENTIFICACION) VALUES(%s,%s,%s,2)"
    val = (CodigoProcesado,TimeStamp,usuarioid)
    cursora.execute(sql,val)
    cursora.connection.commit()





