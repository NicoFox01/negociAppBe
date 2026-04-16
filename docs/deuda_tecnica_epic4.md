# Deuda Técnica - Epic 4: Gestión de Inventario y Producción

## Fecha: 12/03/2026
## Estado: Pendiente de desarrollo

---

## 1. Historial de Transacciones de Inventario

### Problema identificado
Actualmente el frontend puede consultar el historial de transacciones por producto, pero el backend no registra automáticamente las transacciones cuando se realizan:

- **Ventas**: Al registrar una venta, debe registrarse una transacción de tipo `SALE` con cantidad negativa
- **Transformaciones**: Al crear una transformación, debe registrarse:
  - `TRANSFORMATION_INPUT` (cantidad negativa) para los insumos
  - `TRANSFORMATION_OUTPUT` (cantidad positiva) para los productos resultantes
- **Recepción de Órdenes**: Al recibir una orden de compra, debe registrarse una transacción de tipo `PURCHASE`
- **Merma**: Necesitamos agregar la posibilidad de registrar mermas manually

### Tareas a realizar
1. [ ] Modificar el servicio de ventas (`sales_service.py`) para registrar transacciones de inventario automáticamente
2. [ ] Modificar el servicio de producción (`production_service.py`) para registrar transacciones de entrada y salida
3. [ ] Modificar el servicio de órdenes (`order_services.py`) para registrar transacciones al recibir mercadería
4. [ ] Agregar endpoint para registrar mermas manualmente (`POST /inventory/waste`)
5. [ ] Agregar campo `transaction_type` en el modelo de transacciones para identificar el origen

### Schema recomendado para InventoryTransaction
```python
class TransactionType(str, Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    TRANSFORMATION_INPUT = "TRANSFORMATION_INPUT"
    TRANSFORMATION_OUTPUT = "TRANSFORMATION_OUTPUT"
    ADJUSTMENT = "ADJUSTMENT"
    WASTE = "WASTE"
    RETURN = "RETURN"
```

---

## 2. Sistema de Alertas de Stock

### Funcionalidad requerida
- Notificaciones cuando el stock de un producto cae por debajo de un umbral mínimo
- Configuración de umbrales mínimos por producto
- Panel de alertas en el dashboard

### Tareas a realizar
1. [ ] Agregar campo `min_stock_threshold` al modelo de Producto
2. [ ] Crear servicio de verificación de stock mínimo
3. [ ] Integrar con el sistema de notificaciones existente
4. [ ] Crear endpoint para configurar umbrales (`PATCH /products/{id}/threshold`)

---

## 3. Reportes de Inventario

### Funcionalidad requerida
- Reporte de productos con stock bajo
- Reporte de movimientos por período
- Reporte de valoración de inventario (stock × costo)

### Tareas a realizar
1. [ ] Crear endpoint de reportes (`GET /inventory/reports/low-stock`)
2. [ ] Crear endpoint de reportes de movimientos (`GET /inventory/reports/movements`)
3. [ ] Crear endpoint de valoración de inventario (`GET /inventory/reports/valuation`)

---

## 4. Validaciones de Negocio

### Pendientes
- [ ] Validar que al crear una transformación haya stock suficiente de los insumos
- [ ] Validar que no se puede vender más de lo que hay en stock
- [ ] Validar que al recibir una orden, las cantidades no excedan lo ordenado

---

## 5. Mejoras UI/UX Pendientes

- [ ] Mejorar visualización del modal de transformación (actualmente básico)
- [ ] Agregar validación en tiempo real del stock disponible al crear órdenes
- [ ] Agregar filtros por rango de fechas en el historial de transacciones
- [ ] Exportar historial de transacciones a PDF/Excel

---

## Notas

Este documento sirve como guía para el desarrollo de la Epic 4 completa. Las funcionalidades básicas de visualización ya están implementadas en el frontend, pero falta la lógica de negocio para el registro automático de transacciones.
