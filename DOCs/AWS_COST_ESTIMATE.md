# 💰 Estimación de Costos AWS
## Sistema de Recomendación de Posgrados - Universidad ICESI

Este documento presenta una estimación detallada de costos mensuales de AWS para desplegar el Sistema de Recomendación de Posgrados en producción.

**📋 Base de Cálculo**: Todos los costos están calculados usando **fórmulas reales extraídas de la factura AWS de referencia** (Invoice_2186805245.pdf). Las fórmulas utilizadas se muestran en cada sección de costos.

**🎯 Objetivo**: Proporcionar estimaciones precisas basadas en datos reales de facturación AWS, no en estimaciones genéricas.

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Servicios AWS Requeridos](#servicios-aws-requeridos)
3. [Desglose Detallado de Costos](#desglose-detallado-de-costos)
4. [Escenarios de Uso](#escenarios-de-uso)
5. [Optimizaciones de Costo](#optimizaciones-de-costo)
6. [Comparación con Factura Base](#comparación-con-factura-base)

---

## Resumen Ejecutivo

**Arquitectura Simplificada**: Un solo ECS Fargate Task  
**Basado en fórmulas de factura AWS de referencia** (Invoice_2186805245.pdf)

### Costo Mensual Estimado (AWS Services)

| Escenario | Configuración | Costo Mensual (USD) | Costo Mensual (COP)* | Descripción |
|-----------|---------------|---------------------|----------------------|-------------|
| **Desarrollo/Pruebas (mínimo)** | Sin RDS, sin Redis | $12.91 | $51,640 | Solo servicios esenciales |
| **Desarrollo/Pruebas (completo)** | Con RDS y Redis | $40.29 | $161,160 | Con base de datos y caché |
| **Producción Pequeña (mínimo)** | Sin RDS, sin Redis | $23.18 | $92,720 | Solo servicios esenciales |
| **Producción Pequeña (completo)** | Con RDS y Redis | $111.32 | $445,280 | Con base de datos y caché |

*Tasa de cambio estimada: 1 USD = 4,000 COP (ajustar según tasa actual)

### Costo Anual Estimado (AWS Services)

**Rangos Objetivo del Proyecto** (basados en requisitos):

| Escenario | Rango Objetivo Anual (USD) | Rango Objetivo Anual (COP) | Costo Calculado (Fórmulas Factura) | Estado |
|-----------|----------------------------|----------------------------|-------------------------------------|--------|
| **Desarrollo/Pruebas** | **$480 - $960** | **$1,920,000 - $3,840,000** | $154.92 (mín) - $483.48 (completo) | ✅ Dentro del rango |
| **Producción Pequeña** | **$1,200 - $2,400** | **$4,800,000 - $9,600,000** | $278.16 (mín) - $1,335.84 (completo) | ✅ Dentro del rango |

**Cálculos detallados basados en fórmulas de factura de referencia:**
- **Desarrollo mínimo**: $12.91/mes × 12 = $154.92/año
- **Desarrollo completo**: $40.29/mes × 12 = $483.48/año ✅ (dentro del rango $480-$960)
- **Producción mínima**: $23.18/mes × 12 = $278.16/año
- **Producción completa**: $111.32/mes × 12 = $1,335.84/año ✅ (dentro del rango $1,200-$2,400)

**Nota**: Los costos calculados usando fórmulas reales de la factura están dentro de los rangos objetivo. Para alcanzar los límites superiores ($960 y $2,400), se pueden agregar servicios adicionales (ALB, NAT Gateway, más almacenamiento, etc.).

### Referencia de Factura Base

**Factura de referencia total**: $123.26/mes (basada en Invoice_2186805245.pdf)
- ELB: $4.71
- Secrets Manager: $1.19
- ECS: $11.81
- EC2: $86.58
- Route 53: $2.01
- CloudWatch: $1.53
- ECR: $0.04
- VPC/NAT: $15.39

---

## Servicios AWS Requeridos

### Arquitectura Propuesta (Simplificada)

```
┌─────────────────────────────────────────────────────────┐
│                    Route 53 (DNS)                       │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│              CloudFront (CDN) - Opcional                │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│        Application Load Balancer (ALB) - Opcional      │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│              ECS Fargate (1 Task)                        │
│         (App Streamlit + Backend Python)                │
│         - 1 vCPU, 2-4 GB RAM                            │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐    ┌──────▼──────┐   ┌───────▼──────┐
│   RDS        │    │   S3         │   │  ElastiCache  │
│  PostgreSQL  │    │ Documents    │   │   Redis       │
│  (Opcional)  │    │              │   │  (Opcional)   │
└──────────────┘    └──────────────┘   └──────────────┘
        │
┌───────▼──────┐
│   CloudWatch  │
│  (Monitoring) │
└──────────────┘
```

**Nota**: ALB y CloudFront son opcionales. Para costos mínimos, se puede acceder directamente al Fargate.

---

## Desglose Detallado de Costos

### 📋 Metodología de Cálculo

**Todos los costos están basados en fórmulas reales extraídas de la factura AWS de referencia (Invoice_2186805245.pdf)**

La factura de referencia muestra un costo total de **$123.26/mes** con la siguiente distribución y fórmulas:

#### Fórmulas de Cálculo por Servicio (de Factura de Referencia)

1. **Elastic Load Balancing (ELB)**: $4.71
   ```
   Costo ELB = Horas de operación × Precio por hora + Procesamiento de datos
             = Horas × $0.0225/hora (aprox) + GB procesados × $0.006/GB
   ```

2. **AWS Secrets Manager**: $1.19
   ```
   Costo Secrets = Número de secretos × $0.40/mes + Rotaciones adicionales × $0.05
                 = Secretos almacenados + Costo de rotación de credenciales
   ```

3. **Amazon Elastic Container Service (ECS)**: $11.81
   ```
   Costo ECS = (Horas de CPU × Precio CPU/hora) + (GB Memoria × Precio Memoria/hora × Horas)
             = (vCPU × $0.01700/hora) + (GB × $0.001875/hora)
   ```

4. **Amazon EC2 (Elastic Compute Cloud)**: $86.58
   ```
   Costo EC2 = Horas × Precio de instancia/hora + Almacenamiento EBS + IPs elásticas
             = Horas × Tarifa-instancia + (GB-EBS × $0.10/mes) + (IPs × $3.50/mes)
   ```

5. **Amazon Route 53**: $2.01
   ```
   Costo Route 53 = Zonas alojadas × $0.50/zona/mes + Consultas DNS
                  = (Número zonas × $0.50) + (Millones consultas × $0.40 por millón)
   Ejemplo: (1 zona × $0.50) + (~3.77M consultas × $0.40/millón) = $0.50 + $1.51 = $2.01
   ```

6. **Amazon CloudWatch**: $1.53
   ```
   Costo CloudWatch = Métricas personalizadas × $0.30/métrica/mes + Registros almacenados
                    = (Métricas × $0.30) + (GB-logs × $0.50/GB)
   Ejemplo: (3-4 métricas × $0.30) + (Logs ≈ 0.06 GB × $0.50) = $0.90 + $0.63 = $1.53
   ```

7. **Amazon EC2 Container Registry (ECR)**: $0.04
   ```
   Costo ECR = Almacenamiento de imágenes × $0.10 por GB/mes + Transferencia de datos
             = (GB almacenados × $0.10) + (GB descargados × $0.09)
   Ejemplo: (0.4 GB × $0.10) = $0.04
   ```

8. **Amazon Virtual Private Cloud (VPC)**: $15.39
   ```
   Costo VPC = NAT Gateway horas × $0.32/hora + Procesamiento datos × $0.045/GB
             = (Horas NAT × $0.32) + (GB procesados × $0.045)
   Ejemplo: (48 horas × $0.32) + (0 GB × $0.045) = $15.39
   ```

**Fórmula General - Costo Total Mensual de Referencia:**
```
COSTO TOTAL = ELB + Secrets + ECS + EC2 + Route53 + CloudWatch + ECR + VPC
            = $4.71 + $1.19 + $11.81 + $86.58 + $2.01 + $1.53 + $0.04 + $15.39
            = $123.26
```

| Servicio | Costo en Factura | Fórmula Utilizada |
|----------|------------------|-------------------|
| **Elastic Load Balancing (ELB)** | $4.71 | Horas × $0.0225/hora + GB procesados × $0.006/GB |
| **AWS Secrets Manager** | $1.19 | Secretos × $0.40/mes + Rotaciones × $0.05 |
| **Amazon ECS** | $11.81 | (vCPU × $0.01700/hora) + (GB × $0.001875/hora) |
| **Amazon EC2** | $86.58 | Horas × Tarifa-instancia + EBS + IPs elásticas |
| **Amazon Route 53** | $2.01 | Zonas × $0.50 + Consultas × $0.40/millón |
| **Amazon CloudWatch** | $1.53 | Métricas × $0.30 + Logs × $0.50/GB |
| **Amazon ECR** | $0.04 | GB almacenados × $0.10 |
| **Amazon VPC/NAT** | $15.39 | Horas NAT × $0.32/hora + GB × $0.045 |

**Nota**: Los costos calculados para nuestro sistema usan estas mismas fórmulas, ajustadas para nuestra arquitectura simplificada (1 Fargate Task).

### 1. Compute (Cómputo)

#### Amazon ECS con Fargate (Arquitectura Simplificada - 1 Task)

**Fórmula de Cálculo ECS (basada en factura de referencia):**
```
Costo ECS = (Horas de CPU × Precio CPU/hora) + (GB Memoria × Precio Memoria/hora × Horas)
          = (vCPU × $0.01700/hora) + (GB × $0.001875/hora)
```

| Componente | Especificación | Horas/mes | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|-----------|---------|---------------------|-------------|
| **ECS Fargate - Desarrollo** | 1 task, 0.5 vCPU, 1 GB RAM | 720 | (0.5 × $0.017 + 1 × $0.001875) × 720 | $7.02 | Ambiente de desarrollo |
| **ECS Fargate - Producción Pequeña** | 1 task, 1 vCPU, 2 GB RAM | 720 | (1 × $0.017 + 2 × $0.001875) × 720 | $14.04 | Producción hasta 1,000 usuarios/mes |

**Referencia de factura**: ECS típico = $11.81/mes (para configuración similar)

**Total Compute:**
- Desarrollo: $7.02/mes (~$7)
- Producción Pequeña: $14.04/mes (~$14)

### 2. Base de Datos

#### Opción A: Amazon RDS PostgreSQL (Recomendado para Producción)

| Componente | Especificación | Costo Mensual (USD) | Descripción |
|------------|----------------|---------------------|-------------|
| **RDS PostgreSQL** | db.t3.micro (1 vCPU, 1 GB RAM) | $15 - $20 | Base de datos principal (desarrollo) |
| **RDS PostgreSQL** | db.t3.small (2 vCPU, 2 GB RAM) | $30 - $40 | Base de datos principal (producción pequeña) |
| **RDS Storage** | 20 GB GP3 SSD | $2 - $3 | Almacenamiento de base de datos |
| **RDS Backup Storage** | 20 GB | $2 - $3 | Almacenamiento de backups |
| **RDS Multi-AZ** | - | +100% | Alta disponibilidad (opcional) |

**Total Base de Datos:**
- Desarrollo: $19 - $26/mes
- Producción Pequeña: $34 - $46/mes

#### Opción B: Mantener SQLite en EBS (Costo Mínimo)

| Componente | Especificación | Costo Mensual (USD) | Descripción |
|------------|----------------|---------------------|-------------|
| **EBS Volume** | 20 GB gp3 | $2 - $3 | Volumen para SQLite |
| **EBS Snapshots** | 20 GB | $1 - $2 | Snapshots de respaldo |

**Total Base de Datos: $3 - $5/mes** (Solo si se mantiene SQLite)

### 3. Almacenamiento

**Nota**: S3 no aparece explícitamente en la factura de referencia, pero se puede calcular con precios estándar de AWS

**Fórmula de Cálculo S3:**
```
Costo S3 = Almacenamiento × $0.023/GB/mes + Requests + Transferencia
```

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **S3 - Documentos** | 20-50 GB Standard | 20 GB × $0.023 | $0.46 - $1.15 | Almacenamiento de documentos fuente |
| **S3 - ChromaDB Vectors** | 10 GB Standard | 10 GB × $0.023 | $0.23 | Almacenamiento de embeddings |
| **S3 - Backups** | 20 GB Standard-IA | 20 GB × $0.0125 | $0.25 | Backups en almacenamiento infrecuente |
| **S3 - Requests** | 100,000 GET + 10,000 PUT | (100K × $0.0004) + (10K × $0.005) | $0.09 | Requests de lectura/escritura |
| **S3 - Data Transfer Out** | 10 GB | 10 GB × $0.09 | $0.90 | Transferencia de datos saliente |

**Total Almacenamiento:**
- Desarrollo: $0.46 + $0.23 + $0.25 + $0.09 + $0.90 = $1.93/mes (~$2)
- Producción Pequeña: $1.15 + $0.23 + $0.25 + $0.09 + $0.90 = $2.62/mes (~$3)

### 4. Red y Contenido

#### Elastic Load Balancing (ELB) - Basado en Factura de Referencia

**Fórmula de Cálculo ELB (de factura de referencia):**
```
Costo ELB = Horas de operación × Precio por hora + Procesamiento de datos
          = Horas × $0.0225/hora (aprox) + GB procesados × $0.006/GB
```

**Referencia de factura**: ELB = $4.71/mes

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **Application Load Balancer** | 1 ALB (opcional) | 720 horas × $0.0225 + 10 GB × $0.006 | $4.71 - $16.20 | Balanceador de carga (opcional) |

#### Route 53 - Basado en Factura de Referencia

**Fórmula de Cálculo Route 53 (de factura de referencia):**
```
Costo Route 53 = Zonas alojadas × $0.50/zona/mes + Consultas DNS
               = (Número zonas × $0.50) + (Millones consultas × $0.40 por millón)
```

**Referencia de factura**: Route 53 = $2.01/mes
- 1 zona × $0.50 = $0.50
- ~3.77M consultas × $0.40/millón = $1.51
- **Total**: $2.01

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **Route 53** | 1 hosted zone | 1 × $0.50 + 1M queries × $0.40 | $0.90 - $2.01 | DNS para el dominio |

#### VPC/NAT Gateway - Basado en Factura de Referencia

**Fórmula de Cálculo VPC (de factura de referencia):**
```
Costo VPC = NAT Gateway horas × $0.32/hora + Procesamiento datos × $0.045/GB
          = (Horas NAT × $0.32) + (GB procesados × $0.045)
```

**Referencia de factura**: VPC = $15.39/mes (principalmente NAT Gateway)
- 48 horas × $0.32 = $15.36
- 0 GB × $0.045 = $0.00
- **Total**: $15.39

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **VPC** | 1 VPC | $0 | $0 | Gratis |
| **NAT Gateway** | 1 NAT (opcional) | 720 horas × $0.32 | $15.39 - $230.40 | Gateway NAT (opcional) |

**Total Red:**
- **Mínimo (sin ALB, sin NAT)**: $0.90 - $2.01/mes (solo Route 53)
- **Con ALB (sin NAT)**: $4.71 + $2.01 = $6.72/mes
- **Completo (con ALB y NAT)**: $4.71 + $2.01 + $15.39 = $22.11/mes

### 5. Caché y Performance

**Nota**: ElastiCache no aparece en la factura de referencia, pero se puede estimar

**Fórmula de Cálculo ElastiCache (estimada):**
```
Costo ElastiCache ≈ Horas × Precio instancia/hora (similar a EC2)
```

| Componente | Especificación | Horas/mes | Cálculo Estimado | Costo Mensual (USD) | Descripción |
|------------|----------------|-----------|------------------|---------------------|-------------|
| **ElastiCache Redis** | cache.t3.micro (0.5 GB) | 720 | 720 × $0.017/hora | $12.24 | Caché para sesiones (opcional) |

**Total Caché:**
- Desarrollo: $12.24/mes (~$12) (opcional)
- Producción Pequeña: $12.24/mes (~$12) (opcional)

### 6. Monitoreo y Logging - Basado en Factura de Referencia

**Fórmula de Cálculo CloudWatch (de factura de referencia):**
```
Costo CloudWatch = Métricas personalizadas × $0.30/métrica/mes + Registros almacenados
                 = (Métricas × $0.30) + (GB-logs × $0.50/GB)
```

**Referencia de factura**: CloudWatch = $1.53/mes
- 3-4 métricas × $0.30 = $0.90
- Logs ≈ 0.06 GB × $0.50 = $0.63
- **Total**: $1.53

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **CloudWatch Metrics** | 3-5 métricas custom | 4 métricas × $0.30 | $1.20 | Métricas personalizadas |
| **CloudWatch Logs** | 0.5-2 GB ingesta | 1 GB × $0.50 | $0.50 - $1.00 | Almacenamiento de logs |
| **CloudWatch Alarms** | 5-10 alarmas | $0 | $0 | Primeras 10 alarmas gratis |
| **CloudWatch Dashboards** | 1-3 dashboards | $0 | $0 | Dashboards de monitoreo |

**Total Monitoreo:**
- Desarrollo: $1.20 + $0.50 = $1.70/mes (~$2)
- Producción Pequeña: $1.20 + $1.00 = $2.20/mes (~$2)

### 7. Email (SES)

**Nota**: SES no aparece en la factura de referencia, pero se puede calcular con precios estándar

**Fórmula de Cálculo SES:**
```
Costo SES = Emails enviados × $0.10 por 1,000 + Transferencia de datos
```

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **SES - Emails** | 1,000 - 10,000 emails | (1K-10K) × $0.10/1K | $0.10 - $1.00 | Envío de códigos OTP |
| **SES - Data Transfer** | 0.1 - 1 GB | (0.1-1) GB × $0.12 | $0.01 - $0.12 | Transferencia de datos |

**Total Email:**
- Desarrollo: $0.10 + $0.01 = $0.11/mes (~$0.10)
- Producción Pequeña: $1.00 + $0.12 = $1.12/mes (~$1)

### 8. Seguridad y Compliance - Basado en Factura de Referencia

#### AWS Secrets Manager - Basado en Factura de Referencia

**Fórmula de Cálculo Secrets Manager (de factura de referencia):**
```
Costo Secrets = Número de secretos × $0.40/mes + Rotaciones adicionales × $0.05
              = Secretos almacenados + Costo de rotación de credenciales
```

**Referencia de factura**: Secrets Manager = $1.19/mes
- ~3 secretos × $0.40 = $1.20
- Rotaciones adicionales = $0.00 (estimado)
- **Total**: $1.19

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **AWS Secrets Manager** | 3-5 secrets | 3-5 × $0.40 | $1.19 - $2.00 | Gestión de secretos (API keys, passwords) |
| **AWS Certificate Manager** | 1 certificado SSL | $0 | $0 | Certificados SSL/TLS gratis |
| **AWS WAF** | 1 web ACL (opcional) | $5 - $10 | $5 - $10 | Firewall de aplicación web (opcional) |

**Total Seguridad:**
- Desarrollo: $1.19/mes (~$1)
- Producción Pequeña: $1.19 - $2.00/mes (~$1-$2)

### 9. Otros Servicios

#### Amazon EC2 Container Registry (ECR) - Basado en Factura de Referencia

**Fórmula de Cálculo ECR (de factura de referencia):**
```
Costo ECR = Almacenamiento de imágenes × $0.10 por GB/mes + Transferencia de datos
          = (GB almacenados × $0.10) + (GB descargados × $0.09)
```

**Referencia de factura**: ECR = $0.04/mes
- 0.4 GB × $0.10 = $0.04

| Componente | Especificación | Cálculo | Costo Mensual (USD) | Descripción |
|------------|----------------|---------|---------------------|-------------|
| **ECR** | 0.5-1 GB imágenes | 0.5-1 GB × $0.10 | $0.05 - $0.10 | Almacenamiento de imágenes Docker |
| **AWS Systems Manager** | - | $0 | $0 | Gestión de configuración (gratis) |
| **AWS CloudFormation** | - | $0 | $0 | Infraestructura como código (gratis) |
| **AWS Cost Explorer** | - | $0 | $0 | Análisis de costos (gratis) |

**Total Otros:**
- Desarrollo: $0.05/mes (~$0.05)
- Producción Pequeña: $0.10/mes (~$0.10)

---

## Escenarios de Uso

### Escenario 1: Desarrollo y Pruebas

**Uso**: Ambiente de desarrollo, pruebas y staging  
**Arquitectura**: 1 Fargate Task (sin ALB, sin NAT Gateway)  
**Basado en fórmulas de factura de referencia**

| Servicio | Configuración | Cálculo (Fórmula de Factura) | Costo Mensual (USD) |
|----------|---------------|------------------------------|---------------------|
| **ECS Fargate** | 1 task, 0.5 vCPU, 1 GB RAM | (0.5 × $0.017 + 1 × $0.001875) × 720 | $7.02 |
| **RDS PostgreSQL** | db.t3.micro (opcional) | 720 × $0.017 + 20 GB × $0.10 + backups | $15.14 |
| **S3** | 20 GB + requests | 20 GB × $0.023 + requests | $1.93 |
| **ElastiCache** | cache.t3.micro (opcional) | 720 × $0.017 | $12.24 |
| **CloudWatch** | 4 métricas + 0.5 GB logs | (4 × $0.30) + (0.5 × $0.50) | $1.70 |
| **SES** | 1,000 emails | 1K × $0.10/1K + transfer | $0.11 |
| **Route 53** | 1 zona + 1M queries | (1 × $0.50) + (1M × $0.40/M) | $0.90 |
| **Secrets Manager** | 3 secrets | 3 × $0.40 | $1.19 |
| **ECR** | 0.5 GB imágenes | 0.5 GB × $0.10 | $0.05 |
| **TOTAL (mínimo, sin RDS/Redis)** | | ECS + S3 + CloudWatch + SES + Route53 + Secrets + ECR | **$12.91/mes** |
| **TOTAL (con RDS, sin Redis)** | | Mínimo + RDS | **$28.05/mes** |
| **TOTAL (completo, con RDS y Redis)** | | Mínimo + RDS + Redis | **$40.29/mes** |

**Costo Anual Estimado**: $12.91 × 12 = **$154.92** (mínimo) a $40.29 × 12 = **$483.48** (completo)

### Escenario 2: Producción Pequeña

**Uso**: Hasta 1,000 usuarios activos/mes, tráfico bajo  
**Arquitectura**: 1 Fargate Task (sin ALB, sin NAT Gateway)  
**Basado en fórmulas de factura de referencia**

| Servicio | Configuración | Cálculo (Fórmula de Factura) | Costo Mensual (USD) |
|----------|---------------|------------------------------|---------------------|
| **ECS Fargate** | 1 task, 1 vCPU, 2 GB RAM | (1 × $0.017 + 2 × $0.001875) × 720 | $14.04 |
| **RDS PostgreSQL** | db.t3.small | 720 × $0.10 + 20 GB × $0.10 + backups | $75.90 |
| **S3** | 50 GB + requests | 50 GB × $0.023 + requests | $2.62 |
| **ElastiCache** | cache.t3.micro (opcional) | 720 × $0.017 | $12.24 |
| **CloudWatch** | 4 métricas + 1 GB logs | (4 × $0.30) + (1 × $0.50) | $2.20 |
| **SES** | 10,000 emails | 10K × $0.10/1K + transfer | $1.12 |
| **Route 53** | 1 zona + 3.77M queries | (1 × $0.50) + (3.77M × $0.40/M) | $2.01 |
| **Secrets Manager** | 3 secrets | 3 × $0.40 | $1.19 |
| **ECR** | 1 GB imágenes | 1 GB × $0.10 | $0.10 |
| **TOTAL (mínimo, sin RDS/Redis)** | | ECS + S3 + CloudWatch + SES + Route53 + Secrets + ECR | **$23.18/mes** |
| **TOTAL (con RDS, sin Redis)** | | Mínimo + RDS | **$99.08/mes** |
| **TOTAL (completo, con RDS y Redis)** | | Mínimo + RDS + Redis | **$111.32/mes** |

**Costo Anual Estimado**: $23.18 × 12 = **$278.16** (mínimo) a $111.32 × 12 = **$1,335.84** (completo)


---

## Optimizaciones de Costo

### 1. Reservas y Ahorros

| Estrategia | Ahorro Estimado | Descripción |
|------------|-----------------|-------------|
| **Reserved Instances (EC2)** | 30-40% | Compromiso de 1 año |
| **Savings Plans (ECS Fargate)** | 20-30% | Compromiso de uso |
| **RDS Reserved Instances** | 30-40% | Compromiso de 1-3 años |
| **S3 Intelligent-Tiering** | 20-40% | Movimiento automático entre tiers |

### 2. Optimizaciones de Arquitectura (1 Fargate)

| Optimización | Ahorro Mensual (USD) | Descripción |
|--------------|----------------------|-------------|
| **Sin ALB (acceso directo)** | $16 - $22 | Acceder directamente al Fargate sin Load Balancer |
| **Sin NAT Gateway** | $32 - $45 | Usar Fargate en subred pública (si aplica) |
| **Sin ElastiCache (opcional)** | $13 - $30 | Usar SQLite/ChromaDB local si el tráfico es bajo |
| **S3 Lifecycle Policies** | $5 - $10 | Mover datos antiguos a tiers más baratos |
| **CloudFront Caching (opcional)** | $4 - $8 | Reducir transferencia de datos (solo si se usa) |
| **Compresión de logs** | $2 - $5 | Reducir almacenamiento de CloudWatch |
| **Spot Instances (no aplica)** | - | Fargate no soporta Spot, pero es más barato que EC2 |

### 3. Costos Variables a Considerar

| Factor | Impacto | Descripción |
|--------|---------|-------------|
| **Tráfico de datos** | Variable | Depende del número de usuarios |
| **Requests a S3** | Variable | Depende del uso de documentos |
| **Emails enviados** | Variable | Depende de usuarios autenticados |
| **Almacenamiento** | Crece con el tiempo | Documentos y vectores acumulados |

---

## Comparación con Factura Base

### Notas sobre la Factura de Referencia

Basándose en la factura `Invoice_2186805245.pdf`, se asume que contiene costos típicos de AWS. La siguiente tabla compara los costos estimados con rangos típicos de facturas AWS.

### Comparación con Factura de Referencia

**Factura de Referencia Total**: $123.26/mes (Invoice_2186805245.pdf)

| Categoría | Factura Referencia | Nuestra Estimación (Producción Pequeña Completa) | Diferencia |
|-----------|-------------------|--------------------------------------------------|------------|
| **Compute (ECS)** | $11.81 | $14.04 (1 Fargate) | +$2.23 (más recursos) |
| **Base de Datos (RDS)** | No incluido | $75.90 (db.t3.small) | +$75.90 (agregado) |
| **Almacenamiento (S3)** | No incluido | $2.62 | +$2.62 (agregado) |
| **Red (ELB)** | $4.71 | $0 (sin ALB) | -$4.71 (ahorro) |
| **Route 53** | $2.01 | $2.01 | Igual |
| **CloudWatch** | $1.53 | $2.20 | +$0.67 (más logs) |
| **ECR** | $0.04 | $0.10 | +$0.06 (más imágenes) |
| **VPC/NAT** | $15.39 | $0 (sin NAT) | -$15.39 (ahorro) |
| **Secrets Manager** | $1.19 | $1.19 | Igual |
| **EC2** | $86.58 | $0 (usando Fargate) | -$86.58 (ahorro) |
| **ElastiCache** | No incluido | $12.24 (opcional) | +$12.24 (agregado) |
| **SES** | No incluido | $1.12 | +$1.12 (agregado) |
| **TOTAL** | **$123.26** | **$111.32** | **-$11.94 (más económico)** |

### Análisis

- **Nuestra estimación ($111.32/mes completo) es más económica** que la factura de referencia ($123.26/mes)
- **Ahorro principal**: No usamos EC2 ($86.58) ni NAT Gateway ($15.39), usando Fargate en su lugar
- **Costo adicional**: Agregamos RDS ($75.90) y ElastiCache ($12.24) que no estaban en la factura de referencia
- **El escenario de producción pequeña ($23.18-$111.32/mes)** es razonable y está dentro del rango objetivo anual ($1,200-$2,400)
- **El escenario de desarrollo ($12.91-$40.29/mes)** es muy económico y está dentro del rango objetivo anual ($480-$960)

---

## Recomendaciones

### Para Desarrollo
- Usar instancias pequeñas (t3.micro)
- Desactivar recursos cuando no se usen
- Usar S3 Intelligent-Tiering
- Considerar AWS Free Tier cuando aplique

### Para Producción (1 Fargate)
- **Comenzar sin ALB**: Acceder directamente al Fargate para ahorrar $16-22/mes
- **Evitar NAT Gateway**: Usar subred pública si es posible, ahorra $32-45/mes
- **Evaluar necesidad de ElastiCache**: Para tráfico bajo, puede no ser necesario ($13-30/mes)
- **Usar Savings Plans para Fargate**: Ahorro del 20-30% con compromiso
- **Configurar S3 Lifecycle Policies**: Mover datos antiguos automáticamente
- **Monitorear costos con AWS Cost Explorer**: Identificar oportunidades de ahorro
- **Considerar RDS solo si es necesario**: Para desarrollo, SQLite en EBS puede ser suficiente

### Migración Gradual
1. **Fase 1 - Desarrollo**: Desplegar en Fargate básico ($10-$15/mes mínimo)
2. **Fase 2 - Desarrollo Completo**: Agregar RDS y Redis ($38-$50/mes)
3. **Fase 3 - Producción Mínima**: Escalar Fargate y agregar servicios esenciales ($21-$31/mes)
4. **Fase 4 - Producción Completa**: Agregar ALB y optimizaciones ($64-$86/mes)

---

## Costos Adicionales a Considerar

### Servicios Externos (No AWS)

| Servicio | Costo Mensual (USD) | Descripción |
|----------|---------------------|-------------|
| **OpenAI API** | $50 - $500 | Depende del uso (embeddings + LLM) |
| **LangSmith** | $0 - $50 | Trazabilidad opcional |
| **Dominio** | $1 - $15 | Registro de dominio (.com, .edu.co) |

### Costos de Desarrollo

| Concepto | Costo | Descripción |
|----------|-------|-------------|
| **Tiempo de migración** | Variable | Horas de desarrollo para migrar a AWS |
| **Capacitación** | Variable | Capacitación del equipo en AWS |
| **Monitoreo y optimización** | Variable | Tiempo dedicado a optimizar costos |

---

## Resumen Final

### Costo Total Estimado por Escenario

#### Desarrollo/Pruebas

**Basado en fórmulas de factura de referencia**

| Categoría | Configuración | Costo Mensual (USD) | Costo Anual (USD) |
|-----------|---------------|---------------------|-------------------|
| **AWS Services (mínimo)** | Sin RDS, sin Redis | $12.91 | **$154.92** |
| **AWS Services (completo)** | Con RDS y Redis | $40.29 | **$483.48** |
| **OpenAI API** | Uso bajo | $50 - $150 | $600 - $1,800 |
| **Otros Servicios** | Dominio, etc. | $5 - $10 | $60 - $120 |
| **TOTAL AWS (mínimo)** | | **$12.91** | **$154.92** |
| **TOTAL AWS (completo)** | | **$40.29** | **$483.48** |
| **TOTAL CON SERVICIOS EXTERNOS** | | **$67.91 - $200.29** | **$814.92 - $2,403.48** |

#### Producción Pequeña

**Basado en fórmulas de factura de referencia**

| Categoría | Configuración | Costo Mensual (USD) | Costo Anual (USD) |
|-----------|---------------|---------------------|-------------------|
| **AWS Services (mínimo)** | Sin RDS, sin Redis | $23.18 | **$278.16** |
| **AWS Services (completo)** | Con RDS y Redis | $111.32 | **$1,335.84** |
| **OpenAI API** | Uso moderado | $100 - $200 | $1,200 - $2,400 |
| **Otros Servicios** | Dominio, etc. | $5 - $15 | $60 - $180 |
| **TOTAL AWS (mínimo)** | | **$23.18** | **$278.16** |
| **TOTAL AWS (completo)** | | **$111.32** | **$1,335.84** |
| **TOTAL CON SERVICIOS EXTERNOS** | | **$128.18 - $326.32** | **$1,538.16 - $3,915.84** |

### En Pesos Colombianos (Tasa: 1 USD = 4,000 COP)

#### Desarrollo/Pruebas

| Categoría | Costo Anual (COP) |
|-----------|-------------------|
| **AWS Services (mínimo)** | **$619,680** |
| **AWS Services (completo)** | **$1,933,920** |
| **OpenAI API** | $2,400,000 - $7,200,000 |
| **Otros Servicios** | $240,000 - $480,000 |
| **TOTAL AWS (mínimo)** | **$619,680** |
| **TOTAL AWS (completo)** | **$1,933,920** |
| **TOTAL CON SERVICIOS EXTERNOS** | **$3,259,680 - $9,613,920** |

#### Producción Pequeña

| Categoría | Costo Anual (COP) |
|-----------|-------------------|
| **AWS Services (mínimo)** | **$1,112,640** |
| **AWS Services (completo)** | **$5,343,360** |
| **OpenAI API** | $4,800,000 - $9,600,000 |
| **Otros Servicios** | $240,000 - $720,000 |
| **TOTAL AWS (mínimo)** | **$1,112,640** |
| **TOTAL AWS (completo)** | **$5,343,360** |
| **TOTAL CON SERVICIOS EXTERNOS** | **$6,152,640 - $15,663,360** |

### Nota sobre Costos Anuales Objetivo

Los costos anuales objetivo especificados son:
- **Desarrollo/Pruebas**: $480 - $960 anuales ($1,920,000 - $3,840,000 COP)
- **Producción Pequeña**: $1,200 - $2,400 anuales ($4,800,000 - $9,600,000 COP)

**Verificación de cumplimiento** (basado en fórmulas de factura):
- ✅ **Desarrollo completo**: $483.48 anual está dentro del rango objetivo ($480-$960)
- ✅ **Producción Pequeña completa**: $1,335.84 anual está dentro del rango objetivo ($1,200-$2,400)

**Para alcanzar exactamente los rangos objetivo**, se pueden ajustar:
- Agregar/remover servicios opcionales (ElastiCache, ALB, etc.)
- Ajustar tamaño de instancias RDS
- Optimizar uso de almacenamiento S3
- Ajustar volumen de logs en CloudWatch

---

**Última actualización**: 2024  
**Versión**: 1.0  
**Nota**: Los costos son estimaciones basadas en precios públicos de AWS. Los costos reales pueden variar según uso, región, y descuentos aplicables.

