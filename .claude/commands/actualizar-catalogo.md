# Agente de Actualización de Catálogo RELUVSA

Eres el agente encargado de actualizar los datos del catálogo RELUVSA desde un archivo Excel.

## Flujo Completo

### Paso 1: Verificar el archivo borrador
Buscar `data/borrador-catalogo.xlsx` y validar:

1. **Estructura**: Debe tener exactamente 22 columnas con estos headers:
   - Col 0: Clave (SKU)
   - Col 1: Grupo -> Nombre
   - Col 2: SKU
   - Col 3: Codigo de Barras
   - Col 4: Departamento -> Nombre
   - Col 5: Marcas Prodcuto -> Nombre
   - Col 6: Ultima Venta
   - Col 7: Última Compra
   - Col 8: Dias sin venta
   - Col 9: Descripcion
   - Col 10: Precio Tres C/IVA
   - Col 11: Precio Cinco C/IVA
   - Col 12: Precio abierto 3 C/IVA (precio_publico)
   - Col 13: Precio abierto 5 C/IVA (precio_mayoreo)
   - Col 14: Variant Scr (imagen_url)
   - Col 15-20: Inventario por sucursal
   - Col 21: Total Almacenes (inventario_total)

2. **Calidad de datos**:
   - Total de filas con datos
   - SKUs únicos vs duplicados (reportar duplicados)
   - Productos con inventario >0 vs sin inventario
   - Precios en $0 y precios negativos
   - Productos sin descripción
   - Comparación con BD actual (cuántos se actualizan, cuántos son nuevos, cuántos quedarán con inv=0)

3. **Nombre de la hoja**: Verificar el nombre exacto de la hoja del Excel. Si difiere del configurado en `backend/scripts/actualizar_precios_excel.py` (variable `SHEET_NAME`), corregirlo antes de ejecutar.

4. **Presentar resumen** al usuario y esperar confirmación para continuar.

### Paso 2: Renombrar y ejecutar
Una vez que el usuario confirme:

1. Renombrar: `cp data/borrador-catalogo.xlsx data/limpieza-catalogo.xlsx`
2. Ejecutar: `cd backend && python3 scripts/actualizar_precios_excel.py` (timeout 10 min)
3. Mostrar resumen de la actualización

### Paso 3: Deploy
1. Copiar BD: `cp backend/data/catalogo.db data/catalogo.db`
2. Commit: `git add backend/data/catalogo.db data/catalogo.db` + cualquier archivo modificado del script
3. Mensaje de commit: `"Update precios e inventario [Mes] [Año]"`
4. Push a main

## Notas Importantes
- Los precios en el Excel ya vienen CON IVA
- SKUs se normalizan quitando ceros iniciales en numéricos
- Productos nuevos se insertan solo si: inventario > 0 AND última compra < 5 años
- Productos en BD que no están en Excel → inventario se pone en 0
- **Productos existentes con descripción cambiada**: el script detecta cambios en la
  columna Descripcion y re-procesa al producto en modo MERGE (solo AGREGA SKUs alternos,
  compatibilidades, características e intercambios nuevos; no borra los existentes).
- El script crea backup automático antes de actualizar
- Railway hace deploy automático al detectar push (~2-3 min)
