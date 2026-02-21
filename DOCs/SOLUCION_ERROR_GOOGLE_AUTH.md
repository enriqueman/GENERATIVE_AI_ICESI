# Solución: Error "invalid_grant" en Google OAuth

## Problema Identificado

Estabas viendo estos errores:
```
Error exchanging code: {
  "error": "invalid_grant",
  "error_description": "Bad Request"
}
```

Y el formulario OTP no se mostraba después de la redirección.

## Causas

1. **Código de autorización usado múltiples veces**: Cada vez que Streamlit hacía re-render, intentaba usar el mismo código de autorización otra vez, causando "invalid_grant".

2. **Query params persistentes**: Los parámetros `code=...` permanecían en la URL causando que el código se procesara varias veces.

3. **Redirect URI no coincidente**: Si el redirect_uri configurado no coincide exactamente con el de Google Console.

## Soluciones Aplicadas

### 1. Flag de procesamiento
He añadido un flag `google_callback_processed` en session_state para evitar procesar el callback múltiples veces:

```python
if 'google_callback_processed' not in st.session_state:
    # Procesar callback una sola vez
    st.session_state.google_callback_processed = True
```

### 2. Limpieza de query params
Después de procesar el callback, limpiamos los query params:

```python
st.query_params.clear()
st.rerun()
```

### 3. Mejor manejo de errores
Ahora se muestra la excepción completa para debugging:

```python
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.exception(e)
```

## Verificar Configuración

### 1. Redirect URI debe coincidir exactamente

En tu `.env`:
```bash
GOOGLE_REDIRECT_URI=http://localhost:8501/google_login
```

En Google Cloud Console (APIs & Services > Credentials):
- **Authorized redirect URIs**: `http://localhost:8501/google_login`

**IMPORTANTE**: Deben coincidir EXACTAMENTE, carácter por carácter.

### 2. Para producción (Docker)

Si usas Docker y quieres que funcione correctamente:

```bash
# En docker-compose.yml ya está configurado
GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI:-http://localhost:8501/google_login}
```

Pero para Docker, deberías usar:
```bash
GOOGLE_REDIRECT_URI=http://0.0.0.0:8501/google_login
```

O mejor aún, si usas nginx:
```bash
GOOGLE_REDIRECT_URI=http://tu-dominio.com/google_login
```

Y en Google Console añadir ambos:
- `http://0.0.0.0:8501/google_login`
- `http://localhost:8501/google_login`

## Reconstruir y Reiniciar

```bash
# Detener contenedores
docker-compose down

# Reconstruir
docker-compose build --no-cache

# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f ecomarket-app
```

## Verificar que Funciona

1. **Limpia cache del navegador**: Ctrl+Shift+R (Windows) o Cmd+Shift+R (Mac)

2. **Ve a**: `http://localhost:8501/google_login`

3. **Flujo esperado**:
   - Haz clic en "Continuar con Google"
   - Autoriza en Google
   - Se redirige de vuelta
   - Debes ver: "✅ Código OTP enviado a tu correo electrónico"
   - Aparece el formulario para ingresar OTP
   - Ingresa el código de 6 dígitos
   - Sesión creada → Acceso al Admin Panel

## Debugging

Si todavía ves el error, verifica:

### 1. Variables de entorno
```bash
docker-compose exec ecomarket-app env | grep GOOGLE
```

Deberías ver:
```
GOOGLE_CLIENT_ID=626294519743-...
GOOGLE_CLIENT_SECRET=GOCSPX-...
GOOGLE_REDIRECT_URI=http://localhost:8501/google_login
```

### 2. Ver logs detallados
```bash
docker-compose logs -f ecomarket-app | grep -i google
```

### 3. Verificar en Google Console

1. Ve a Google Cloud Console
2. APIs & Services > Credentials
3. Selecciona tu OAuth 2.0 Client ID
4. Verifica que "Authorized redirect URIs" tenga exactamente:
   - `http://localhost:8501/google_login`
   - `http://0.0.0.0:8501/google_login`

### 4. Prueba con un nuevo código de autorización

Si el error persiste, intenta con un navegador incógnito o limpia las cookies del sitio.

## Estados del Flujo

El flujo ahora maneja correctamente estos estados en `session_state`:

1. `google_callback_processed`: Indica que el callback ya fue procesado
2. `otp_sent`: Indica que el OTP fue enviado
3. `email`: Email del usuario autenticado
4. `google_user`: Información del usuario de Google

## Archivos Modificados

- ✅ `src/views/google_login.py` - Vista principal (actualizada)
- ✅ `src/pages/google_login.py` - Página standalone (actualizada)

Ambos archivos ahora tienen el mismo código mejorado.

## Resumen

El problema era que el código OAuth se estaba usando múltiples veces. Ahora:
- Se procesa solo una vez
- Se limpian los query params
- Se muestra el formulario OTP correctamente
- Mejor manejo de errores para debugging

¡Prueba nuevamente y debería funcionar!

