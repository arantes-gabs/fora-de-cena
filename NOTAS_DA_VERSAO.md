# Fora de Cena 0.5.0-beta.2 — correção de abertura no Linux

**Beta experimental Linux x64 e ARM64. Esta versão não foi testada em uma máquina Linux real por um usuário e pode apresentar bugs.** Os testes automatizados e o teste gráfico do executável passaram nos runners Linux do GitHub; câmera, desempenho e chamadas reais ainda precisam de validação.

## Baixar o aplicativo

| Computador | Download |
| --- | --- |
| PC Intel/AMD de 64 bits (`x86_64`) | [**Linux x64 — aplicativo TAR.GZ**](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.2/ForaDeCena-0.5.0-beta.2-linux-x86_64-experimental.tar.gz) |
| Linux ARM64 (`aarch64`/`arm64`) | [**Linux ARM64 — aplicativo TAR.GZ**](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.2/ForaDeCena-0.5.0-beta.2-linux-arm64-experimental.tar.gz) |

Baixe apenas o TAR.GZ correto para executar. Os ZIPs de fontes/licenças acompanham a distribuição e não precisam ser instalados ou compilados pelo usuário. `SHA256SUMS.txt` permite conferir os sete arquivos anexados de aplicativo e fontes/avisos.

## Correção desta versão

- Inclui explicitamente `PIL._tkinter_finder` e `PIL._imagingtk`, necessários para o carregamento dinâmico de Pillow/Tk.
- Corrige o `ModuleNotFoundError` relatado ao exibir as imagens de ajuda dos gestos, que fazia a beta.1 Linux encerrar ao abrir.
- Novo teste gráfico bloqueia o pacote se as sete imagens reais não renderizarem dentro do executável Linux. Usa Xvfb, sem webcam, microfone ou ponte Meet.
- Falhas de inicialização Unix passam a orientar pelo terminal onde encontrar o log.

## Como testar

1. Crie uma pasta nova para esta versão. **Não extraia por cima da beta.1.**
2. Extraia o TAR.GZ, mantendo o executável `ForaDeCena` e a pasta `_internal` juntos.
3. Abra `ForaDeCena` ou execute `./ForaDeCena` em um terminal dentro da pasta extraída. Não use sudo. Não precisa instalar Python.
4. Selecione **Só prévia**, escolha a webcam e inicie a câmera.
5. Prepare o fundo **Estático** e teste as imagens de ajuda, os gestos, efeitos e Restaurar.

A base é Ubuntu 22.04/glibc 2.35, com ambiente gráfico. Outras distribuições podem exigir bibliotecas de sistema ou apresentar incompatibilidades. Para transmitir para chamadas, é necessário configurar v4l2loopback; a prévia não exige câmera virtual. [Guia Linux](https://github.com/arantes-gabs/fora-de-cena/blob/main/LINUX.md).

## Relatar problemas ou resultado do teste

[**Abrir relato no GitHub Issues**](https://github.com/arantes-gabs/fora-de-cena/issues/new/choose). Escolha “Relatar erro” ou “Resultado de teste da beta”. Informe versão do app, distribuição/versão, arquitetura, passos e erro observado. Relatos são públicos: remova nomes/caminhos pessoais, senhas, tokens e chaves. Não publique arquivos de sessão ou gravações privadas. Vulnerabilidades seguem [SECURITY.md](https://github.com/arantes-gabs/fora-de-cena/blob/main/SECURITY.md).

## Privacidade e limites

As imagens são processadas no dispositivo. O fornecedor MediaPipe declara métricas de uso/desempenho. Uma amostra sintética registrou tentativas HTTPS sem captura do conteúdo; origem exata e sessões longas seguem em investigação. Leia [PRIVACY.md](https://github.com/arantes-gabs/fora-de-cena/blob/main/PRIVACY.md) antes de usar. Não é certificação de funcionamento totalmente sem rede. `distribution_ready=false` e `dependency_network_verified=false` permanecem nesta beta.

## Fontes e outras plataformas

Tag e pacotes correspondem ao commit `a56e1aab5e2a98b2ecf2003c092d15aeef68708d`. O ZIP de fontes preserva os arquivos do build; a documentação atualizada está na main. Fontes correspondentes do auxiliar GPL-2.0-only e avisos específicos de cada arquitetura estão anexados no mesmo local dos aplicativos.

Este lançamento é somente Linux. Mac Apple Silicon permanece na beta.1 já publicada; Windows continua na 0.4.0. Seus downloads não foram substituídos. Intel não é anunciado como suportado nesta versão.


## Versões anteriores

[0.5.0-beta.1 — Mac Apple Silicon e primeira beta Linux](https://github.com/arantes-gabs/fora-de-cena/releases/tag/v0.5.0-beta.1) · [0.4.0 — Windows](https://github.com/arantes-gabs/fora-de-cena/releases/tag/v0.4.0). A beta.1 Linux tem falha de abertura conhecida; use a beta.2.
