# Linux — beta experimental 0.5.0-beta.1

**Problema conhecido no Linux beta.1:** houve falha de abertura confirmada ao carregar as ilustrações (`PIL._tkinter_finder` ausente). A correção 0.5.0-beta.2 está em preparação e ainda não foi publicada. Os downloads Mac/Windows não são substituídos por essa correção.

**Não foi testada em uma máquina Linux real por um usuário. Pode apresentar bugs, falhas de câmera ou incompatibilidades.** Compilação nativa, testes automatizados, inferência sintética e autotestes dos pacotes passaram nos runners Linux do GitHub. Isso não certifica webcam, desempenho, saída virtual ou chamadas reais.

## Qual arquivo baixar

| Computador | Arquivo |
| --- | --- |
| PC Intel/AMD de 64 bits, `uname -m` mostra `x86_64` | [Linux x64 — TAR.GZ](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.1/ForaDeCena-0.5.0-beta.1-linux-x86_64-experimental.tar.gz) |
| Linux ARM64, `uname -m` mostra `aarch64` ou `arm64` | [Linux ARM64 — TAR.GZ](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.1/ForaDeCena-0.5.0-beta.1-linux-arm64-experimental.tar.gz) |

Base de build Ubuntu 22.04, glibc 2.35, ambiente gráfico. Outras distribuições e versões ainda não estão validadas. Não há pacote para 32 bits ou Alpine/musl. As bibliotecas gráficas do sistema podem precisar ser instaladas pelo gerenciador da distribuição. Não existe promessa de pacote universal para todo Linux.

## Abrir e testar

1. Baixe o TAR.GZ da sua arquitetura.
2. Extraia pelo gerenciador de arquivos, preservando a pasta `ForaDeCena` e seus recursos.
3. Abra o executável `ForaDeCena` dentro dessa pasta. Se não abrir por duplo clique, abra um terminal na pasta e execute `./ForaDeCena`.
4. Não execute com `sudo`. Não precisa instalar Python, baixar o repositório nem compilar.
5. Selecione **Só prévia**, escolha sua webcam e inicie a câmera.
6. Use fundo **Estático**, capture o cenário vazio, confirme o fundo e teste os gestos, os efeitos e Restaurar. Deixe funcionando alguns minutos e informe eventuais travamentos.

Fontes do auxiliar e avisos de licença estão disponíveis ao lado de cada pacote, na mesma Release. Quem só quer executar não precisa extrair ou compilar esses ZIPs. Para compartilhar o aplicativo, mantenha também o acesso a esses fontes e avisos.

## Usar em chamadas

A prévia não exige driver virtual. Para Meet/Discord/gravadores, o Linux precisa de **v4l2loopback**, módulo configurado pelo administrador do sistema. O app não instala módulos, altera Secure Boot nem muda permissões dos dispositivos automaticamente.

Quando o dispositivo estiver pronto, selecione **Câmera virtual Linux** e o dispositivo correto de saída. Use a webcam física como entrada. Inicie o envio no Fora de Cena antes de selecionar a câmera virtual na chamada. Veja o preparo técnico em [MAC_LINUX.md](MAC_LINUX.md). Navegadores Snap/Flatpak e X11/Wayland podem exigir investigação separada.

## Relatar um erro ou resultado de teste

[**Abrir relato no GitHub Issues**](https://github.com/arantes-gabs/fora-de-cena/issues/new/choose) — exige conta GitHub. Escolha **Relatar erro** ou **Resultado de teste da beta**. Relatos são públicos e não concedem permissão para editar o repositório.

Informe distribuição/versão, arquitetura, versão do app, X11/Wayland se souber, o que tentou, resultado esperado e resultado observado. Se falhar ao abrir, copie o erro do terminal **após remover nomes de usuário, caminhos pessoais, tokens, senhas e chaves**. Não publique gravações privadas nem os arquivos de preferências ou pareamento. Para vulnerabilidades, siga [SECURITY.md](SECURITY.md), em vez de publicar detalhes exploráveis em Issues.

## Integridade e privacidade

[Linux-SHA256SUMS.txt](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.1/Linux-SHA256SUMS.txt) contém os hashes dos dois pacotes e dos respectivos ZIPs de fontes/licenças. Na pasta dos downloads, `sha256sum NOME_DO_ARQUIVO.tar.gz` permite conferir o arquivo escolhido. O checksum não é certificação de segurança.

As imagens são processadas no dispositivo. O MediaPipe declara métricas; tentativas HTTPS foram observadas em uma amostra sintética, sem captura do conteúdo. A origem exata e sessões longas continuam em investigação. Leia [PRIVACY.md](PRIVACY.md) antes de usar. A beta não é certificada como totalmente sem rede. `distribution_ready=false` e `dependency_network_verified=false` permanecem.
