# Patrones de Descripción por Marca - Catálogo RELUVSA

Este documento detalla el patrón exacto de cada marca y cómo extraer información de compatibilidad.

## Resumen de Tipos de Marcas

### Tipo A: Con Compatibilidades Vehiculares
Marcas que incluyen información de vehículos (marca, modelo, años, motor):
- ACDELCO, SYD, INJETECH, CAUPLAS, ESAEVER, OPTIMO, USPARTS, GARLO, etc.

### Tipo B: Sin Compatibilidades (Llantas)
Marcas de llantas que solo tienen medidas:
- TORNEL, NEREUS, GOODRIDE, HANKOOK, BKT, CARLISLE, CHAOYANG, etc.

### Tipo C: Sin Compatibilidades (Aceites/Químicos)
Marcas de aceites y productos químicos:
- RELUVSA, AKRON, CASTROL, BARDAHL, CHEVRON, MOBIL, etc.

### Tipo D: Productos Genéricos
Productos sin aplicación vehicular específica:
- ABRO (silicones), AYC/CDC (cables), ERKCO (herramientas), etc.

---

## MARCAS CON COMPATIBILIDADES (TIPO A)

### ACDELCO (5104 productos)

**Patrón General:**
```
SKU1/SKU2/SKU3 TIPO_PRODUCTO MODELO1 AÑO1/AÑO2, MODELO2 AÑO3/AÑO4
```

**Ejemplos:**
- `19192667/AS16MX LIMPIAPARABRISAS 16/400 MM AVEO 07/20 CAVALIER 18/21`
- `25121293/GG-66/GF578/G7315 FILTRO DE GASOLINA MALIBU 97/05,S10 03/05,GRAND AM 92/95`
- `PF47M/19210284/R1008/GP-46 FILTRO ACEITE CHEVY 94/12,CORSA03/08,AVEO 1.6L 08/18`

**Extracción:**
1. SKUs alternos: Todo antes del primer espacio después de códigos alfanuméricos con /
2. Tipo producto: Palabras después de SKUs (FILTRO, BUJIA, etc.)
3. Modelos: Buscar modelos conocidos (AVEO, CHEVY, MALIBU, etc.)
4. Años: Formato XX/XX (dos dígitos/dos dígitos)
5. Motor: Formato X.XL (1.6L, 2.4L, etc.)

**Particularidades:**
- Muchos productos tienen múltiples SKUs alternos separados por /
- Los años siempre son formato corto (07/20 = 2007-2020)
- A veces el año aparece sin modelo previo

---

### GONHER (1872 productos)

**Patrón General:**
```
G-XXX/SKU2/SKU3 FILTRO DE ACEITE [TIPO S.P. | MODELO AÑO/AÑO]
```

**Ejemplos:**
- `G-6/CH6/P80/A21475 FILTRO DE ACEITE F100 F250 F350 L6 V8 53/67`
- `G-31 FILTRO DE ACEITE GONHER S.P.` (Sin aplicación específica)
- `G-200/PF141/P18 FILTRO DE ACEITE PICKUP C10-C20-C30 73/61`

**Extracción:**
1. SKU principal: Siempre empieza con G-XXX
2. "S.P." = Sin aplicación específica (Servicio Pesado genérico)
3. Modelos: Pueden incluir series (F100, F250, C10-C20-C30)
4. Motor: Formato LX o VX (L6, V8)

**Particularidades:**
- "S.P." indica producto genérico sin compatibilidad específica
- Algunos tienen rango de años inverso (73/61 = 1961-1973)
- Los modelos pueden ser series completas

---

### SYD (2793 productos)

**Patrón General:**
```
CODIGO/CODIGO-ARE/K-XXXX TIPO_PRODUCTO MODELO AÑO/AÑO, MODELO2 AÑO/AÑO
```

**Ejemplos:**
- `1606002/K-7347 BRAZO AUXILIAR RAM 1500 00/02,RAM 3500 S.I. 00/03`
- `54501-01G90/54501-01G90-ARE HORQUILLA INFERIOR IZQUIERDA NISSAN PICKUP 94-13`
- `FO1106/TM518510/MGF1106-B MAZA DELANTERA FIESTA 98/11, COURIER 00-12`

**Extracción:**
1. Código con sufijo -ARE indica referencia alterna
2. K-XXXX son códigos de competencia
3. "S.I." = Suspensión Independiente
4. Años con guión (94-13) o slash (98/11)

**Particularidades:**
- Usa tanto / como - para separar años
- Incluye especificaciones técnicas (4X2, 4X4, DANA 28)
- Múltiples vehículos separados por coma

---

### INJETECH (1111 productos)

