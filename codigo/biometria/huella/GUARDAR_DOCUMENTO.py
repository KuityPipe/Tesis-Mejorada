from datetime import datetime
import CONEXION_BD
import tkinter
from tkinter import filedialog
from pathlib import Path
from fpdf import FPDF


#LLAMAR A LA BASE DE DATOS
cursora = CONEXION_BD.cur
cursorS = CONEXION_BD.cur

#Funcion seleccion mail en base de datos utilizar ID#17
usuarioid = int(input("Introduce el numero de ID del usuario a seleccionar: "))
sql = "SELECT EMAIL FROM USUARIO WHERE ID_USUARIO = %s"
val = (usuarioid)
cursorS.execute(sql,val)
seleccion = cursorS.fetchall()

#Para llamar a los documentos se utilizara el metodo get en la pagina
print("Selecciona archivo para guardar en la tabla")
archivo = filedialog.askopenfilename()
NombreArchi = (Path(archivo).stem)  

print(NombreArchi)

#Convertir el archivo a PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial",size=10)
line = 1

#conversion
fichero = open(str(archivo),"r")
for linea in fichero:
    pdf.cell(600,10,txt=linea,ln=line,align="L")
    if linea[-1]==("\n"):
        linea=linea[:-1]
    line+=1

pdf.output(NombreArchi + ".pdf")

fichero.close()

TimeStamp = datetime.now()
TimeStamp = TimeStamp.strftime("%y-%m-%d %H:%M:%S")

sql1 = "INSERT INTO DOCUMENTO(NOMBRE_DOCUMENTO, ARCHIVO, FECHA_SUBIDA_DOCUMENTO, FK_USUARIO, FK_ESTADO_DOCUMENTO) VALUES(%s,%s,%s,%s,2)"
val1 = (NombreArchi, pdf, TimeStamp, usuarioid)
cursora.execute(sql1,val1)
cursora.connection.commit()
