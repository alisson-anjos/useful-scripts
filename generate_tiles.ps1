param (
    [string]$inputFolder = ".",   # Pasta onde estão os vídeos (padrão: diretório atual)
    [int]$tileWidth = 512,        # Largura do tile (padrão: 512)
    [int]$tileHeight = 512        # Altura do tile (padrão: 512)
)

# Verificar se a pasta existe
if (-Not (Test-Path $inputFolder -PathType Container)) {
    Write-Host "Erro: A pasta '$inputFolder' não existe!" -ForegroundColor Red
    exit
}

# Obter todos os arquivos de vídeo da pasta
$videoFiles = Get-ChildItem -Path $inputFolder -Filter *.mp4

if ($videoFiles.Count -eq 0) {
    Write-Host "Nenhum arquivo .mp4 encontrado na pasta '$inputFolder'." -ForegroundColor Yellow
    exit
}

# Loop para processar cada vídeo
foreach ($video in $videoFiles) {
    $inputVideo = $video.FullName
    $videoName = [System.IO.Path]::GetFileNameWithoutExtension($video.Name)
    $outputFolder = "$inputFolder\$videoName-tiles"

    # Criar pasta para os tiles
    if (-Not (Test-Path $outputFolder)) {
        New-Item -ItemType Directory -Path $outputFolder | Out-Null
    }

    # Obter resolução do vídeo usando ffprobe
    $videoWidth = [int](ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$inputVideo")
    $videoHeight = [int](ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$inputVideo")

    # Calcular número de tiles
    $columns = [math]::Floor($videoWidth / $tileWidth)
    $rows = [math]::Floor($videoHeight / $tileHeight)

    $tileCount = 1

    # Loop para gerar os tiles
    for ($y = 0; $y -lt $rows; $y++) {
        for ($x = 0; $x -lt $columns; $x++) {
            $xOffset = $x * $tileWidth
            $yOffset = $y * $tileHeight
            $outputFile = "$outputFolder\tile_$tileCount.mp4"

            # Executar FFmpeg para cortar o vídeo
            ffmpeg -i "$inputVideo" -vf "crop=${tileWidth}:${tileHeight}:${xOffset}:${yOffset}" -c:a copy "$outputFile"

            Write-Host "Tile $tileCount criado para '$videoName': $outputFile"
            $tileCount++
        }
    }

    Write-Host "Processo concluído para '$videoName'. Tiles salvos em: $outputFolder" -ForegroundColor Green
}

Write-Host "Todos os vídeos foram processados!" -ForegroundColor Cyan
