# HelyMar Repostería

Monolito Django. En localhost la base de datos es SQLite. PostgreSQL se usa en producción.

## Requisitos

- Python 3.12 o superior.

## Arranque en localhost

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements\dev.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`createsuperuser` pide un rol. Los valores válidos son `administrador`, `ventas` y `produccion`.

La aplicación queda en <http://127.0.0.1:8000/>. El panel está en <http://127.0.0.1:8000/dashboard/> y el acceso del personal en <http://127.0.0.1:8000/cuenta/entrar/>.

No hace falta PostgreSQL ni Docker para desarrollar. El archivo local es `db.sqlite3` y no se versiona.

## WhatsApp

`HELYMAR_WHATSAPP_NUMBER` va en `.env`, solo dígitos, sin `+` ni espacios. El valor actual es `5638773661`. Si queda vacío en localhost, los botones usan ese mismo número.

## Producción

Instala `requirements/prod.txt` y arranca con `DJANGO_SETTINGS_MODULE=config.settings.production`.

Hacen falta `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y `DATABASE_URL` de PostgreSQL. Los archivos estáticos los sirve WhiteNoise después de `python manage.py collectstatic`. Las imágenes usan el almacenamiento indicado por `FILE_STORAGE_BACKEND`; en esta fase el valor local es el sistema de archivos.

## Pruebas

```powershell
python -m pytest
python manage.py check
```

## Roles

El acceso al panel exige sesión y pertenencia al grupo del rol. Un administrador recibe `is_staff` y todos los permisos. Ventas administra contactos y oportunidades y puede consultar el catálogo. Producción solo consulta el catálogo. No existe registro público.

## Catálogo y clientes

El personal con permiso administra productos en `/dashboard/catalogo/` y contactos en `/dashboard/clientes/`. El catálogo público solo muestra productos activos. No hay productos de ejemplo.

La importación de contactos acepta un CSV con las columnas `nombre`, `apellidos`, `correo`, `telefono`, `whatsapp`, `empresa`, `origen`, `estado`, `etiquetas` y `observaciones`. La vista previa señala duplicados y no fusiona registros.

## Operación

Cotizaciones en `/dashboard/cotizaciones/`, pedidos y su calendario en `/dashboard/pedidos/`, cocina en `/dashboard/produccion/`, inventario en `/dashboard/inventario/` y resultado en `/dashboard/resultado/`.

Ventas arma cotizaciones y pedidos, cobra anticipos y ve la cocina sin editarla. Producción mueve las fichas y ve existencias, sin precios ni ganancia. El administrador ve el resultado: cobros menos compras y gastos. Las inversiones quedan aparte.

No hay productos, clientes, insumos ni gastos de ejemplo. Mercado Pago y las notificaciones automáticas siguen pendientes.

## Despliegue

En el servidor, `/home/ubuntu/helmar-reposteria` es un clon de `main`. `deploy/update.sh` hace `git pull --ff-only` y `docker compose up -d --build`. El archivo `.env` no se versiona y el volumen de PostgreSQL se llama `helmar-reposteria`.

## Pendiente

- Mercado Pago y notificaciones.
- El aviso de privacidad está pendiente de revisión legal.
