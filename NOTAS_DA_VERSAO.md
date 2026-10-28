# Fora de Cena 0.5.0-beta.1 — Apple Silicon · 28/10/2026

Primeiro download público para Mac Apple Silicon, M1 em diante, macOS 15+. **Beta**, com build nativo e autoteste aprovados e funcionamento confirmado pelo proprietário em seu M1. Windows continua em 0.4.0; não há download público Linux ou Intel nesta Release.

## Baixar

[**Baixar aplicativo Mac — DMG**](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.1/ForaDeCena-0.5.0-beta.1-macos-arm64-experimental.dmg). Este é o único arquivo necessário para usar o aplicativo. [Guia completo de instalação, autorização e OBS](MAC_APPLE_SILICON.md).

## Novidades

- Aplicativo `.app` dentro de um DMG, com Python, bibliotecas e modelos incluídos.
- Captura AVFoundation e ajustes da janela Configurar no Mac.
- Aquecimento da segmentação e início da animação após a preparação para melhorar o teleporte.
- Composição interna otimizada no Mac, preservando resolução de captura/saída.
- Fundo Estático como padrão, restauração manual e saída para OBS Virtual Camera.

## Primeira abertura

Arraste o app para Aplicativos. Se a Apple não conseguir verificar o aplicativo, após tentar abri-lo use **Ajustes do Sistema → Privacidade e Segurança → Abrir Mesmo Assim → Abrir**. Autorize a câmera quando solicitado. Não desative Gatekeeper. Não há Developer ID nem notarização Apple nesta versão.

Teste primeiro Só prévia, capture o fundo vazio e experimente os efeitos e Restaurar. Para reuniões, prepare OBS 30+ e autorize sua extensão de câmera; os passos estão no guia Mac. A extensão do navegador é opcional, apenas para sair da aba vinculada do Meet.

## Limitações e privacidade

As imagens são processadas no dispositivo. O fornecedor MediaPipe declara métricas de uso/desempenho. Houve tentativas HTTPS numa amostra sintética Linux, sem captura do conteúdo; a origem exata e sessões longas ainda precisam de investigação. Leia [PRIVACY.md](PRIVACY.md) antes de iniciar a câmera. Não é certificação de funcionamento totalmente sem rede.

`distribution_ready=false` e `dependency_network_verified=false` permanecem: beta experimental, sem certificação de todas as webcams, Macs, versões do macOS ou serviços de chamada. O teste do proprietário não detalhou individualmente todos esses casos. Fundo em movimento continua experimental e 720p/30 FPS depende do hardware.

## Fontes e licenças

O DMG é exatamente o pacote testado: commit `b80b504a383d123cf834997757a77b764a66e585`. A tag aponta para esse commit. A documentação atualizada está na main. O ZIP de fontes anexado preserva os fontes correspondentes ao build, incluindo seus documentos da época.

Fontes do app, fontes correspondentes do auxiliar independente GPL-2.0-only, avisos de licença e `SHA256SUMS.txt` acompanham o download. Esses arquivos não precisam ser compilados ou instalados pelo usuário. Consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
