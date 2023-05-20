import IMAGEN_HUELLA
import CONEXION_BD
from fpdf import FPDF

#Guardar Huella en base de datos en la firma, para luego comprobarla con una alerta

#Tengo que añadir una pagina exclusiva en el pdf para guardar la firma
#ademas que llame la otra clase de autentificacion 
#para realizar una autentificacion para ver si la firma es correcta

#LLAMAR A LA BASE DE DATOS
cursora = CONEXION_BD.cur
cursorS = CONEXION_BD.cur

pdf =FPDF()

pdf.open("Imprimir para motivacion y traducir.pdf")