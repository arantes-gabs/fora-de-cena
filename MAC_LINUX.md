# Mac e Linux — candidatos experimentais

Esta adaptação está em desenvolvimento. Os downloads Windows existentes não mudaram. Os candidatos Mac/Linux só poderão ser anunciados como estáveis após build nativo, revisão das bibliotecas incluídas e teste de webcam/chamada real. Um teste no Windows com plataformas simuladas não certifica suporte nativo.

## Alvos iniciais

| Sistema | Pacote preparado pelo build | Requisitos/meta |
| --- | --- | --- |
| Mac Apple Silicon, M1 em diante | `.dmg` contendo `Fora de Cena.app` | perfil OpenCV mínimo macOS 15; mínimo efetivo auditado no bundle; OBS 30+ para câmera virtual |
| Linux x86_64 | `.tar.gz` com executável e recursos | Base de build Ubuntu 22.04/glibc 2.35; ambiente gráfico e v4l2loopback |
| Linux ARM64 | Receita de build disponível | Experimental, sem teste físico confirmado |
| Mac Intel | Receita experimental; compilação nativa pendente | MediaPipe 1.1.1 compilado a partir dos fontes; perfil macOS 15+, sem download liberado; veja [MAC_INTEL.md](MAC_INTEL.md) |

Não há AppImage nesta primeira receita. O `.tar.gz` preserva os links e permissões exigidos pelo PyInstaller, sem adicionar uma dependência de FUSE. Não separe o executável da pasta de recursos.

## Para usar um candidato já compilado

### Mac

1. Baixe o pacote correto para Apple Silicon e confira seu SHA-256.
2. Abra o `.dmg` e arraste `Fora de Cena.app` para Aplicativos.
3. Não há assinatura Developer ID nem notarização paga. O macOS pode bloquear a primeira abertura. Quando disponível, a autorização individual fica em Ajustes do Sistema → Privacidade e Segurança → Abrir Mesmo Assim. Máquinas gerenciadas podem proibir a abertura. Não desative Gatekeeper e não remova a quarentena por comandos indiscriminados.
4. Ao iniciar a câmera, autorize seu uso. Se negar, libere Fora de Cena nos ajustes de privacidade e reinicie o aplicativo.
5. Para transmitir: instale OBS 30+ pelo site oficial, abra-o, inicie e pare sua câmera virtual uma vez e feche o OBS. No macOS 15+, autorize OBS Virtual Camera em Ajustes do Sistema → Geral → Itens de Início e Extensões → Extensões de Câmera. Enquanto aguarda autorização, ela não aparece no Meet. Depois feche e reabra o navegador. Não mantenha a câmera virtual do OBS iniciada enquanto o Fora de Cena a utiliza.
6. No Fora de Cena, prepare o fundo, escolha OBS Virtual Camera e inicie. No Meet/gravador, selecione OBS Virtual Camera.

Não é necessário instalar Python para usar o pacote compilado. Alguns teclados exigem Fn+F8; o atalho é local no Mac/Linux. O botão Restaurar permanece disponível.

### Linux

1. Extraia o `.tar.gz` preservando permissões e links em uma pasta do seu usuário.
2. Abra o executável `ForaDeCena` dentro da pasta extraída, ou execute `./ForaDeCena` no terminal dessa pasta. Não rode com sudo.
3. Para só visualizar, escolha Só prévia. Para transmitir, o sistema precisa disponibilizar uma câmera v4l2loopback.
4. Em Ubuntu, o administrador pode instalar o pacote oficial `v4l2loopback-dkms` e os headers correspondentes ao kernel. A preparação é do sistema, não uma ação automática do aplicativo. Consulte a documentação da distribuição se Secure Boot exigir assinatura do módulo; não desative Secure Boot.
5. O administrador pode carregar um dispositivo livre, por exemplo `sudo modprobe v4l2loopback devices=1 exclusive_caps=1 card_label="Fora de Cena"`. Se o módulo já estiver carregado/usado, não descarregue automaticamente: confira a configuração existente. Não use chmod 777 nos dispositivos.
6. Em Configurar → Meet, escolha Câmera virtual Linux e, se necessário, o dispositivo `/dev/videoN` de saída. Use uma webcam física como entrada. Inicie o vídeo aqui antes de selecioná-lo no Meet: com exclusive_caps, a câmera pode aparecer no navegador só depois do envio começar.

