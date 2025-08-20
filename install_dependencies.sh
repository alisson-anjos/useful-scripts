#!/bin/bash
# Script para instalar dependências do RIFE Video Processor

echo "🚀 Instalando dependências para processamento RIFE..."

# Detectar sistema operacional
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "🖥️  Sistema detectado: $MACHINE"

# Função para instalar FFmpeg
install_ffmpeg() {
    echo "📦 Instalando FFmpeg..."
    
    case $MACHINE in
        Linux)
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y ffmpeg
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y ffmpeg
            elif command -v pacman &> /dev/null; then
                sudo pacman -S ffmpeg
            else
                echo "❌ Gerenciador de pacotes não suportado. Instale FFmpeg manualmente."
                exit 1
            fi
            ;;
        Mac)
            if command -v brew &> /dev/null; then
                brew install ffmpeg
            else
                echo "❌ Homebrew não encontrado. Instale-o primeiro ou instale FFmpeg manualmente."
                exit 1
            fi
            ;;
        *)
            echo "❌ Sistema não suportado para instalação automática do FFmpeg."
            exit 1
            ;;
    esac
}

# Função para baixar RIFE
install_rife() {
    echo "🎯 Baixando RIFE-NCNN-Vulkan..."
    
    # Criar diretório para RIFE
    mkdir -p rife-ncnn-vulkan
    cd rife-ncnn-vulkan
    
    case $MACHINE in
        Linux)
            echo "📥 Baixando versão Linux..."
            wget -O rife.zip "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20220901/rife-ncnn-vulkan-20220901-ubuntu.zip"
            ;;
        Mac)
            echo "📥 Baixando versão macOS..."
            wget -O rife.zip "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20220901/rife-ncnn-vulkan-20220901-macos.zip"
            ;;
        *)
            echo "❌ Sistema não suportado para download automático do RIFE."
            echo "Baixe manualmente de: https://github.com/nihui/rife-ncnn-vulkan/releases"
            exit 1
            ;;
    esac
    
    # Extrair arquivo
    if command -v unzip &> /dev/null; then
        unzip rife.zip
        rm rife.zip
    else
        echo "❌ unzip não encontrado. Extraia o arquivo manualmente."
        exit 1
    fi
    
    # Tornar executável
    chmod +x rife-ncnn-vulkan
    
    # Voltar ao diretório anterior
    cd ..
    
    echo "✅ RIFE instalado em: $(pwd)/rife-ncnn-vulkan/"
}

# Verificar se FFmpeg já está instalado
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg já está instalado"
else
    install_ffmpeg
fi

# Verificar se RIFE já está instalado
if [ -f "rife-ncnn-vulkan/rife-ncnn-vulkan" ]; then
    echo "✅ RIFE já está instalado"
else
    install_rife
fi

echo ""
echo "🎉 Instalação concluída!"
echo ""
echo "📋 Como usar:"
echo "  1. Processar um único vídeo:"
echo "     python3 rife_processor.py video.mp4"
echo ""
echo "  2. Processar todos os vídeos de uma pasta:"
echo "     python3 rife_processor.py /pasta/dos/videos/"
echo ""
echo "  3. Personalizar configurações:"
echo "     python3 rife_processor.py videos/ --fps 30 --duration 4 --output-dir saida_custom"
echo ""
echo "  4. Se RIFE estiver em local diferente:"
echo "     python3 rife_processor.py videos/ --rife-path /caminho/para/rife-ncnn-vulkan"
echo ""
echo "⚠️  Certifique-se de que sua GPU suporta Vulkan para melhor performance!"
