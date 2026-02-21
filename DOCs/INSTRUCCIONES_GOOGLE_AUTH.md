# Instrucciones: Autenticación con Google OAuth + OTP

## 📋 Resumen

He implementado un sistema completo de autenticación con Google que incluye:

✅ Autenticación con Google OAuth  
✅ Envío de código OTP al email verificado  
✅ Verificación de código OTP obligatoria  
✅ Email único por usuario  
✅ Sesión segura de 24 horas  

## 🔧 Archivos Creados/Modificados

### Nuevos Archivos
- `src/tools/google_auth.py` - Servicio de autenticación Google y OTP
- `src/pages/google_login.py` - Página de login con Google
- `DOCs/GOOGLE_AUTH_SETUP.md` - Documentación técnica completa
- `DOCs/INSTRUCCIONES_GOOGLE_AUTH.md` - Este archivo

### Archivos Modificados
- `src/models/db.py` - Añadidas tablas `google_auth` y `otp_codes`
- `src/controllers/auth.py` - Añadidas funciones para Google auth
- `requirements.txt` - Añadidas dependencias OAuth
- `env.example` - Añadidas variables de entorno

## 🚀 Configuración Paso a Paso

### 1️⃣ Configurar Google Cloud Console

#### Paso 1: Crear Proyecto
1. Ve a https://console.cloud.google.com/
2. Crea un nuevo proyecto llamado "EcoMarket"

#### Paso 2: Habilitar OAuth
1. Ve a **APIs & Services** > **Library**
2. Busca "Google+ API" o "Identity Platform"
3. Habilítalo

#### Paso 3: Pantalla de Consentimiento
1. Ve a **APIs & Services** > **OAuth consent screen**
2. Selecciona **External** (para usuarios externos)
3. Completa:
   - **Nombre de la aplicación**: EcoMarket
   - **Email de soporte**: tu-email@ejemplo.com
   - **Email de desarrollador**: tu-email@ejemplo.com
4. En **Scopes**, añade:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
5. En **Test users**, añade tus emails de prueba
6. Guarda

#### Paso 4: Credenciales OAuth
1. Ve a **APIs & Services** > **Credentials**
2. Crea **OAuth client ID** > **Web application**
3. Configura:
   - **Nombre**: EcoMarket Web Client
   - **JavaScript origins**: `http://localhost:8501`
   - **Redirect URIs**: `http://localhost:8501/google_login`
4. Crea y **copia el Client ID y Client Secret**

### 2️⃣ Configurar Gmail para OTP

#### Paso 1: Activar 2-Factor Authentication
1. Ve a https://myaccount.google.com/
2. **Security** > **2-Step Verification** > Activar

#### Paso 2: Generar App Password
1. Ve a https://myaccount.google.com/apppasswords
2. Selecciona:
   - **App**: Mail
   - **Device**: Other (Custom name)
3. Nombre: "EcoMarket OTP System"
4. **Genera y copia el password** (16 caracteres como: `abcd efgh ijkl mnop`)

### 3️⃣ Configurar Proyecto

#### Instalar Dependencias
```bash
pip install -r requirements.txt
```

#### Configurar .env

Crea un archivo `.env` en la raíz del proyecto con:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8501/google_login
APP_URL=http://localhost:8501

# Email (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # El App Password de 16 caracteres
SMTP_FROM=tu-email@gmail.com
```

**Importante**: 
- Reemplaza los valores con tus credenciales reales
- Para producción, cambia `localhost:8501` por tu dominio

### 4️⃣ Inicializar Base de Datos

Las tablas se crean automáticamente al iniciar la app. Si necesitas inicializar manualmente:

```python
from models.db import init_database
init_database()
```

## 💡 Uso

### Acceder al Login con Google

Desde tu aplicación Streamlit, añade un botón de login con Google. Por ejemplo, en `src/pages/admin_login.py`:

```python
st.markdown("---")

if st.button("🔵 Continuar con Google", use_container_width=True):
    st.switch_page("pages/google_login.py")
