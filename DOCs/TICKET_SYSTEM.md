# Sistema de Gestión de Tickets - EcoMarket

## 📋 Descripción General

El sistema de tickets permite gestionar casos de clientes de manera organizada, creando registros para diferentes tipos de solicitudes y asignando tickets únicos para su seguimiento.

## 🎯 Tipos de Tickets Disponibles

### 1. **Compra** (`compra`)
- Genera tickets para procesar compras de clientes
- Registra información de productos, total y datos del cliente

### 2. **Devolución** (`devolucion`)
- Crea tickets para solicitudes de devolución de productos
- Incluye información de producto, factura, motivo y fecha

### 3. **Guía de Seguimiento** (`guia_de_seguimiento`)
- Genera guías para rastrear envíos
- Asocia número de seguimiento con empresa de transporte

### 4. **Factura** (`factura`)
- Solicita y gestiona información de facturas
- Permite búsqueda por número de factura o email del cliente

### 5. **Queja/Reclamo/Felicitación** (`queja_reclamo_felicitacion`)
- Registra feedback de clientes (quejas, reclamos o felicitaciones)
- Prioridad automática según tipo

## 🛠️ Funciones Disponibles

### `crear_ticket_devolucion()`
Crea un ticket para solicitud de devolución.

**Parámetros:**
- `cliente_email`: Email del cliente (requerido)
- `cliente_nombre`: Nombre del cliente (requerido)
- `producto_id`: ID o nombre del producto (requerido)
- `factura_numero`: Número de factura (requerido)
- `motivo_devolucion`: Motivo de devolución (requerido)
- `cantidad`: Cantidad de productos (opcional, default: 1)
- `cliente_telefono`: Teléfono del cliente (opcional)
- `fecha_devolucion`: Fecha de devolución (opcional)
- `notas`: Notas adicionales (opcional)

**Ejemplo de uso en consulta:**
```
"Quiero devolver un producto, mi email es cliente@ejemplo.com, 
factura FAC-12345, producto Botella de Acero"
```

### `crear_ticket_compra()`
Crea un ticket para procesar una compra.

**Parámetros:**
- `cliente_email`: Email del cliente
- `cliente_nombre`: Nombre del cliente
- `productos`: Lista de productos (string separado por comas)
- `total`: Total de la compra
- `cliente_telefono`: Teléfono (opcional)
- `notas`: Notas adicionales (opcional)

**Ejemplo de uso:**
```python
result = crear_ticket_compra(
    cliente_email="cliente@ejemplo.com",
    cliente_nombre="Juan Pérez",
    productos="Botella de Acero, Bolsa de Tela",
    total=59.99
)
```

### `generar_guia_de_seguimiento()`
Genera una guía de seguimiento para un envío.

**Parámetros:**
- `ticket_number`: Número de ticket existente (opcional)
- `cliente_email`: Email del cliente
- `numero_pedido`: Número de pedido
- `empresa_envio`: Empresa de envío
- `numero_seguimiento`: Número de guía (opcional, se genera automáticamente)

**Ejemplo de uso en consulta:**
```
"Necesito una guía de seguimiento para mi pedido #12345"
```

### `consulta_seguimiento()`
Consulta el estado de un pedido.

**Parámetros:**
- `numero_seguimiento`: Número de guía de seguimiento
- `ticket_number`: Número de ticket (opcional)
- `cliente_email`: Email del cliente (opcional)

**Ejemplo de uso en consulta:**
```
"¿Cuál es el estado de mi pedido con número GS-TKT-12345?"
```

### `obtener_factura()`
Solicita información de una factura.

**Parámetros:**
- `factura_numero`: Número de factura
- `cliente_email`: Email del cliente
- `ticket_number`: Número de ticket (opcional)

**Ejemplo de uso en consulta:**
```
"Necesito mi factura número FAC-12345"
```

### `crear_ticket_queja_reclamo()`
Crea un ticket de queja, reclamo o felicitación.

**Parámetros:**
- `cliente_email`: Email del cliente
- `cliente_nombre`: Nombre del cliente
- `tipo_queja`: Tipo ('queja', 'reclamo', 'felicitacion')
- `descripcion`: Descripción detallada
- `cliente_telefono`: Teléfono (opcional)
- `producto_id`: ID del producto relacionado (opcional)
- `factura_numero`: Número de factura (opcional)
- `notas`: Notas adicionales (opcional)

**Ejemplo de uso en consulta:**
```
"Tengo un reclamo sobre mi producto defectuoso"
```

### `consultar_ticket()`
Consulta información de tickets existentes por número, email o estado.