**Patrón General:**
```
CODIGO/CODIGO TIPO_PRODUCTO MODELO MOTOR AÑO/AÑO
```

**Ejemplos:**
- `12903/84991/D95166 VALVULA DE MARCHA MINIMA IAC PLATINA 01/05 RENAULT CLIO 02/04 1.6L`
- `11008/AC253 VALVULA BY PASS FORD IKON,KA,COURIER, FOCUS 00/AD`
- `04866/12596851 SENSOR DE POCISION DE CIGUEÑAL ESCALADE,BLAZER-S10,SUBURBAN 94-07`

**Extracción:**
1. "AD" = Año actual/Adelante
2. Puede incluir marca de vehículo explícita (FORD, NISSAN, etc.)
3. Tipo sensor específico (IAC, TPS, CKP, MAF)

**Particularidades:**
- Productos electrónicos con especificaciones técnicas
- Muchos son sensores con códigos OEM
- "AD" indica aplicación hasta año actual

---

### CAUPLAS (1469 productos)

**Patrón General:**
```
CODIGO/CODIGO/OEM MANGUERA CAUPLAS [TIPO] MODELO MOTOR AÑO/AÑO
```

**Ejemplos:**
- `5477 MANGUERA CAUPLAS SALIDA CALEFACCION CAPTIVA 2.4L 08/14`
- `4500/93428011/62695 MANGUERA CAUPLAS RADIADOR INFERIOR SIN AC CHEVY 1.4L 1.6L 99/13`
- `3922/61105/CH137502 MANGUERA CAUPLAS RADIADOR INFERIOR BRONCO 5.0L 90-92`

**Extracción:**
1. Tipo manguera: RADIADOR, CALEFACCION, REFRIGERACION
2. Posición: SUPERIOR, INFERIOR, ENTRADA, SALIDA
3. Especificación: CON AC, SIN AC
4. Motor siempre en formato X.XL

**Particularidades:**
- Productos muy específicos (posición, AC)
- Motor casi siempre presente
- Múltiples códigos OEM

---

### ESAEVER (336 productos)

**Patrón General:**
```
RXXXXXXX/ZXXXXXXX/OEM/CODIGO TIPO_PRODUCTO MODELO MOTOR AÑO/AÑO
```

**Ejemplos:**
- `R42609220/Z95048411/700061 TANQUE CON TAPON DEPOSITO ANTICONGELANTE SONIC 1.6L DOHC 12/17`
- `R19314860/19314860/B-6046 BOMBA AGUA AVEO 1.6L 06/17`
- `R94539597/96420303 TAPON TANQUE DEPOSITO ANTICONGELANTE AVEO,OPTRA 16V 2.0L 03/12`

**Extracción:**
1. Prefijo R = código ESAEVER
2. Prefijo Z = código alterno
3. DOHC/SOHC = tipo de motor
4. 16V = 16 válvulas

**Particularidades:**
- Especializado en sistema de enfriamiento
- Incluye especificaciones de motor (DOHC, 16V)
- Códigos bien estructurados

---

### OPTIMO (351 productos)

**Patrón General:**
```
CODIGOXXNNXXXX/OEM TIPO_PRODUCTO MARCA MODELO AÑO/AÑO
```

**Ejemplos:**
- `BMNN0150/OEM43200-50Y00 MAZA TRASERA 4 BIRLOS NISSAN TSURU-III 92/14`
- `TKNN0100/OEM30502-53J01 KIT DE CLUTCH NISSAN TSURU III 92/10`
- `SUNC9900/1003008/19334782 ROTULA INFERIOR AVEO 06/16,PONTIAC G3 06/11`

**Extracción:**
1. Prefijo indica tipo (BM=Maza, TK=Kit, SU=Suspensión, SH=Horquilla, SQ=Buje)
2. XX indica marca (NN=Nissan, NC=Chevrolet, NF=Ford, NK=Chrysler)
3. OEM código original del fabricante

**Particularidades:**
- Códigos muy estructurados y predecibles
- Fácil identificar tipo de producto y marca destino
- Incluye marca de vehículo explícita frecuentemente

---

### USPARTS (310 productos)

**Patrón General:**
```
XXX-XXX/RXXXXXXX/OEM TIPO MODELO MOTOR AÑO/AÑO
```

**Ejemplos:**
- `100-001/R9046588 TOMA AGUA CON TERMOSTATO AVEO NG 1.5L 18/23`
- `100-008/KGT-6819A TOMA CON TERMOSTATO RAM PROMASTER RAPID 1.4L 18/22`
- `120-016/13251435 CONECTOR MANGUERA RADIADOR INFERIOR CRUZE 1.4L 11/16`

