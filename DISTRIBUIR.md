# Gerar e distribuir o Fora de Cena

## Executáveis prontos

A [Release 0.4.0](https://github.com/arantes-gabs/fora-de-cena/releases/tag/v0.4.0)
oferece instalador por usuário e executável único. Ambos incluem Python, modelos,
interface e o programa independente de saída. O OBS é instalado separadamente
pelo usuário para disponibilizar a câmera virtual. A extensão do Meet é opcional.

Os executáveis ainda não possuem assinatura digital. Não desative as proteções
do Windows para executá-los. Confira os hashes da versão publicada.

## Ambiente de build — candidata 0.5.0-beta.1

Os comandos desta branch preparam a próxima candidata; não atualizam a Release 0.4.0.

Use Windows x64, Python 3.14 x64 com Tcl/Tk e Git. Primeiro prepare o ambiente
seguindo [DESENVOLVIMENTO.md](DESENVOLVIMENTO.md), incluindo modelos e dependências
de `requirements-build.txt`.

Para o instalador, instale o compilador Inno Setup pelo site oficial. O projeto
foi empacotado com Inno Setup 6.7.3; informe o caminho de `ISCC.exe` com `--iscc`.
O executável único não precisa desse compilador.

Na raiz do repositório:

```powershell
.venv\Scripts\python.exe -B tools/fetch_distribution_sources.py
.venv\Scripts\python.exe -B tools/build_windows.py --single-file
.venv\Scripts\python.exe -B tools/build_windows.py --iscc "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

O primeiro comando baixa os fontes oficiais do PyVirtualCam 0.15.0, seu submódulo
libyuv e as fichas dos modelos. Os commits e hashes são fixados e conferidos.
Tudo fica em `work/`, fora do Git. Não são instalados drivers por esse comando.
O script não deve precisar de tokens de GitHub.

O build compila o programa independente primeiro, coleta licenças e gera o app.
Confere os modelos, recusa dependências indevidas no agregado e executa diagnósticos
sintéticos dos binários, inclusive em caminhos com espaços e acentos. Não abre a
webcam, não instala o produto e não publica no GitHub.

Os arquivos ficam em `dist/windows/`:

- `ForaDeCena-0.5.0-beta.1-Portatil.exe`: arquivo único, com extração automática ao abrir.
- `ForaDeCena-0.5.0-beta.1-Setup.exe`: instalador por usuário, atalhos e desinstalador.
- `ForaDeCena-0.5.0-beta.1-Fontes-Saida.zip`: fontes correspondentes do programa GPL e de
  suas dependências PyVirtualCam/libyuv.
- `ForaDeCena-0.5.0-beta.1-Licencas.zip`: avisos, licenças e atribuição dos modelos.
- Arquivos `.sha256`: integridade de cada artefato.

O ZIP com uma pasta de executáveis também é gerado como intermediário local.
O script usa as versões instaladas indicadas nos locks; não promete builds
idênticos bit a bit em outros ambientes.

## Pacote completo de fontes

```powershell
.venv\Scripts\python.exe -B tools/package_release.py
```

Gera `dist/fora-de-cena-0.5.0-beta.1-source.zip` e seu checksum. Inclui código principal,
saída de vídeo, extensão, testes, recursos necessários, dependências declaradas,
receitas e documentação de desenvolvimento. Exclui dados locais, dependências
baixadas, prompts, relatórios e rascunhos internos.

Para preparar uma pasta de revisão local com esses mesmos fontes:

```powershell
.venv\Scripts\python.exe -B tools/prepare_distribution.py
```

Isso não modifica permissões, Git, Releases ou arquivos remotos. Os executáveis
são construídos e publicados separadamente. O histórico da tag binária 0.4.0 é
preservado; para obter todos os fontes atuais use a branch main ou o pacote
completo de fontes oferecido junto da Release.

## Licenças e publicação

O app principal MIT envia BGR24 por pipes locais ao programa independente GPL;
não importa PyVirtualCam. O processo de saída não importa os módulos de visão ou
da interface. O protocolo genérico está em [camera_output/README.md](camera_output/README.md).
Consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) para a análise e condições.

Mantenha os fontes correspondentes e os avisos disponíveis com o mesmo acesso dos
executáveis. Ter fontes do app no Git não dispensa os fontes dos componentes GPL.
Revise arquivos e checksums antes de publicar. Novos builds precisam de seus
próprios testes físicos; aprovação de uma versão anterior não valida uma nova.
Não publique chaves, dados de usuário, ambientes virtuais ou pastas de trabalho.

## Mac e Linux em desenvolvimento

As receitas experimentais, requisitos, testes físicos pendentes e limites de
redistribuição das bibliotecas nativas estão em [MAC_LINUX.md](MAC_LINUX.md).
`tools/build_unix.py` gera candidatos locais, sem publicação. Não promova um
candidato com `distribution_ready: false` como versão final.

## Preparar downloads para revisão — fluxo manual ainda não executado

O workflow `.github/workflows/release-candidates.yml` prepara um **rascunho de
pré-lançamento**, sem publicação automática. Só poderá ser acionado pelo
proprietário, a partir da main, quando os fontes forem aprovados e estiverem
nessa branch. Exige o SHA completo do commit revisado e confirmação explícita.

Em Actions → **Review draft candidates**, o padrão `mac-linux` prepara Mac Apple
Silicon e Linux x64/ARM64. Intel é uma tentativa opcional separada; escolha uma
plataforma ou `all` quando necessário. Os runners recompilam e repetem os testes; somente depois enviam os
arquivos selecionados ao rascunho `v0.5.0-beta.1`. O proprietário pode baixar
esses arquivos autenticado no GitHub. Rascunhos não são downloads públicos.

- Windows: executável portátil e instalador por usuário.
- Mac: DMG com APP, separado por chip, assinatura ad hoc e sem notarização.
- Linux: TAR.GZ com executável e recursos, separado por arquitetura.
- Cada plataforma: fontes correspondentes da saída, licenças e SHA256SUMS.
- Fontes completos da aplicação: um ZIP próprio e seu SHA256SUMS.

Não há armazenamento de artifacts do Actions. Os arquivos vão para Assets de
Releases, cujo [limite é 2 GiB por arquivo](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
Arquivos de plataformas diferentes recebem nomes distintos e nenhum executável
ou checksum existente é substituído. Uma nova compilação diferente exige nova
candidata ou revisão explícita dos assets do rascunho.

O token temporário do workflow recebe `contents: write` **somente neste fluxo
manual** para criar o rascunho e enviar assets. Ele é [restrito ao próprio
repositório](https://docs.github.com/en/actions/concepts/security/github_token),
não é o token pessoal do mantenedor e não é colocado no ambiente dos comandos
de compilação/teste. A execução automática de testes continua somente leitura.

O rascunho mantém `distribution_ready=false`. O fluxo não publica Releases,
não promove candidato a versão estável, não sobrescreve a v0.4.0 nem faz push
na main. Câmera/chamadas reais, licenças do inventário final e a revisão de rede
precisam estar concluídas antes de aprovar uma publicação pública.