**Parámetros:**
- `ticket_number`: Número de ticket específico (opcional)
- `cliente_email`: Email del cliente (opcional)
- `estado`: Filtrar por estado (opcional: abierto, pendiente, procesando, cerrado)
- `tipo`: Filtrar por tipo de ticket (opcional: compra, devolucion, factura, etc.)

**Ejemplo de uso:**
```python
# Consultar ticket específico
result = consultar_ticket(ticket_number="TKT-1234567890-ABCD1234")

# Consultar tickets de un cliente
result = consultar_ticket(cliente_email="cliente@ejemplo.com")

# Consultar tickets por estado
result = consultar_ticket(estado="pendiente")

# Consultar tickets por tipo
result = consultar_ticket(tipo="devolucion")
```

**Ejemplo de uso en consulta:**
```
"Consultar mi ticket TKT-1234567890-ABCD1234"
"Mis tickets con email cliente@ejemplo.com"
"Ver mis tickets pendientes"
```

**Retorna:**
```python
{
    "exito": True,
    "total": 1,
    "mensaje": "Ticket TKT-1234567890-ABCD1234 encontrado",
    "tickets": [
        {
            "numero": "TKT-1234567890-ABCD1234",
            "tipo": "devolucion",
            "estado": "pendiente",
            "prioridad": "alta",
            "titulo": "Devolución de producto...",
            "descripcion": "Cliente solicita...",
            "cliente": {
                "nombre": "Juan Pérez",
                "email": "cliente@ejemplo.com",
                "telefono": "+57 300 123 4567"
            },
            "producto_id": "Botella de Acero",
            "factura_numero": "FAC-12345",
            "cantidad": 1,
            "fecha_creacion": "2024-01-15 10:30:00",
            "fecha_actualizacion": "2024-01-15 14:20:00",
            "fecha_resolucion": "No resuelto"
        }
    ]
}
```

### `generar_etiqueta_devolucion()`
Genera una etiqueta de devolución para un ticket existente.

**Parámetros:**
- `ticket_number`: Número de ticket de devolución
- `direccion_retiro`: Dirección para retiro (opcional)
- `notas`: Notas adicionales (opcional)

**Ejemplo de uso:**
```python
result = generar_etiqueta_devolucion(
    ticket_number="TKT-1234567890-ABCD1234",
    direccion_retiro="Calle 123, Ciudad"
)
```

## 🔍 Detección Automática

El sistema RAG detecta automáticamente cuando una consulta requiere crear un ticket basándose en palabras clave:

### Palabras Clave para Devoluciones:
- "devolver", "devolución", "retornar"
- "quiero devolver", "necesito devolver"
- "etiqueta de devolución"

### Palabras Clave para Seguimiento:
- "seguimiento", "rastrear", "donde está"
- "guía de seguimiento", "estado de mi pedido"

### Palabras Clave para Facturas:
- "factura", "recibo", "obtener factura"

### Palabras Clave para Compras:
- "comprar", "pedir", "ordenar", "quiero"

### Palabras Clave para Quejas:
- "reclamo", "queja", "felicitación"

### Palabras Clave para Consulta de Tickets:
- "consultar mi ticket", "estado de mi ticket", "mi ticket"
- "mis tickets", "historial de tickets", "ver mi ticket"

## 📊 Estructura de la Base de Datos

### Tabla `tickets`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PRIMARY KEY | ID único |
| `ticket_number` | TEXT UNIQUE | Número de ticket (ej: TKT-1234567890-ABCD1234) |
| `tipo` | TEXT | Tipo de ticket (compra, devolucion, etc.) |
| `estado` | TEXT | Estado (abierto, pendiente, procesado, cerrado) |
| `prioridad` | TEXT | Prioridad (baja, normal, alta, urgente) |
| `titulo` | TEXT | Título del ticket |
| `descripcion` | TEXT | Descripción detallada |
| `cliente_email` | TEXT | Email del cliente |
| `cliente_nombre` | TEXT | Nombre del cliente |
| `cliente_telefono` | TEXT | Teléfono del cliente |
| `producto_id` | TEXT | ID del producto relacionado |
| `factura_numero` | TEXT | Número de factura |
| `numero_seguimiento` | TEXT | Número de guía de seguimiento |
| `guia_seguimiento` | TEXT | Información de guía |
| `cantidad` | INTEGER | Cantidad de productos |
| `total` | DECIMAL | Total de compra |
| `fecha_devolucion` | TEXT | Fecha de devolución |
| `motivo_devolucion` | TEXT | Motivo de devolución |
| `notas` | TEXT | Notas adicionales |
| `created_at` | DATETIME | Fecha de creación |
| `updated_at` | DATETIME | Fecha de actualización |
| `resolved_at` | DATETIME | Fecha de resolución |

