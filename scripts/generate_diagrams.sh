#!/bin/bash
# Script para generar todos los diagramas C4
# Uso: ./scripts/generate_diagrams.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIAGRAMS_DIR="$PROJECT_ROOT/DOCs/diagrams"
GENERATED_DIR="$DIAGRAMS_DIR/generated"

# Crear directorio de salida si no existe
mkdir -p "$GENERATED_DIR"

echo "🎨 Generando diagramas C4..."
echo "📁 Directorio de diagramas: $DIAGRAMS_DIR"
echo ""

# Verificar y generar diagramas PlantUML
if command -v plantuml &> /dev/null; then
    echo "✅ PlantUML encontrado"
    echo "📊 Generando diagramas PlantUML..."
    
    cd "$DIAGRAMS_DIR"
    plantuml -o generated *.puml 2>&1 | grep -v "Creating" || true
    
    echo "✅ Diagramas PlantUML generados"
else
    echo "⚠️  PlantUML no está instalado"
    echo "   Instala con: brew install plantuml (macOS) o sudo apt-get install plantuml (Linux)"
    echo "   O usa el servidor web: http://www.plantuml.com/plantuml/uml/"
fi

echo ""

# Verificar y generar diagramas Mermaid
if command -v mmdc &> /dev/null; then
    echo "✅ Mermaid CLI encontrado"
    echo "📊 Generando diagramas Mermaid..."
    
    cd "$DIAGRAMS_DIR"
    for file in *.mmd; do
        if [ -f "$file" ]; then
            echo "   Generando: $file"
            mmdc -i "$file" -o "generated/$(basename "$file" .mmd).png" 2>/dev/null || true
        fi
    done
    
    echo "✅ Diagramas Mermaid generados"
else
    echo "⚠️  Mermaid CLI no está instalado"
    echo "   Instala con: npm install -g @mermaid-js/mermaid-cli"
fi

echo ""
echo "✨ ¡Proceso completado!"
echo "📂 Diagramas generados en: $GENERATED_DIR"
echo ""
echo "📋 Archivos generados:"
ls -lh "$GENERATED_DIR" 2>/dev/null || echo "   (ningún archivo generado)"


