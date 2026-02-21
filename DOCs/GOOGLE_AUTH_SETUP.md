# Configuración de Autenticación con Google OAuth y OTP

## Descripción General

Este sistema implementa autenticación con Google OAuth seguida de verificación OTP (One-Time Password) para mayor seguridad. Cuando un usuario se autentica con Google, el sistema:

1. Autentica al usuario con Google
2. Obtiene la información del usuario verificado
3. Envía un código OTP de 6 dígitos al correo electrónico verificado
4. Solicita el código OTP para completar el acceso
5. El código expira en 10 minutos

## Arquitectura

### Archivos Creados/Modificados

1. **`src/tools/google_auth.py`** - Servicio de autenticación Google y OTP
2. **`src/controllers/auth.py`** - Funciones de controlador actualizadas
3. **`src/pages/google_login.py`** - Interfaz Streamlit para login con Google
4. **`src/models/db.py`** - Tablas de base de datos añadidas
5. **`requirements.txt`** - Dependencias añadidas
6. **`env.example`** - Variables de entorno actualizadas

### Tablas de Base de Datos

#### Tabla `google_auth`
```sql
CREATE TABLE google_auth (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    google_id TEXT UNIQUE NOT NULL,
    name TEXT,
    picture_url TEXT,
    email_verified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
)
```

#### Tabla `otp_codes`
```sql
CREATE TABLE otp_codes (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    otp_code TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## Configuración de Google Cloud Console

### Paso 1: Crear un Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Nombre del proyecto: `EcoMarket` (o el nombre que prefieras)

### Paso 2: Habilitar Google+ API

1. Ve a **APIs & Services** > **Library**
2. Busca "Google+ API" o "Identity Platform"
3. Haz clic en **Enable**

### Paso 3: Configurar Consent Screen

1. Ve a **APIs & Services** > **OAuth consent screen**
2. Selecciona **External** (para usuarios externos)
3. Completa la información:
   - **Application name**: EcoMarket
   - **User support email**: tu-email@ejemplo.com
   - **Developer contact email**: tu-email@ejemplo.com
4. Haz clic en **Save and Continue**
5. En **Scopes**, haz clic en **Add or Remove Scopes**
6. Selecciona:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
7. Haz clic en **Save and Continue**
8. En **Test users**, agrega las direcciones de correo de prueba
9. Haz clic en **Save and Continue**
10. Revisa y finaliza

### Paso 4: Crear Credenciales OAuth

1. Ve a **APIs & Services** > **Credentials**
2. Haz clic en **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Selecciona **Web application**
4. Completa:
   - **Name**: EcoMarket Web Client
   - **Authorized JavaScript origins**: 
     - `http://localhost:8501` (desarrollo)
     - `https://tu-dominio.com` (producción)
   - **Authorized redirect URIs**:
     - `http://localhost:8501/google_login` (desarrollo)
     - `https://tu-dominio.com/google_login` (producción)
5. Haz clic en **Create**
6. **Copiar el Client ID y Client Secret**

## Configuración de Email (Gmail SMTP)

### Paso 1: Activar 2-Factor Authentication