```

O accede directamente a:
```
http://localhost:8501/google_login
```

### Flujo del Usuario

1. **Usuario hace clic en "Continuar con Google"**
2. Se redirige a Google para autenticarse
3. Usuario autoriza la aplicación
4. **Sistema envía código OTP de 6 dígitos al email**
5. Usuario ingresa el código en la pantalla
6. Si el código es válido → **Sesión creada**
7. Usuario es redirigido al panel de administración

## 🔒 Seguridad

- **Email único**: Cada email solo puede tener una cuenta
- **Código OTP**: 6 dígitos, expira en 10 minutos
- **Sesión**: 24 horas de duración
- **Verificación**: Email verificado por Google antes de enviar OTP

## 🧪 Testing

### Probar el Sistema

1. Inicia la aplicación:
```bash
streamlit run src/app.py
```

2. Ve a: `http://localhost:8501/google_login`
3. Haz clic en "Continuar con Google"
4. Autoriza con una cuenta de Google
5. Revisa tu email para el código OTP
6. Ingresa el código para completar el login

### Verificar en Base de Datos

```bash
# Conectar a SQLite
sqlite3 doc_sage.sqlite

# Ver usuarios de Google
SELECT * FROM google_auth;

# Ver códigos OTP (recientes)
SELECT * FROM otp_codes ORDER BY created_at DESC LIMIT 5;

# Ver sesiones activas
SELECT * FROM sessions;
```

## 🐛 Problemas Comunes

### Error: "redirect_uri_mismatch"
**Solución**: Verifica que la URI en `.env` coincida exactamente con Google Console

### No llega el email OTP
**Soluciones**:
- Verifica que usaste el App Password correcto (16 caracteres)
- Revisa spam/trash
- Verifica logs en consola
- Asegúrate de que el SMTP esté configurado correctamente

### "invalid_client" error
**Solución**: Verifica que `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` no tengan espacios

### Error SMTP
**Solución**: 
- Verifica que el puerto 587 esté abierto
- Usa App Password, no tu contraseña normal
- Activa 2FA en Gmail

## 📊 Tablas de Base de Datos

### google_auth
Almacena usuarios autenticados con Google:
- `email`: Email del usuario (único)
- `google_id`: ID de Google del usuario
- `name`: Nombre del usuario
- `picture_url`: URL de foto de perfil
- `email_verified`: Si el email está verificado

### otp_codes
Almacena códigos OTP:
- `email`: Email que recibió el OTP
- `otp_code`: Código de 6 dígitos
- `expires_at`: Fecha de expiración
- `used`: Si ya fue usado

## 📝 Ejemplo de Uso en Código

### Desde una página Streamlit

```python
import streamlit as st

# Botón para ir a Google login
if st.button("Login con Google"):
    st.switch_page("pages/google_login.py")

# Verificar si usuario está autenticado
if 'session_token' in st.session_state:
    st.write(f"Bienvenido: {st.session_state.user_info['name']}")
```

### Enviar OTP manualmente

```python
from controllers.auth import send_google_otp

# Enviar OTP a un email
if send_google_otp("usuario@gmail.com"):
    st.success("OTP enviado!")
```

## 🚢 Producción

### Cambios Necesarios

1. **Actualizar .env**:
```bash
GOOGLE_REDIRECT_URI=https://www.tu-dominio.com/google_login
APP_URL=https://www.tu-dominio.com
```

2. **Google Console**:
- Añade tu dominio a Authorized JavaScript origins
- Añade tu dominio a Authorized redirect URIs

3. **SMTP**:
- Considera usar SendGrid o Amazon SES para mejor deliverability
- Configura SPF y DKIM records

## 📚 Documentación

Para más detalles técnicos, ver:
- `DOCs/GOOGLE_AUTH_SETUP.md` - Documentación técnica completa
- `src/tools/google_auth.py` - Código del servicio

## ✅ Checklist de Implementación

- [x] Archivos creados
- [x] Tablas de base de datos añadidas
- [x] Servicio de OAuth implementado
- [x] Envío de email OTP
- [x] Verificación de OTP
- [x] Interfaz de login creada
- [x] Documentación completada
- [ ] Configurar Google Cloud Console
- [ ] Configurar Gmail App Password
- [ ] Crear archivo .env
- [ ] Probar login con Google
- [ ] Verificar envío de OTP

## 🎉 ¡Listo!

El sistema de autenticación con Google + OTP está completamente implementado. Solo necesitas:

1. Configurar Google Cloud Console
2. Configurar Gmail para envío de emails
3. Crear archivo .env con tus credenciales
4. Probar el flujo completo

¡Buena suerte! 🚀

