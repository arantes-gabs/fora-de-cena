# Histórico de versões

## 0.5.0-beta.1 — candidata em validação, não lançada

- Integração das correções testadas no Mac M1: Configurar em janela nativa no Mac,
  autorização da extensão de câmera do OBS e auditoria do mínimo real do macOS.
- Teleporte com aquecimento sintético e relógio iniciado após a preparação;
  falha ou atraso do recorte cancela a animação sem ocultar a pessoa de surpresa.
- Composição de camadas otimizada; limite interno de 480 pixels somente no Mac,
  preservando a resolução de captura/saída e o fundo original.
- Adaptadores de captura AVFoundation/V4L2, saída v4l2loopback e seleção do dispositivo Linux.
- Pastas por sistema, pareamento privado em Unix, ícone PNG e restauração local sem Win32.
- Pillow atualizado para 13.0.0; dependências específicas por marcadores de plataforma.
- Receita de build nativo experimental, testes dos adaptadores e workflow de testes em branch separada, com execução manual prevista.
- Novos pacotes ainda dependem de build/teste nativo, revisão das bibliotecas e aprovação para publicação.
- Versão dos pacotes, recursos Windows e metadados do APP separados da versão pública anterior.
- Compilação enxuta do OpenCV estendida ao Linux, com V4L2/JPEG e sem FFmpeg/Qt.
- Receita NumPy Linux da mesma versão sem BLAS/Fortran externos, ainda em validação nativa.
- Observação sintética de syscalls de rede no Linux, sem captura de pacotes ou tráfego pessoal.

## 0.4.0

- Programa independente de saída de vídeo, com protocolo BGR24 local e confirmação
  por quadro após envio à câmera virtual.
- Recuperação de falha e timeout do processo de saída.
- Fontes correspondentes, licenças e modelos verificados por hashes.
- Instalador por usuário e executável único para Windows x64.
- Fontes completos do aplicativo, extensão, testes e receitas disponibilizados
  neste repositório após a publicação inicial dos executáveis.

## 0.3.x

- Nome Fora de Cena, identidade visual e ajuda ilustrada por efeito.
- Gestos específicos: testa, selo de uma mão, estalo visual, pinça, palma e portal.
- Interface simplificada, restauração manual e atalho F8.
- Fundo estático por padrão e atualização de fundo experimental opcional.
- Integração opcional para sair automaticamente da aba vinculada do Meet.

## 0.2.x

- Efeitos procedurais de teleporte, fumaça, poeira, saída digital, desenho e portal.
- Segmentação local da pessoa e composição temporal dos efeitos.

## MVP

- Captura e confirmação do fundo vazio.
- Desaparecimento e reaparecimento com gesto sustentado ou comando manual.
- Prévia local e saída para câmera virtual.


### Desenvolvimento local Mac — OpenCV enxuto

- Compilação própria 4.14.0.94 com AVFoundation/JPEG, sem FFmpeg/GStreamer/HighGUI.
- Wheel explicitamente vinculada a hash/proveniência; auditoria de RPATHs e avisos
  das bibliotecas estáticas. Venv e artefatos anteriores preservados.
- Nenhuma alteração nos efeitos ou fluxo Windows/Linux; candidato não publicado.

### Automação multiplataforma preparada, sem publicação

- Workflow de testes com runners padrão públicos para Windows x64, Mac Apple Silicon e Linux x64/ARM64; testes e compilação opcional sem artifacts armazenados ou Releases.
- Tentativa experimental Mac Intel: compilar a C API MediaPipe 1.1.1 no runner x86_64, manter as versões atuais, conferir a arquitetura/proveniência e empacotar apenas após testes. Ainda sem compilação Intel validada ou download disponível.
- Auditoria Mach-O parametrizada por arquitetura, preservando a verificação ARM64 e recusando bibliotecas ARM no candidato Intel.
- Mantidas as pendências de licenças/fontes nativas, rede do MediaPipe, câmera/chamadas reais e aprovação de publicação. `distribution_ready=false`.
