# 🐳 EcoMarket RAG System - Docker Deployment

## 🚀 Quick Start

### Prerequisites
- Docker installed on your system
- OpenAI API Key

### 1. Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your OpenAI API key
nano .env
```

### 2. Build and Run
```bash
# Build and start the application
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application
- **Main Application**: http://localhost:8501
- **Admin Panel**: http://localhost:8501/admin_login

## 🔧 Manual Docker Commands (Alternative)

### Build the Image
```bash
docker build -t ecomarket-rag-system .
```

### Run the Container
```bash
docker run -d \
  --name ecomarket-app \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/persist:/app/static/persist \
  ecomarket-rag-system
```

### Stop and Remove
```bash
docker stop ecomarket-app
docker rm ecomarket-app
```

## 📁 Volume Mounts

The application uses the following volume mounts for data persistence:

- `./data` → `/app/data` - Application data
- `./static/persist` → `/app/static/persist` - Vector database
- `./static/temp_files` → `/app/static/temp_files` - Temporary files

## 🌐 Production Deployment

### With Nginx (Recommended)
```bash
# Start with Nginx reverse proxy
docker-compose --profile production up -d
```

This will start:
- EcoMarket app on port 8501 (internal)
- Nginx on ports 80 and 443 (external)

### Environment Variables for Production
```bash
# .env file for production
OPENAI_API_KEY=your_production_api_key
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
DEBUG=False
SECRET_KEY=your_secure_secret_key
```

## 🔍 Troubleshooting

### Check Container Logs
```bash
docker logs ecomarket-app
```

### Access Container Shell
```bash
docker exec -it ecomarket-app /bin/bash
```

### Health Check
```bash
curl http://localhost:8501/_stcore/health
```

### Common Issues

1. **OpenAI API Key Error**
   - Ensure `OPENAI_API_KEY` is set in your environment
   - Check the key is valid and has sufficient credits

2. **Port Already in Use**
   - Change the port mapping: `-p 8502:8501`
   - Or stop the conflicting service

3. **Permission Issues**
   - Ensure Docker has permission to access the project directory
   - Check file permissions: `chmod -R 755 .`

## 📊 Monitoring

### Container Status
```bash
docker ps
```

### Resource Usage
```bash
docker stats ecomarket-app
```

### Database Backup
```bash
# Copy database from container
docker cp ecomarket-app:/app/doc_sage.sqlite ./backup/
```

## 🔄 Updates

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Update Dependencies
```bash
# Edit requirements.txt
# Then rebuild
docker-compose build --no-cache
docker-compose up -d
```

## 🛡️ Security Notes

- Change default admin credentials after first login
- Use strong secret keys in production
- Consider using Docker secrets for sensitive data
- Regularly update base images and dependencies
- Use HTTPS in production (configure SSL certificates)

## 🆘 Support

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Verify environment variables in `.env` file
3. Ensure all required ports are available
4. Check Docker and Docker Compose versions