**Extracción:**
1. Código XXX-XXX (grupo-secuencia)
2. 100 = Tomas de agua
3. 120 = Conectores
4. "NG" = Nueva Generación

**Particularidades:**
- Productos nuevos/recientes
- Códigos bien organizados por tipo
- Enfoque en GM moderno

---

### GARLO (545 productos)

**Patrón General:**
```
HY-XXX/JG-XXX CABLES DE BUJIA MODELO MOTOR AÑO/AÑO
```

**Ejemplos:**
- `HY-201/JG-201 CABLES DE BUJIA LUV 1.8L-2.2L 72/81,BLAZER 1.9L 82/85`
- `HY-111/8JG-111 CABLES DE BUJIA D100 318 360 75/92,DAKOTA 5.2L 5.9L 90/92`
- `HY-153/SHY CABLES DE BUJIA VW SEDAN 1600 E.ELEC`

**Extracción:**
1. HY-XXX = código Garlo
2. JG-XXX o 8JG-XXX = código alterno
3. Motor puede ser rango (1.8L-2.2L)
4. "318 360" son motores (en pulgadas cúbicas)

**Particularidades:**
- Especializado en cables de bujía
- Motors pueden estar en litros o pulgadas cúbicas
- Incluye especificaciones eléctricas (E.ELEC)

---

### DAYCO (1257 productos)

**Patrón General:**
```
APXX/69 AXX BANDA DAYCO
DAYCO-XXX TIPO_PRODUCTO
95XXX/CODIGO BANDA/TENSOR/KIT MODELO AÑO/AÑO
```

**Ejemplos:**
- `AP75/69 A75 BANDA DAYCO` (banda genérica por medida)
- `DAY-400 DIAFRAGMA FRENOS DAYCO` (producto genérico)
- `95285/PKB285 KIT DISTRIBUCION TSURU III 93/17,SENTRA 92/94`

**Extracción:**
1. AP = Banda tipo A, medida en pulgadas
2. 95XXX = Kit de distribución
3. Productos genéricos no tienen aplicación

**Particularidades:**
- Mezcla de productos genéricos y específicos
- Bandas genéricas por medida
- Kits tienen aplicación específica

---

### TOTALPARTS (1087 productos)

**Patrón General:**
```
CODIGO/OEM TIPO_PRODUCTO MODELO AÑO/AÑO
```

**Ejemplos:**
- `42119C/H6024 UNIDAD SELLADA (SILVIN) REDONDA 3 PATAS` (genérico)
- `14442/25319301 INYECTOR DE COMBUSTIBLE CHEVY CORSA 1.6L 04/08`
- `13704C/03622/3439088 BULBO SENSOR INDICADOR TEMPERATURA CHEVY`

**Extracción:**
1. Sufijo C = código CIOSA
2. H = códigos de silvin/focos
3. Impulsor TIM/TK con aplicación específica

**Particularidades:**
- Variedad de productos
- Muchos silivines genéricos
- Eléctricos con aplicación específica

---

## MARCAS SIN COMPATIBILIDADES (TIPO B - LLANTAS)

### TORNEL (311 productos)

**Patrón:**
```
MEDIDA [CAPAS] [MODELO] JK TORNEL LLANTA [TIPO]
```

**Ejemplos:**
- `31X10.5 R15 LT 6C LN DEPORTIVA JK TORNEL LLANTA DEPORTIVA`
- `1000 20 14C T2400 JK TORNEL LLANTA CONVENCIONAL PISO EXTRA`
- `205/60 R13 S/C DIRECCIONAL JK TORNEL LLANTA DIRECCIONAL`

**NO EXTRAER COMPATIBILIDADES** - Solo medidas de llanta

---

### NEREUS (109 productos)

**Patrón:**
```
MEDIDA LLANTA NEREUS MODELO
```

**Ejemplos:**
- `175/70 R13 82T LLANTA NEREUS NS601`
- `195/55 R16 RZ16 91W LLANTA NEREUS NS601 VERSA`

**NO EXTRAER COMPATIBILIDADES** - Solo medidas de llanta
(Nota: Algunos mencionan modelo de auto como referencia, no como compatibilidad)

---

## MARCAS SIN COMPATIBILIDADES (TIPO C - ACEITES)

### RELUVSA (220 productos)

**Patrón:**
```
TIPO RELUVSA [MEDIDA] [VISCOSIDAD] [TIPO_ACEITE]
```

**Ejemplos:**
- `AGUA BATERIA RELUVSA .500 LT`
- `RELUVSA .900ML SAE 40 SJ ACEITE MOTOR GASOLINA`
- `ANTICONGELANTE RELUVSA -6 GALON 3.785L`

