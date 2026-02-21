# Configuración de Variables de Entorno para Docker

## Problema

Docker no estaba leyendo las nuevas variables de Google OAuth porque no estaban configuradas en `docker-compose.yml`.

## Solución

He actualizado el `docker-compose.yml` para incluir las nuevas variables. Ahora necesitas:

### 1. Crear archivo `.env` en la raíz del proyecto

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```bash
# OpenAI (Requerido)
OPENAI_API_KEY=tu_openai_api_key

# Google OAuth (Requerido para Google Login)
GOOGLE_CLIENT_ID=626294519743-9e15mr5vb1eq7gami7to6fj03j4lj7mf.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8501/google_login
APP_URL=http://localhost:8501

# Email SMTP (Requerido para OTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password-16-caracteres
SMTP_FROM=tu-email@gmail.com

# LangSmith (Opcional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=ecomarket-rag-system
```

### 2. Reconstruir y reiniciar el contenedor

```bash
# Detener contenedores actuales
docker-compose down

# Reconstruir con las nuevas variables
docker-compose build

# Iniciar con las nuevas variables
docker-compose up -d

# Ver logs para verificar
docker-compose logs -f
```

### 3. Verificar que las variables se están leyendo

```bash
# Ver variables de entorno del contenedor
docker-compose exec ecomarket-app env | grep GOOGLE
docker-compose exec ecomarket-app env | grep SMTP

# Debes ver:
# GOOGLE_CLIENT_ID=626294519743-9e15mr5vb1eq7gami7to6fj03j4lj7mf.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=GOCSPX-...
# SMTP_USER=tu-email@gmail.com
# etc.
```

## Variables Actualizadas en docker-compose.yml

El archivo `docker-compose.yml` ahora incluye:

```yaml
environment:
  # Google OAuth
  - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
  - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
  - GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI:-http://localhost:8501/google_login}
  - APP_URL=${APP_URL:-http://localhost:8501}
  
  # Email SMTP
  - SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}
  - SMTP_PORT=${SMTP_PORT:-587}
  - SMTP_USER=${SMTP_USER}
  - SMTP_PASSWORD=${SMTP_PASSWORD}
  - SMTP_FROM=${SMTP_FROM}
```

## Variables de tu archivo .env

Basado en lo que compartiste, tu `.env` debería tener:

```bash
GOOGLE_CLIENT_ID=626294519743-9e15mr5vb1eq7gami7to6fj03j4lj7mf.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-tu-secret-completo
GOOGLE_REDIRECT_URI=http://localhost:8501/google_login
APP_URL=http://localhost:8501

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App Password de 16 caracteres
SMTP_FROM=tu-email@gmail.com
```

## Para Producción

Si vas a desplegar en producción, actualiza:

```bash
GOOGLE_REDIRECT_URI=https://tu-dominio.com/google_login
APP_URL=https://tu-dominio.com
```

Y configura Google Cloud Console con tu dominio real.

## Verificar que Funciona

1. Inicia el contenedor con las nuevas variables:
```bash
docker-compose up -d
```

2. Accede a la aplicación:
```bash
http://localhost:8501/google_login
```

3. Verifica que puedas hacer login con Google y recibir el OTP por email.

## Troubleshooting

### Las variables no se cargan

Verifica que el archivo `.env` esté en la raíz del proyecto (mismo nivel que docker-compose.yml).

```bash
# Verificar ubicación
pwd
ls -la .env

# Debería estar en:
# /Users/enriquemanzano/personal/maestria-ai/Generative_AI/GENERATIVE_AI_ICESI/.env
```

### Docker sigue usando valores viejos

```bash
# Reconstruir completamente sin caché
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Ver logs del contenedor

```bash
docker-compose logs ecomarket-app | grep -i google
docker-compose logs ecomarket-app | grep -i smtp
```

## Archivos Relevantes

- `docker-compose.yml` - Configuración de Docker (actualizado)
- `.env` - Variables de entorno (debes crearlo)
- `DOCs/GOOGLE_AUTH_SETUP.md` - Documentación completa
- `DOCs/INSTRUCCIONES_GOOGLE_AUTH.md` - Instrucciones en español

