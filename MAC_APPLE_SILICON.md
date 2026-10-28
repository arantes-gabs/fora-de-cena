# Fora de Cena no Mac — Apple Silicon

Beta 0.5.0-beta.1 para M1 em diante, com macOS 15 ou posterior. Aplicativo empacotado: não precisa instalar Python, baixar o repositório nem compilar.

## Baixar e abrir

1. [Baixe o DMG para Apple Silicon](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.1/ForaDeCena-0.5.0-beta.1-macos-arm64-experimental.dmg).
2. Abra o DMG e arraste **Fora de Cena.app** para **Aplicativos**.
3. Abra o aplicativo pela pasta Aplicativos.
4. Como esta beta não tem Developer ID nem notarização Apple, pode aparecer “A Apple não pôde verificar…”. Após tentar abrir, vá a **Ajustes do Sistema → Privacidade e Segurança**, localize Fora de Cena e escolha **Abrir Mesmo Assim → Abrir**. Autorize somente o arquivo baixado da Release oficial. Não desative Gatekeeper nem use comandos para remover proteções. Computadores gerenciados podem impedir a autorização.
5. Ao iniciar a câmera, permita o acesso à webcam. Se negar, confira **Privacidade e Segurança → Câmera** e reinicie o app.

O DMG é o único arquivo necessário para executar. Os fontes do auxiliar e os avisos de licença ficam disponíveis na mesma Release; não precisam ser compilados ou extraídos pelo usuário. [Downloads, fontes, licenças e SHA-256](https://github.com/arantes-gabs/fora-de-cena/releases/tag/v0.5.0-beta.1).

## Primeiro teste

Escolha **Só prévia**, selecione sua webcam e inicie a câmera. Use o fundo **Estático**, clique em Capturar fundo, saia do enquadramento e confirme o fundo vazio. Volte e experimente o gesto indicado ou o botão manual. Use Restaurar para recuperar a imagem. No Mac, F8 é um atalho local e alguns teclados exigem Fn+F8.

## Enviar para Meet, Discord, Teams ou OBS

A prévia funciona sem OBS. Para enviar o resultado como câmera virtual:

1. Instale [OBS Studio pelo site oficial](https://obsproject.com/download), versão 30 ou posterior compatível com seu macOS.
2. Abra o OBS, inicie e pare a câmera virtual uma vez e feche o OBS.
3. No macOS 15+, se solicitado, autorize **OBS Virtual Camera** em **Ajustes do Sistema → Geral → Itens de Início e Extensões → Extensões de Câmera**. Feche e reabra o navegador depois da autorização.
4. Selecione **OBS Virtual Camera** como saída do Fora de Cena e inicie o vídeo. Não deixe a câmera virtual iniciada no OBS ao mesmo tempo.
5. No serviço de chamada, selecione **OBS Virtual Camera** e desative os efeitos de fundo do serviço. Seu microfone continua sendo o da chamada.

A compatibilidade depende do navegador, aplicativo e permissões. A extensão opcional do Chrome serve somente para sair automaticamente da aba vinculada do Meet; não é necessária para transmitir os efeitos. A opção de sair começa desligada. Consulte [COMO_USAR.md](COMO_USAR.md).

## Privacidade e limites da beta

As imagens são processadas no dispositivo. O MediaPipe declara métricas de uso/desempenho; uma amostra sintética Linux registrou tentativas HTTPS, sem captura do conteúdo. A origem exata e o comportamento em sessões longas seguem em investigação. Leia [PRIVACY.md](PRIVACY.md) antes de usar; esta beta não é certificada como totalmente sem rede. Se não concordar com esse comportamento declarado da dependência, não inicie a câmera.

Build nativo, inferência e autoteste do APP passaram. O proprietário confirmou funcionamento no seu M1 em 28/10/2026; não especificou separadamente todos os casos de câmera, chamada ou versão do macOS. Isso não certifica todas as combinações de hardware e serviços. `distribution_ready=false` e `dependency_network_verified=false` permanecem para a beta experimental.

Linux e Intel continuam em testes, sem download público neste lançamento. Windows 0.4.0 permanece disponível. Não há áudio, garantia de 30 FPS ou dispensa do preparo do fundo. Se houver lentidão, tente 640 × 480 e fundo Estático.

## Conferir integridade

Na pasta do DMG baixado, execute no Terminal:

```sh
shasum -a 256 ForaDeCena-0.5.0-beta.1-macos-arm64-experimental.dmg
```

Compare com `SHA256SUMS.txt` da Release. O checksum confere os bytes e não substitui notarização. Ao relatar erro, remova nomes de usuário, caminhos pessoais e chaves dos logs.

Referências: [Apple — abrir apps baixados](https://support.apple.com/pt-br/102445), [OBS — câmera virtual](https://obsproject.com/kb/virtual-camera-troubleshooting).
