# 📐 Diagramas de Arquitectura C4

Este directorio contiene los archivos fuente para generar los diagramas de arquitectura C4 del Sistema de Recomendación de Posgrados ICESI.

## 📁 Estructura

```
diagrams/
├── C4_Context.puml              # Diagrama de contexto (PlantUML)
├── C4_Container.puml             # Diagrama de contenedores (PlantUML)
├── C4_Component.puml             # Diagrama de componentes (PlantUML)
├── sequence_complete.mmd          # Flujo completo (Mermaid)
├── sequence_auth.mmd              # Flujo de autenticación (Mermaid)
├── generated/                     # Diagramas generados (PNG/SVG)
│   └── .gitkeep
└── README.md                      # Este archivo
```

## 🚀 Generación de Diagramas

### Prerrequisitos

#### PlantUML
```bash
# macOS
brew install plantuml

# Linux
sudo apt-get install plantuml

# O usar servidor web: http://www.plantuml.com/plantuml/uml/
```

#### Mermaid CLI
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Generar Diagramas

#### Opción 1: Script Automatizado

```bash
# Desde la raíz del proyecto
./scripts/generate_diagrams.sh
```

#### Opción 2: Manual

**PlantUML:**
```bash
cd DOCs/diagrams
plantuml *.puml -o generated
```

**Mermaid:**
```bash
cd DOCs/diagrams
mmdc -i sequence_complete.mmd -o generated/sequence_complete.png
mmdc -i sequence_auth.mmd -o generated/sequence_auth.png
```

## 📊 Diagramas Disponibles

### Nivel 1: Contexto
- **Archivo**: `C4_Context.puml`
- **Descripción**: Muestra el sistema en su entorno, incluyendo usuarios y sistemas externos
- **Audiencia**: Stakeholders, gerentes, clientes

### Nivel 2: Contenedores
- **Archivo**: `C4_Container.puml`
- **Descripción**: Descompone el sistema en contenedores principales (aplicaciones, bases de datos)
- **Audiencia**: Arquitectos, desarrolladores senior

### Nivel 3: Componentes
- **Archivo**: `C4_Component.puml`
- **Descripción**: Muestra los componentes internos del backend
- **Audiencia**: Desarrolladores del equipo

### Diagramas de Secuencia

#### Flujo Completo
- **Archivo**: `sequence_complete.mmd`
- **Descripción**: Flujo completo desde autenticación hasta recomendación
- **Incluye**: Autenticación, entrevista, análisis, recomendación

#### Flujo de Autenticación
- **Archivo**: `sequence_auth.mmd`
- **Descripción**: Proceso detallado de autenticación OTP
- **Incluye**: Envío y verificación de código OTP

## 🔄 Actualización de Diagramas

Cuando la arquitectura cambie:

1. **Actualizar archivos fuente** (`.puml` o `.mmd`)
2. **Regenerar diagramas** usando los comandos arriba
3. **Revisar cambios** en los diagramas generados
4. **Commit cambios** en Git

## 📝 Notas

- Los archivos fuente (`.puml`, `.mmd`) están versionados en Git
- Los diagramas generados (`.png`, `.svg`) pueden estar en `.gitignore` si son muy grandes
- Los diagramas Mermaid se pueden ver directamente en GitHub (renderizado automático)

## 🔗 Referencias

- [Documentación C4 Completa](../C4_ARCHITECTURE_DIAGRAMS.md)
- [C4 Model](https://c4model.com/)
- [PlantUML](https://plantuml.com/)
- [Mermaid](https://mermaid.js.org/)



