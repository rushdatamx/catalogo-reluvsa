// Nombres cortos y amigables para departamentos (estilo MercadoLibre/Amazon).
// Se usan en la barra de categorías y en la vitrina de más vendidos.
export const NOMBRE_CATEGORIA = {
  'LUBRICACIÓN': 'Aceites',
  'AFINACION': 'Afinación',
  'SISTEMA ELECTRICO & SENSORES': 'Eléctrico y baterías',
  'ACCESORIO': 'Accesorios',
  'ENFRIAMIENTO Y BANDAS': 'Enfriamiento y bandas',
  'LLANTAS': 'Llantas',
  'PARTES DE MOTOR': 'Partes de motor',
  'QUIMICOS,ADITIVOS,AGUA PARA BATERIA,EMBE': 'Químicos y aditivos',
  'CLUTCH': 'Clutch',
  'SUSPENSION': 'Suspensión',
  'FRENOS': 'Frenos',
  'TRANSMISION MANUAL & EJE TRASERO': 'Transmisión',
  'OTROS': 'Otros',
  'CASCO USADO CHICO Y GRANDE': 'Cascos',
  'COMBUSTIBLE': 'Combustible',
  'CALEFACCION': 'Calefacción',
  'SERVICIOS TALLER': 'Servicios de taller',
};

// Devuelve un nombre legible para un departamento (con fallback capitalizado).
export const nombreCategoria = (dep) => {
  if (!dep) return '';
  if (NOMBRE_CATEGORIA[dep]) return NOMBRE_CATEGORIA[dep];
  return dep.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
};