**NO EXTRAER COMPATIBILIDADES** - Productos genéricos

---

### AKRON (46 productos)

**Patrón:**
```
AKRON[.MEDIDA] TIPO SAE [VISCOSIDAD] [CLASIFICACION]
```

**Ejemplos:**
- `AKRON.946L SUPER GEAR SAE 140 GL1`
- `AKRON 5L AKRON HD INTENSE SAE 40 SL`

**NO EXTRAER COMPATIBILIDADES** - Aceites genéricos

---

## Clasificación de las 236 Marcas

### CON COMPATIBILIDADES (Crear parser específico):
1. 4KAR - Poleas tensoras
2. ACDELCO - Filtros, bujías, etc.
3. AG - Amortiguadores
4. ANAUTOMY - Bombas, sensores
5. AUTOPAR - Balatas, coronas
6. AUTOTAL - Kits tiempo, bombas
7. AUTOTODO - Tomas, bombas
8. BOGE - Amortiguadores
9. BOKAR - Bombas gasolina
10. BORG WARNER - Cadenas tiempo
11. BOSCH - Eléctricos
12. BRUCK - Clutch, enfriamiento
13. BRUMER - Bombas agua
14. CAHSA - Cables
15. CARFAN - Motoventiladores
16. CARTEK - Homocinéticas
17. CAUPLAS - Mangueras
18. CHAMPION - Bujías
19. CHROMITE - Baleros
20. CLEVITE - Metales
21. CONTINENTAL - Mangueras, bandas
22. COOLTECH - Bulbos
23. CUB - Bulbos, cilindros
24. DAI - Bases, soportes
25. DAYCO - Bandas (parcial)
26. DC EMPAQUES - Empaques
27. DEPO - Faros
28. DIAMOND - Anillos, metales
29. DOLZ - Bombas agua
30. DORMAN - Cilindros freno
31. DYNAGEAR - Kits distribución
32. DYNAMIC - Interruptores
33. DYNAMIK - Balatas
34. ESAEVER - Enfriamiento
35. EXEDY - Clutch
36. FAG - Mazas, baleros
37. FLEETGUARD - Filtros SP
38. FLEX CONTROL - Cables
39. FLOTAMEX - Bombas
40. FRACO - Empaques
41. FRITEC - Balatas
42. GABRIEL - Amortiguadores SP
43. GARANTI - Kits, pistones
44. GARLO - Cables bujía
45. GATES - Bandas, mangueras
46. GC - Filtros
47. GMB - Bombas, mazas
48. GOLDEN FRICTION - Balatas
49. GONHER - Filtros
50. INJETECH - Sensores, válvulas
51. MORESA - Motor
52. NGK - Bujías
53. OPTIMO - Suspensión
54. PRESTONE - Anticongelantes (parcial)
55. RUVILLE - Kits
56. SKF - Baleros
57. SYD - Suspensión
58. TRW - Frenos
59. TOTALPARTS - Varios
60. USPARTS - Enfriamiento
61. WALKER - Sensores
62. WEGA - Suspensión

### SIN COMPATIBILIDADES (No crear parser):

**Llantas:**
- BFGOODRICH, BKT, CARLISLE, CHAOYANG, EPSILON, GOODRIDE, HANKOOK,
  HIFLY, MASTERTRACK, MILESTAR, NEREUS, TORNEL, TRIANGLE, WESTLAKE

**Aceites/Químicos:**
- ABRO, AKRON, BARDAHL, CASTROL, CHEVRON, FLEX QUIM, MOBIL,
  PENNZOIL, QUAKER STATE, RELUVSA, VALVOLINE

**Acumuladores:**
- CAMEL, CHECKER, EXTREMA, LTH

**Herramientas/Genéricos:**
- APS, AYC, CDC, ERKCO, FANDELI, FIAMM, GENERICO, etc.

---

## Notas de Implementación

1. **Años cortos a largos**:
   - 00-99 → Si ≤ 30, añadir 2000; Si > 30, añadir 1900
   - 07/20 → 2007/2020
   - 75/92 → 1975/1992

2. **Motor en litros**: Regex `\d+\.\d+L`

3. **Motor en cilindros**: Regex `V[468]|L[46]|\d+\s*CIL`

4. **Modelos compuestos**:
   - "TSURU III" = modelo completo
   - "RAM 1500" = marca + modelo
   - "F-150" = modelo con guión

5. **Marcas de vehículo implícitas**:
   - AVEO, CHEVY, CORSA, SPARK → CHEVROLET
   - TSURU, SENTRA, VERSA → NISSAN
   - FIESTA, FOCUS, RANGER → FORD
