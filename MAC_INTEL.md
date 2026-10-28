# Mac Intel — receita experimental, sem download liberado

O aplicativo tem uma tentativa de compilação para macOS Intel x86_64, mantendo
Python 3.14, MediaPipe 1.1.1 e as versões atuais do aplicativo. **A compilação
está sendo tentada no runner Intel; ainda não foi concluída com todos os testes.
Não é suporte confirmado.** O acompanhamento fica em [MULTIPLATAFORMA.md](MULTIPLATAFORMA.md).
Nenhum pacote Intel foi publicado. `distribution_ready=false` permanece.

Para inspecionar os insumos no Windows, sem baixar ou compilar, execute
`python tools/build_mediapipe_intel.py --plan`.

## Por que há uma compilação específica

O PyPI oficial não disponibiliza wheel Intel do MediaPipe 1.1.1. A versão
0.10.21 possui wheel Intel, mas exige uma pilha diferente, incluindo NumPy <2.
Essa versão antiga não é selecionada automaticamente.

A receita usa o código C API da tag oficial `v1.1.1`, conferindo o commit
`50505c8312c7eacb1bd411cecdc4cc9fd08d53cb`. Compila diretamente o target
`//mediapipe/tasks/c:mediapipe_source` com Bazel 7.7.0, CPU Intel e execução
de modelos em CPU. Assim evita o `setup.py`, que fixa ARM no Mac, e o target
que pode escolher uma biblioteca ARM pré-compilada.

Um patch pequeno e identificado por SHA-256 configura o OpenCV privado da C API
como estático, com processamento de imagens em memória e codecs externos/GUI
desligados. O OpenCV Python usado pelo app para câmera e JPEG permanece separado.
Isso evita depender da lista de bibliotecas Linux do build estático original
no Mac. A compatibilidade desse perfil C/C++ também precisa do primeiro build
Intel; o patch não substitui os testes de inferência ou a revisão de licenças.

Os arquivos Python e avisos da wheel oficial da mesma versão são preservados.
A biblioteca ARM é substituída por uma **nova biblioteca compilada e auditada
para Intel**. A wheel recebe build tag `1fdcintel`, plataforma x86_64 e um novo
inventário `RECORD`. Renomear uma wheel ARM não oferece suporte Intel: a receita
recusa bibliotecas sem a arquitetura exigida ou membros nativos inesperados.

Fontes, Bazel, template Python e wheel produzida têm identificação por commit
ou SHA-256 no perfil/proveniência. A proveniência é conferida novamente contra
a wheel instalada antes de empacotar o aplicativo. Essa conferência identifica
os insumos; não substitui a revisão das dependências transitivas compiladas.

## Executar na branch de testes do GitHub

Pushes autorizados na branch `testing/mac-linux` disparam a tentativa Intel. A compilação pode demorar e consumir bastante memória/disco do runner gratuito. Quando o workflow também estiver na branch padrão, a execução manual terá a opção `build_macos_intel`, desligada por padrão.

Acompanhe o job Intel: compilação C API → instalação da wheel explícita e
   lock → testes Python/JS → inferência sintética → DMG → autoteste do executável.

Há limite de 120 minutos no job e 90 minutos na etapa de compilação C++.
Se houver incompatibilidade de toolchain, dependência, espaço ou API, o job
deve falhar; o erro precisa ser corrigido antes de anunciar um candidato.
A opção normal de teste só confirma que a wheel oficial Intel está ausente.
Um job de sondagem verde, com aviso BLOCKED, não certifica funcionamento.

Usa o runner padrão `macos-15-intel` de repositório público. Não guarda artifacts,
não cria Releases e não altera cobrança, drivers ou configurações do computador.
O DMG experimental é descartado junto com a máquina; a disponibilização para
testadores exige uma etapa de publicação separada, após revisão e autorização.

## Compilar manualmente em Mac Intel

Use Python 3.14 x86_64 com Tk e ferramentas de linha de comando do Xcode já
instaladas. Esta é uma receita de desenvolvimento; quem receber um aplicativo
final não precisará compilar MediaPipe, instalar Python ou Bazel.

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install --only-binary=:all: packaging==26.3 macholib==1.16.4 altgraph==0.17.5
python tools/build_mediapipe_intel.py
python -m pip install --only-binary=:all: work/mediapipe-intel/wheels/*.whl -r requirements.lock.txt -r requirements-build.txt
python -m pip check
python setup_models.py
python -m unittest discover -s tests -q
node --test tests/meet_extension.test.mjs
python main.py --self-test --report work/intel-source-self-test.json
python tools/fetch_distribution_sources.py
python tools/build_unix.py --mediapipe-wheel work/mediapipe-intel/wheels/mediapipe-1.1.1-1fdcintel-py3-none-macosx_15_0_x86_64.whl --mediapipe-provenance work/mediapipe-intel/provenance.json
```

O build recusa diretório de trabalho anterior, para evitar reutilizar binários
de outra tentativa. Preserve relatórios antes de preparar uma pasta de trabalho
nova; nenhum script remove recursivamente os seus dados para tentar de novo.
Se faltar a licença da distribuição Python, use `--python-license` conforme
[MAC_LINUX.md](MAC_LINUX.md). O comando de CI fixa Python 3.14.7 e confere a
licença correspondente; o build manual aceita a série 3.14 do desenvolvedor.

## O que ainda falta

- Compilação nativa efetiva e todos os autotestes no runner Intel. Os testes
  Windows verificam lógica, formato da wheel e barreiras de empacotamento;
  não executam uma biblioteca Intel de macOS.
- Revisão de licenças, fontes correspondentes e dependências nativas do build
  de MediaPipe e do bundle completo. OpenCV Intel usa a wheel oficial nesta
  primeira tentativa e pode incluir FFmpeg/Qt: não é o perfil enxuto ARM64.
- Verificação de rede das dependências, especialmente MediaPipe, permanece
  pendente. Usar modelos locais não comprova ausência de telemetria.
- Testes reais em um Mac Intel: prévia, câmera interna/USB, gestos, efeitos,
  restauração, captura do fundo, desempenho, permissão de câmera, OBS Virtual
  Camera e uma chamada confirmada por outro participante.

O mínimo inicial do perfil é macOS 15. O mínimo efetivo de todas as bibliotecas
é auditado e registrado no candidato; não anunciar macOS antigo nem pacote
universal2. Apple Silicon e Intel permanecem pacotes separados. Não há assinatura
Developer ID ou notarização; mantém-se a orientação de autorização individual
do macOS, sem desativar Gatekeeper.

## Referências técnicas

- [MediaPipe 1.1.1: target C API](https://github.com/google-ai-edge/mediapipe/blob/50505c8312c7eacb1bd411cecdc4cc9fd08d53cb/mediapipe/tasks/c/BUILD)
- [MediaPipe 1.1.1: configurações de CPU Mac](https://github.com/google-ai-edge/mediapipe/blob/50505c8312c7eacb1bd411cecdc4cc9fd08d53cb/.bazelrc)
- [PyPI: arquivos oficiais de MediaPipe 1.1.1](https://pypi.org/project/mediapipe/1.1.1/#files)
- [Bazel: biblioteca compartilhada](https://bazel.build/reference/be/c-cpp#cc_binary.linkshared)
- [PyInstaller: arquiteturas macOS](https://pyinstaller.org/en/stable/feature-notes.html#macos-multi-arch-support)

A documentação Google de wheels descreve principalmente pipelines manylinux.
Esta receita Intel é uma adaptação experimental do Fora de Cena; não é uma
receita Mac Intel homologada pelo fornecedor.
