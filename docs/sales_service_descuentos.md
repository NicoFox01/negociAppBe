# Sales Service - Descuentos y Funciones Pendientes

## Descuentos: Arquitectura Recomendada

### Estructura de campos a agregar

| Campo | Tabla | Tipo | Descripción |
|-------|-------|------|-------------|
| `general_discount_value` | `ClientOrder` | `Numeric(10,2)` | Descuento general (monto o %) |
| `general_discount_type` | `ClientOrder` | `Enum(DiscountType)` | Tipo: PERCENTAGE o FIXED_AMOUNT |
| `discount_value` (por item) | `ClientOrderItem` | `Numeric(10,2)` | Descuento por item específico |

### Flujo de cálculo (create y update)

```
1. Por cada item:
   - subtotal_item = (precio_unitario * cantidad)
   - descuento_item = subtotal_item * (discount_item / 100)  [si es %]
   - subtotal_item -= descuento_item

2. Calcular promociones activas del canal:
   - descuento_promocion = subtotal_total * (promo_value / 100)  [si es %]

3. Aplicar descuento general de la orden:
   - descuento_general = subtotal_total * (general_discount / 100)  [si es %]

4. TOTAL = sum(items) - promo - general
```

### Prioridad recomendada

1. ✅ Promo del canal (ya existe)
2. ✅ Descuento general en `ClientOrder` (agregar campo opcional)
3. ⏳ Descuento por item (futuro, si lo necesitan)

---

## Funciones faltantes en sales_service.py

### Actualmente implementadas (parcialmente)

| Función | Estado |
|---------|--------|
| `create_sales_channel` | ✅ OK |
| `get_sales_channels` | ✅ OK |
| `get_sales_channel_by_id` | ✅ OK |
| `update_sales_channel` | ✅ OK |
| `delete_sales_channel` | ✅ OK |
| `set_product_price` | ✅ OK |
| `get_product_price_by_id` | ⚠️ Necesita fix: retornar None en vez de 404 |
| `get_all_channel_prices` | ✅ OK |
| `delete_product_price` | ✅ OK |
| `create_promotion` | ✅ OK |
| `get_promotions_by_channel` | ✅ OK |
| `get_active_promotion` | ✅ OK |
| `update_promotion` | ✅ OK |
| `delete_promotion` | ✅ OK |
| `create_order` | ⚠️ Necesita fix: import de Product |
| `get_orders` | ⚠️ Necesita fix: joinedload |
| `get_order_by_id` | ⚠️ Necesita fix: joinedload |
| `update_order` | ⚠️ Corregir (ver abajo) |
| `cancel_order` | ⚠️ Corregir (ver abajo) |

### Funciones nuevas agregadas ✅

| Función | Descripción |
|---------|-------------|
| `get_orders_by_date_range` | Órdenes filtradas por rango de fechas, con filtros opcionales de canal y estado |
| `apply_manual_discount` | Aplicar descuento manual (% o monto fijo) a una orden, con motivo |

### Funciones que podrían faltar (sugerencias)

| Función | Descripción |
|---------|-------------|
| `get_orders_by_customer` | Buscar órdenes por nombre/teléfono de cliente |
| `get_order_stats` | Métricas: total ventas, por estado, por canal |

---

## Fixes pendientes en funciones ClientOrder

### 1. `get_product_price_by_id` (línea ~106)
- **Cambiar**: retornar `None` en vez de lanzar 404 cuando no existe precio
- **Por qué**: `create_order` necesita caer al precio base si no hay precio de canal

### 2. `create_order` (línea ~212)
- **Agregar import**: `from app.models.products import Product`

### 3. `get_orders` (línea ~306)
- **Fix**: `joinedload(ClientOrder.channel_id)` → `joinedload(ClientOrder.channel)`
- **Fix**: coma entre joinedloads
- **Fix**: `created_at.desc()` → `ClientOrder.created_at.desc()`

### 4. `get_order_by_id` (línea ~327)
- **Fix**: `joinedload(ClientOrder.channel_id)` → `joinedload(ClientOrder.channel)`

### 5. `update_order` y `cancel_order`
- Ya corregidas en el código (ver sección anterior)
