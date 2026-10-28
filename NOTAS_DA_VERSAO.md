# Fora de Cena 0.5.0-beta.1 — preparação, sem lançamento

Esta candidata não substitui os downloads 0.4.0. `distribution_ready=false`.

- Adaptação para Mac Apple Silicon e Linux x64/ARM64; Intel permanece experimental.
- Correções de Configurar no Mac, recursos Tk empacotados e fluidez do teleporte.
- Receitas nativas com verificações de modelos, arquitetura, avisos e proveniência.
- OpenCV enxuto no Mac ARM64 e em teste no Linux, sem FFmpeg/Qt.
- NumPy Linux sem BLAS externo em teste, mantendo a versão da aplicação.
- Checagem limitada de rede no Linux e diagnósticos públicos com dados sensíveis ocultados.

Resultados e pendências reais: [MULTIPLATAFORMA.md](MULTIPLATAFORMA.md).

## Versão publicada anterior — 0.4.0

- Fundo estático como padrão, inclusive ao atualizar.
- Escolha manual de fundo lembrada após a primeira abertura desta atualização.
- Preparar vídeo para o Meet preserva o tipo de fundo.
- Duas opções: instalador e executável único com Python e modelos incluídos.
- OBS Virtual Camera continua necessário para chamadas; extensão é opcional.

- Saída virtual independente, com confirmação por quadro e recuperação de falhas.
- Fontes correspondentes e licenças acompanham os downloads.

**Status:** versão pública inicial de avaliação. Testes automatizados e diagnósticos dos pacotes passaram; câmera, instalação e chamada reais precisam ser conferidas em cada computador.