Driver indisponível/permissão negada não deve travar a prévia. Reinício e atualização do kernel podem exigir nova verificação do módulo. Navegadores Snap/Flatpak e X11/Wayland precisam de testes separados. OBS sozinho não instala necessariamente esse driver.

## Compilar a partir dos fontes

Etapas de desenvolvimento; não são exigidas de quem recebe o pacote pronto. Execute no sistema e chip de destino. Não existe compilação Windows → Mac/Linux nesta receita.

Use Python 3.14 com suporte Tk. Em Linux, instale pelo gerenciador da distribuição as bibliotecas necessárias, como PortAudio, libGL, libEGL, libGLES e GLib, quando ausentes. A biblioteca nativa MediaPipe exige EGL/GLES mesmo quando a inferência usa CPU. Esses requisitos precisam ser conferidos no inventário do candidato. No Mac, use uma distribuição Python confiável com Tk; não substitua o Python do sistema.

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install --only-binary=:all: -r requirements.lock.txt -r requirements-build.txt
python -m pip check
python setup_models.py
python tools/fetch_distribution_sources.py
python -m unittest discover -s tests -q
node --test tests/meet_extension.test.mjs
python main.py --self-test --report work/source-self-test.json
python tools/build_unix.py
```

**Pacote Linux da candidata 0.5.0-beta.1:** use o workflow para reproduzir o
empacotamento completo. Ele compila OpenCV e NumPy enxutos antes de instalar
os locks e valida os hashes dos artefatos selecionados. O comando de build
Linux recusa o NumPy oficial neste perfil de distribuição; executar o app
diretamente dos fontes continua usando o lock normal. A receita NumPy roda
somente no runner limpo, sem aproveitar configurações do computador pessoal.

O lock usa marcadores para dependências específicas de Mac/Windows. Instalar com `--only-binary` interrompe quando faltar um pacote compatível; não compila uma versão desconhecida silenciosamente. As dependências transitivas ainda precisam de validação nativa.

Se a distribuição Python não incluir `LICENSE.txt` no local esperado, informe a licença correspondente com `--python-license /caminho/para/licenca-do-python`. Não selecione arquivos pessoais. O build falha se os modelos, fontes fixados ou avisos exigidos estiverem ausentes.

O Linux exige build em glibc 2.35 para manter a base proposta. Uma base mais nova é recusada, em vez de gerar um pacote anunciado erroneamente como compatível com Ubuntu 22.04. Alpine/musl e 32 bits não são alvos desta receita.

Para consultar o plano sem compilar:

```sh
python tools/build_unix.py --plan macos-arm64
python tools/build_unix.py --plan linux-x86_64
python tools/check_platform_wheels.py macos-arm64 --report work/macos-wheels.json
python tools/check_platform_wheels.py linux-x86_64 --report work/linux-wheels.json
```

O verificador de dependências consulta apenas metadados públicos oficiais do PyPI,
confere pacotes binários compatíveis e o fechamento das versões fixadas. Não
instala/executa esses pacotes e não substitui teste nativo.

Saídas ficam em uma subpasta nova de `dist/native/`, incluindo o pacote, hashes, avisos/fontes do auxiliar, inventário de bibliotecas e `candidate.json`. Logs e relatórios detalhados ficam em `work/native/`, ignorado no Git. O arquivo de inventário usa caminhos relativos. O tar não inclui nome/ID do usuário que compilou.

## Segurança e limitações de publicação

- Nenhum script faz commit, push, release, instalação de driver ou mudança de segurança do sistema.
- O Mac usa assinatura ad hoc gerada pelo empacotador, sem certificado pessoal ou Apple Developer pago. Verificar a assinatura no Mac não equivale a notarização nem certificação de segurança pela Apple.
- Preferências e pareamento do pacote ficam em `~/Library/Application Support/ForaDeCena` no Mac e `$XDG_DATA_HOME/fora-de-cena` no Linux, com padrão `~/.local/share/fora-de-cena`. A chave é criada com modo 0600 em Unix. Fontes preservam a pasta de desenvolvimento existente; não compartilhe seus arquivos de sessão.
- O auxiliar de câmera virtual continua separado do processo principal; a chave Meet não é enviada pelo protocolo de quadros.
- PyInstaller Unix usa links simbólicos. O build aceita links internos exigidos pelo pacote e rejeita links externos, chaves privadas, credenciais e estado de sessão nos destinos previstos.
- OpenCV Unix pode trazer FFmpeg/Qt e outras bibliotecas com condições próprias de redistribuição. Não removemos bibliotecas ligadas diretamente ao OpenCV: isso pode quebrar a captura. A revisão de licenças e fontes dessas bibliotecas é uma etapa obrigatória antes de publicação; coletar avisos sozinho não encerra essa revisão.
- O aviso do fornecedor MediaPipe menciona métricas de desempenho/uso, embora o processamento de imagens seja no dispositivo. O comportamento de rede da dependência precisa de verificação própria. O autoteste não afirma ter capturado tráfego nem prova ausência de telemetria.
- `distribution_ready` permanece falso nos candidatos nativos. Isso é intencional até concluir as etapas pendentes.

## Testes antes de liberar

Automático: instalação limpa e pip check, suíte Python/JS, hashes dos modelos, inferência sintética, auxiliar independente, fidelidade dos quadros, fechamento/recuperação e autoteste do executável sem Python externo.

Manual: baixar em outro perfil sem Python, permissões de câmera negadas/concedidas, webcam interna/USB, calibração, todos os gestos/efeitos, Restaurar, desconexão, suspender/retomar, sessão de 20 minutos em 480p/720p e chamada com segundo participante confirmando o vídeo recebido. Testar OBS gravando e Meet no navegador escolhido. A saída automática exige vínculo explícito e não deve agir quando desligada.

O M1 disponível permite iniciar o teste Mac. Linux e Intel precisam de testador real. Não certificar todos os macOS por um único macOS testado.

## Automação gratuita no GitHub

Na branch pública `testing/mac-linux`, cada push autorizado executa testes e tentativas de compilação nos runners nativos. O workflow também prevê execução manual quando estiver disponível na branch padrão do GitHub:

- **Opção de build desligada (padrão):** verifica dependências, instala o lock, executa testes Python/JavaScript e diagnóstico sem câmera nos runners Windows x64, Mac Apple Silicon, Linux x86_64 e Linux ARM64.
- **Opção de build ligada:** também compila candidatos e executa seus autotestes nativos. Mac ARM64 e Linux recompilam OpenCV enxuto em ambiente separado; Linux também compila NumPy sem BLAS externo. As proveniências são verificadas antes do empacotamento. Pode levar bem mais tempo que os testes.
- **Mac Intel:** o job padrão sonda compatibilidade e sinaliza **BLOCKED** pela ausência de wheel oficial. A opção independente **build_macos_intel**, desligada por padrão, tenta compilar o MediaPipe 1.1.1 para x86_64, instalar a wheel própria, executar testes/inferência e gerar um DMG com autoteste. A receita ainda não foi executada em um Mac Intel; não é suporte confirmado. Veja [MAC_INTEL.md](MAC_INTEL.md).

Só usa runners padrão gratuitos de repositórios públicos. A execução é recusada se o repositório estiver privado ou fora de `main`/`testing/mac-linux`. Push só dispara na branch de testes; não roda em PR, push na main ou agendamento. Quem apenas visita o repositório não ganha permissão para disparar workflows nele.

Não usa certificados pessoais, secrets, runners pagos ou permissões de escrita. Actions estão fixadas por SHA. Não altera drivers, configurações de segurança ou cobrança da conta. Linux instala bibliotecas de sistema apenas na máquina descartável do GitHub.

**Não armazena artifacts e não publica Releases:** os pacotes de teste são descartados com o runner, evitando consumo de armazenamento de artifacts do Actions. Veja resultados em cada job e no resumo da execução. Downloads para usuários continuam nas Releases já publicadas; os novos candidatos só poderão ser disponibilizados após as verificações pendentes e aprovação do proprietário. `distribution_ready=false` permanece em todos os candidatos.

O MediaPipe 1.1.1 oficial não oferece wheel Mac Intel. O `setup.py` da tag oficial fixa `darwin_arm64` no build Mac; a tentativa Intel compila o target C API diretamente e exige biblioteca x86_64, preservando as versões do aplicativo. Não basta trocar o nome de uma wheel ARM. Referência: [código oficial da versão 1.1.1](https://github.com/google-ai-edge/mediapipe/blob/50505c8312c7eacb1bd411cecdc4cc9fd08d53cb/setup.py).

## Documentação oficial

- [PyVirtualCam: plataformas e configuração](https://github.com/letmaik/pyvirtualcam#supported-virtual-cameras)
- [OBS: autorização e solução de problemas da câmera virtual](https://obsproject.com/kb/virtual-camera-troubleshooting)
- [v4l2loopback: preparação e exclusive_caps](https://github.com/v4l2loopback/v4l2loopback)
- [PyInstaller: bundles Mac](https://pyinstaller.org/en/stable/spec-files.html#spec-file-options-for-a-macos-bundle)
- [PyInstaller: links simbólicos e processos externos](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html)
- [PyInstaller: compatibilidade glibc](https://pyinstaller.org/en/stable/usage.html#making-gnu-linux-apps-forward-compatible)
- [Apple: abrir aplicativos baixados](https://support.apple.com/pt-br/102445)
- [XDG: diretórios por usuário](https://specifications.freedesktop.org/basedir/latest/)
- [GitHub: runners e arquiteturas](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)

## Primeiro build Apple Silicon (27/10/2026)

O ambiente nativo disponível é ARM64 com macOS 15.5. O Python 3.14.10 Homebrew
inclui um Mach-O com mínimo macOS 15.0; o MediaPipe 1.1.1 instalado declara 14.0.
Portanto este candidato não comprova nem anuncia funcionamento no macOS 13/14.
A receita calcula LSMinimumSystemVersion pelas bibliotecas e audita o bundle.
Consulte o mínimo efetivo em candidate.json e macos-bundle-audit.json.

A wheel macOS ARM64 de opencv-contrib-python 4.14.0.94 inclui um FFmpeg cuja
avcodec_license() retorna GPL version 3 or later e cuja configuração contém
--enable-gpl, --enable-version3, --enable-libx264 e --enable-libx265. O aviso
LGPL genérico da wheel não é suficiente para essa compilação. A revisão deve
abranger os fontes correspondentes e as obrigações da combinação distribuída,
além das demais bibliotecas nativas. Não remover dylibs ligadas diretamente.
O auxiliar independente GPL-2.0-only deve continuar sem essas dependências.


O candidato OpenCV próprio de 27/10/2026 tem receita, proveniência e roteiro de
reteste em [OPENCV_ENXUTO_MAC.md](OPENCV_ENXUTO_MAC.md). O mínimo real permanece
macOS15 Apple Silicon; não anunciar suporte macOS13/14 apenas pelo perfil OpenCV.