## 🔧 Operaciones CRUD

### Crear Ticket
```python
from models.db import create_ticket

result = create_ticket(
    tipo="devolucion",
    titulo="Devolución de producto",
    descripcion="Cliente solicita devolución...",
    cliente_email="cliente@ejemplo.com",
    cliente_nombre="Juan Pérez"
)
print(result)  # {'id': 1, 'ticket_number': 'TKT-1234567890-ABCD1234'}
```

### Obtener Ticket
```python
from models.db import get_ticket

ticket = get_ticket("TKT-1234567890-ABCD1234")
```

### Listar Tickets
```python
from models.db import list_tickets

# Todos los tickets
tickets = list_tickets()

# Filtrar por tipo
tickets_devolucion = list_tickets(tipo="devolucion")

# Filtrar por estado
tickets_abiertos = list_tickets(estado="abierto")

# Filtrar por cliente
tickets_cliente = list_tickets(cliente_email="cliente@ejemplo.com")
```

### Actualizar Ticket
```python
from models.db import update_ticket

update_ticket(
    ticket_number="TKT-1234567890-ABCD1234",
    estado="cerrado",
    notas="Ticket resuelto exitosamente"
)
```

### Eliminar Ticket
```python
from models.db import delete_ticket

delete_ticket("TKT-1234567890-ABCD1234")
```

## 🚀 Uso en Consultas del Usuario

El sistema está completamente integrado con el RAG agent. Los usuarios pueden hacer consultas naturales y el sistema detectará automáticamente si necesita crear un ticket.

### Ejemplos de Consultas:

**Devolución:**
- "Quiero devolver un producto"
- "Necesito devolver una Botella de Acero, factura FAC-123, motivo: defectuoso"

**Seguimiento:**
- "¿Dónde está mi pedido?"
- "Consulta de seguimiento número GS-12345"

**Factura:**
- "Necesito mi factura número FAC-12345"
- "¿Pueden enviarme mi recibo?"

**Queja/Reclamo:**
- "Tengo un reclamo"
- "El producto llegó defectuoso"

**Consulta de Tickets:**
- "Consultar mi ticket TKT-1234567890-ABCD1234"
- "Mis tickets con email cliente@ejemplo.com"
- "Ver estado de mi ticket"
- "¿Cuál es el estado de mi ticket?"

## 📝 Notas Importantes

1. **Información del Cliente**: El sistema intenta extraer automáticamente email, nombre y teléfono de las consultas usando regex.

2. **Números de Ticket**: Se generan automáticamente con formato `TKT-{timestamp}-{uuid}` para garantizar unicidad.

3. **Estados**: Los estados posibles son:
   - `abierto`: Ticket recién creado
   - `pendiente`: Esperando atención
   - `procesando`: En proceso
   - `en_transito`: Para envíos
   - `procesado`: Completado pero no cerrado
   - `cerrado`: Ticket resuelto

4. **Prioridad**: Se asigna automáticamente:
   - `urgente`: Para problemas críticos
   - `alta`: Para reclamos y devoluciones
   - `normal`: Para consultas generales
   - `baja`: Para felicitaciones

5. **Integración**: El sistema NO modifica la funcionalidad existente de búsqueda de productos y documentos. Estas siguen funcionando normalmente.

## 🎯 Flujo de Trabajo

```
Usuario hace consulta
       ↓
Sistema detecta si es ticket o consulta normal
       ↓
Si es ticket: ¿Es consulta de ticket existente?
       ├─ Sí → Buscar ticket en BD → Mostrar información
       └─ No → Extraer información → Crear ticket → Responder con número
Si es consulta normal: Usar RAG estándar
       ↓
Usuario recibe respuesta con información del ticket o número de ticket
       ↓
Sistema puede buscar y actualizar tickets
```

## 🔍 Consulta de Tickets

La funcionalidad de consulta permite a los clientes:
1. **Ver el estado de sus tickets** proporcionando el número de ticket
2. **Ver todos sus tickets** proporcionando su email
3. **Filtrar tickets** por estado o tipo
4. **Acceder a información detallada** como fecha de creación, prioridad, descripción completa

### Ejemplo de Uso:

**Cliente:** "Consultar mi ticket TKT-1234567890-ABCD1234"

**Sistema:** 
```
📋 **Consulta de Tickets**

Se encontraron 1 ticket(s):

**Ticket #1**
- **Número**: TKT-1234567890-ABCD1234
- **Tipo**: devolucion
- **Estado**: pendiente
- **Prioridad**: alta
- **Título**: Devolución de producto: Botella de Acero
- **Fecha**: 2024-01-15 10:30:00
- **Producto**: Botella de Acero
- **Factura**: FAC-12345
```

