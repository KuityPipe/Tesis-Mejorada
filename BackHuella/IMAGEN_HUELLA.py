from PIL import Image
import math
import hashlib
import sys

#Cargar imagen
def carga(img):
    arr = img.load()
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            arr[x,y] = img.getpixel((x,y))
    return arr
Huella = Image.open("CODIGOS_PY/Huella Imagen/imagenInput/ejemplohuella.png").convert("L")
#Llama a la funcion para convertir la imagen en datos(pixeles)
cargaDato = carga(Huella)
Huella.save("CODIGOS_PY/Huella Imagen/imagenOutput/cargahuella.png")
Huella.show()

#Binarizacion, convierte a valores binarios los colores de la huella digital
def binarizacion (img,umbral):
    arrBina = img.load()
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixel = img.getpixel((x,y))
            if pixel > umbral:
                arrBina[x,y] = 255
            else:
                arrBina[x,y] = 0
    return arrBina
Huella = Image.open("CODIGOS_PY/Huella Imagen/imagenOutput/cargahuella.png").convert("L")
cargaBina = binarizacion(Huella,128)
Huella.save("CODIGOS_PY/Huella Imagen/imagenOutput/Binarihuella.png")
Huella.show()

#Adelgazamiento imagen evita el ruido al poner la huella en caso de movimiento en el lector
def adelgazamiento(img,mascaraH,mascaraV):
    arrAdel = img.load()        
    
    Ha = mascaraH[0][0]
    Hb = mascaraH[0][1]
    Hc = mascaraH[0][2]
    Hd = mascaraH[1][0]
    He = mascaraH[1][1]
    Hf = mascaraH[1][2]
    Hg = mascaraH[2][0]
    Hh = mascaraH[2][1]
    Hi = mascaraH[2][2]

    Va = mascaraV[0][0]
    Vb = mascaraV[0][1]
    Vc = mascaraV[0][2]
    Vd = mascaraV[1][0]
    Ve = mascaraV[1][1]
    Vf = mascaraV[1][2]
    Vg = mascaraV[2][0]
    Vh = mascaraV[2][1]
    Vi = mascaraV[2][2]
    
    for x in range(1,img.size[0]-1):
        for y in range(1,img.size[1]-1):
            Ia = img.getpixel((x-1,y-1))
            Ib = img.getpixel((x-1,y))
            Ic = img.getpixel((x-1,y+1))
            Id = img.getpixel((x,y-1))
            Ie = img.getpixel((x,y))
            If = img.getpixel((x,y+1))
            Ig = img.getpixel((x+1,y-1))
            Ih = img.getpixel((x+1,y))
            Ii = img.getpixel((x+1,y+1))
            Gx = Ha*Ia+Hb*Ib+Hc*Ic+Hd*Id+He*Ie+Hf*If+Hg*Ig+Hh*Ih+Hi*Ii
            Gy = Va*Ia+Vb*Ib+Vc*Ic+Vd*Id+Ve*Ie+Vf*If+Vg*Ig+Vh*Ih+Vi*Ii
            valor = math.sqrt(Gx*Gx+Gy*Gy)
            if valor>255.0:
                valor=255.0
            arrAdel[x-1,y-1] = int(valor)
    return arrAdel

img = Image.open("CODIGOS_PY/Huella Imagen/imagenOutput/Binarihuella.png").convert("L")
thiningX = [[0.0 ,0.0, 0.0],
            [0.0 ,1.0, 0.0],
            [1.0 ,1.0, 1.0],
            
            [1.0 ,0.0, 0.0],
            [1.0 ,1.0, 0.0],
            [1.0 ,0.0, 0.0],
            
            [1.0 ,1.0, 1.0],
            [0.0 ,1.0, 0.0],
            [0.0 ,0.0, 0.0],
                       
            [0.0 ,0.0, 1.0],
            [0.0 ,1.0, 1.0],
            [0.0 ,0.0, 1.0]]
          

