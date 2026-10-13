"""
Consentimiento para el tratamiento de datos biométricos (reconocimiento facial en
servidor). Ley 21.719: el dato biométrico es sensible y requiere consentimiento expreso,
específico e informado, y revocable. Cambiar el texto exige subir VERSION: quien aceptó
una versión anterior debe volver a aceptar antes de capturar su rostro.

La biometría nativa (Face ID/huella del teléfono) NO pasa por acá: el servidor no recibe
ningún dato biométrico en ese flujo.

BORRADOR técnico — el texto final debe revisarlo un abogado (ver docs/legal/).
"""
VERSION = '2026-10-v2'

TEXTO = (
    'Autorizo a KeyServ a capturar una breve secuencia de imágenes de mi rostro para '
    'verificar mi identidad. Las imágenes se procesan al momento y se descartan; solo se '
    'guarda un vector numérico derivado de mi rostro, que se usa únicamente para comparar '
    'futuras verificaciones. Ese vector se conserva mientras mantenga mi cuenta o hasta que '
    'revoque este consentimiento, lo que ocurra primero. Puedo revocarlo en cualquier momento, y al '
    'hacerlo ese vector se elimina. También puedo verificar mi identidad con la biometría '
    'de mi teléfono, o por una vía alternativa sin biometría.'
)