1. Ve a [Google Account Settings](https://myaccount.google.com/)
2. Ve a **Security**
3. Activa **2-Step Verification**

### Paso 2: Generar App Password

1. Ve a [App Passwords](https://myaccount.google.com/apppasswords)
2. Selecciona **App**: Mail
3. Selecciona **Device**: Other (Custom name)
4. Ingresa: "EcoMarket OTP System"
5. Haz clic en **Generate**
6. **Copia el password de 16 caracteres** (ej: `abcd efgh ijkl mnop`)

## Configuración del Proyecto

### Paso 1: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=tu-client-id-google.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8501/google_login
APP_URL=http://localhost:8501

# Email SMTP (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # El App Password de 16 caracteres
SMTP_FROM=tu-email@gmail.com
```

**Nota**: Para producción, actualiza las URLs con tu dominio real.

### Paso 3: Inicializar Base de Datos

Las tablas se crean automáticamente. Para inicializar manualmente:

```python
from models.db import init_database
init_database()
```

## Uso del Sistema

### Flujo de Autenticación

1. **Usuario hace clic en "Continuar con Google"**
   - Se redirige a Google OAuth
   - Usuario autoriza la aplicación

2. **Google redirige a `/google_login` con código de autorización**
   - El sistema intercambia el código por tokens
   - Obtiene información del usuario

3. **Sistema envía OTP al email**
   - Genera código de 6 dígitos
   - Expira en 10 minutos
   - Envía email con código

4. **Usuario ingresa OTP**
   - Sistema verifica el código
   - Si es válido, crea sesión

5. **Usuario accede al sistema**
   - Sesión válida por 24 horas
   - Email único por usuario

### Acceso a Login con Google

Desde cualquier página del sistema:

```python
st.switch_page("pages/google_login.py")
```

O agregar botón en admin_login.py:

```python
if st.button("🔵 Continuar con Google", use_container_width=True):
    st.switch_page("pages/google_login.py")
```

## Características de Seguridad

### Email Único

- Cada email de Google solo puede tener una cuenta
- Email verificado por Google
- Tabla `google_auth` con email UNIQUE

### OTP (One-Time Password)

- Código de 6 dígitos aleatorio
- Expira en 10 minutos
- Se marca como usado después de verificación
- Limpieza automática de códigos expirados

### Sesión Segura

- Token de sesión de 32 caracteres
- Expira en 24 horas
- Compatible con sistema de sesiones existente

### Protección CSRF

- Estado aleatorio almacenado en sesión
- Verificación en callback de OAuth

## Funciones Principales

### `google_auth_service`

```python
from tools.google_auth import google_auth_service

# Generar URL de autenticación
auth_url, state = google_auth_service.generate_auth_url(redirect_uri)

# Intercambiar código por token
token_data = google_auth_service.exchange_code_for_token(code, redirect_uri)

# Obtener información del usuario
user_info = google_auth_service.get_user_info_from_token(access_token)

# Enviar OTP
google_auth_service.send_otp_email(email, otp_code)

# Verificar OTP
is_valid = google_auth_service.verify_otp(email, otp_code)
```

### `auth.py` Functions

```python
from controllers.auth import (
    authenticate_google_user,
    verify_google_otp,
    create_google_session,
    send_google_otp
)

# Autenticar usuario y enviar OTP
result = authenticate_google_user(user_info)

# Verificar OTP
is_valid = verify_google_otp(email, otp_code)

# Crear sesión
session_token = create_google_session(user_info)
```

## Producción

### Configuraciones Adicionales

1. **Dominio y HTTPS**
   - Actualiza `GOOGLE_REDIRECT_URI` con tu dominio
   - Certificado SSL válido

2. **Secrets Management**
   - Usa servicios como AWS Secrets Manager o similar
   - No expongas credentials en código

3. **Rate Limiting**
   - Implementa límites para envío de OTP
   - Previene spam/abuso

4. **Monitoring**
   - Logs de intentos de autenticación
   - Alertas por fallos repetidos

### Ejemplo para Producción

```bash
# .env en producción
GOOGLE_CLIENT_ID=tu-client-id
GOOGLE_CLIENT_SECRET=tu-secret
GOOGLE_REDIRECT_URI=https://www.ecomarket.com/google_login
APP_URL=https://www.ecomarket.com

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@ecomarket.com
SMTP_PASSWORD=xxx
SMTP_FROM=noreply@ecomarket.com
```

## Troubleshooting

### Error: "redirect_uri_mismatch"

- Verifica que la URI en `.env` coincida exactamente con Google Console
- Incluye protocolo (`http://` o `https://`)
- Sin slash final

### Error: "invalid_client"

- Verifica `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`
- Asegúrate de que no tengan espacios extra

### OTP no llega por email

- Verifica credenciales SMTP
- Usa App Password de 16 caracteres
- Revisa spam/trash
- Verifica logs en consola

### Error de conexión SMTP

- Verifica firewall
- Puerto 587 abierto
- StartTLS configurado

## Testing

### Modo de Prueba

Para testing sin enviar emails reales:

```python
# En google_auth.py, descomentar:
return True  # Skip actual email send

# O configurar mock:
from unittest.mock import patch

with patch('src.tools.google_auth.google_auth_service.send_otp_email'):
    # Test code here
```

## Recursos

- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)
- [Google SMTP Settings](https://support.google.com/mail/answer/7126229)
- [App Passwords](https://support.google.com/accounts/answer/185833)
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)