thiningY = [[0.0,  0.0,  0.0],
            [1.0,  1.0,  0.0],
            [0.0,  1.0,  0.0],
            
            [0.0 ,1.0, 0.0],
            [1.0 ,1.0, 0.0],
            [0.0 ,0.0, 0.0],
            
            [0.0 ,1.0, 0.0],
            [0.0 ,1.0, 1.0],
            [0.0 ,0.0, 0.0],
                       
            [0.0 ,0.0, 0.0],
            [0.0 ,1.0, 1.0],
            [0.0 ,1.0, 0.0]]


I =  adelgazamiento(img,thiningX,thiningY)
img.save("CODIGOS_PY/Huella Imagen/imagenOutput/Adelgahuella.png")
img.show()

#Poda Pule los bordes de la huella
def poda(img,mascaraH,mascaraV):
    arrPoda = img.load()        
    
    Ha = mascaraH[0][0]
    Hb = mascaraH[0][1]
    Hc = mascaraH[0][2]
    Hd = mascaraH[1][0]
    He = mascaraH[1][1]
    Hf = mascaraH[1][2]
    Hg = mascaraH[2][0]
    Hh = mascaraH[2][1]
    Hi = mascaraH[2][2]

    Va = mascaraV[0][0]
    Vb = mascaraV[0][1]
    Vc = mascaraV[0][2]
    Vd = mascaraV[1][0]
    Ve = mascaraV[1][1]
    Vf = mascaraV[1][2]
    Vg = mascaraV[2][0]
    Vh = mascaraV[2][1]
    Vi = mascaraV[2][2]
    
    for x in range(1,img.size[0]-1):
        for y in range(1,img.size[1]-1):
            Ia = img.getpixel((x-1,y-1))
            Ib = img.getpixel((x-1,y))
            Ic = img.getpixel((x-1,y+1))
            Id = img.getpixel((x,y-1))
            Ie = img.getpixel((x,y))
            If = img.getpixel((x,y+1))
            Ig = img.getpixel((x+1,y-1))
            Ih = img.getpixel((x+1,y))
            Ii = img.getpixel((x+1,y+1))
            Gx = Ha*Ia+Hb*Ib+Hc*Ic+Hd*Id+He*Ie+Hf*If+Hg*Ig+Hh*Ih+Hi*Ii
            Gy = Va*Ia+Vb*Ib+Vc*Ic+Vd*Id+Ve*Ie+Vf*If+Vg*Ig+Vh*Ih+Vi*Ii
            valor = math.sqrt(Gx*Gx+Gy*Gy)
            if valor>255.0:
                valor=255.0
            arrPoda[x-1,y-1] = int(valor)
    return arrPoda

img = Image.open("CODIGOS_PY/Huella Imagen/imagenOutput/Adelgahuella.png").convert("L")
pruningX = [[0.0 ,0.0, 0.0],
            [0.0 ,1.0, 0.0],
            [0.0 ,0.0, 0.0]]
          

pruningY = [[0.0,  0.0,  0.0],
            [0.0,  1.0,  0.0],
            [0.0,  0.0,  0.0]]


I =  poda(img,thiningX,thiningY)
img.save("CODIGOS_PY/Huella Imagen/imagenOutput/Podahuella.png")
img.show()

#Continuar con guardar la huela en la base de datos y hacer una comprobacion de hash#
def archivo_hash(img):
    imghash = hashlib.sha256()
    with open(img,'rb') as file:
        x = 0
        while x != b'':
            x = file.read()
            imghash.update(x)
    return imghash.hexdigest()

img = Image.open("CODIGOS_PY/Huella Imagen/imagenOutput/Podahuella.png").convert("L")

salida_hash = archivo_hash("CODIGOS_PY/Huella Imagen/imagenOutput/Podahuella.png")
print(salida_hash)

codigo = open('CODIGOS_PY/Contraseña dactilar/CodigoHuella.txt','w')
codigo.write(salida_hash)
codigo.close()













