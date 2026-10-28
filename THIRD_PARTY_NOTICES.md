# Licenças e componentes — Fora de Cena 0.4.0

## Dois programas independentes

O aplicativo gráfico, de implementação própria, mantém licença MIT. Ele captura a
webcam, reconhece gestos e compõe os efeitos. Não importa PyVirtualCam e não carrega
seus módulos nativos no próprio processo.

ForaDeCenaVideoOutput é um programa separado, GPL-2.0-only. Recebe vídeo BGR24 padrão
pela entrada do processo e envia ao driver virtual instalado. Não importa o app,
MediaPipe, OpenCV, Tkinter, gestos, máscaras ou estados da reunião. Pode receber
quadros de qualquer produtor de vídeo bruto. Só confirma o quadro após o envio.

Os arquivos são distribuídos juntos por conveniência, com licenças preservadas;
o arquivo único é um contêiner que extrai e inicia programas independentes.
A análise considera também a interface genérica e a ausência de ligação/importação
entre os módulos, não apenas a existência de processos diferentes.

Referência de critérios: https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation
Este registro documenta a análise de engenharia da distribuição; não é certificação jurídica.

## Componentes

| Componente | Licença / condição | Uso |
|---|---|---|
| Aplicativo Fora de Cena | MIT, conforme LICENSE | Interface, captura, gestos e efeitos |
| ForaDeCenaVideoOutput | GPL-2.0-only | Programa independente de saída |
| PyVirtualCam 0.15.0 | GPL-2.0 | Somente no programa de saída |
| libyuv | BSD e avisos/patentes próprios | Incorporado no PyVirtualCam |
| MediaPipe e modelos selecionados | Apache-2.0 | Somente no app principal |
| OpenCV | Apache-2.0 e avisos dos componentes incluídos | Captura DirectShow/MSMF e composição |
| NumPy | BSD e avisos das bibliotecas nativas incluídas | Cálculos nos dois programas |
| CustomTkinter / cv2-enumerate-cameras | MIT | Interface e enumeração |
| Pillow | HPND e avisos próprios | Imagens da interface |
| Python | PSF e avisos próprios | Interpretadores empacotados |

No Windows, o plugin opencv_videoio_ffmpeg não é incluído: a captura usa
explicitamente DirectShow/MSMF. O build Windows recusa sua presença. O processo de saída também exclui
MediaPipe, OpenCV, SSL/OpenSSL e bibliotecas da interface. Textos de licença de
outros pacotes do ambiente podem estar preservados por cautela, sem que seus
binários estejam incluídos.

## Arquivos que devem acompanhar os downloads

- `ForaDeCena-0.4.0-Fontes-Saida.zip`: fonte do programa de saída, receita de build,
  PyVirtualCam v0.15.0 no commit dbac4732168c21f1337e30182957130f678aa058 e o submódulo
  libyuv no commit 19bbedfd3e37329900d34e104021f04d7205ad78, com seus avisos originais.
- `ForaDeCena-0.4.0-Licencas.zip`: avisos coletados, licença GPL completa, termos
  das bibliotecas, atribuição e origem dos modelos.
- `SHA256SUMS.txt`: integridade de todos os artefatos.

Ofereça esses pacotes no mesmo local e com o mesmo acesso dos executáveis. Quem
só quer usar pode baixar apenas instalador ou portátil; não é obrigado a estudar,
compilar ou baixar os fontes. Não distribua o executável negando acesso aos fontes
correspondentes exigidos pela GPL. Os direitos de modificar/redistribuir o componente
GPL são preservados; eles não concedem acesso de escrita ao repositório do mantenedor.

Os fontes de terceiros são sem alterações; a saída de vídeo própria é uma obra
nova e licenciada GPL-2.0-only. Os binários nativos usados vêm da wheel oficial
PyVirtualCam 0.15.0, não foram recompilados; o arquivo de fontes inclui os fontes
correspondentes da versão e os scripts upstream. Não se promete reprodução bit a bit.

## Modelos

São três arquivos oficiais Google MediaPipe, sem alterações, com hashes fixados
no aplicativo. As fichas oficiais de Hand Tracking Lite/Full, BlazeFace Short Range
e Selfie Segmentation declaram Apache License, Version 2.0. O arquivo MODELS.md do
pacote de licenças relaciona URLs e hashes dos modelos e das fichas consultadas.
O texto Apache-2.0 e o NOTICE do MediaPipe estão incluídos nos avisos.

## OBS, inspiração e imagens

OBS Studio é instalado separadamente pelo usuário; não incluímos seu instalador,
registramos drivers nem modificamos sua instalação.

VanishCam (https://github.com/Nicovic17/vanish_webcam) foi referência técnica inicial.
Não distribuímos seu código ou recursos. Os efeitos são procedurais próprios; não
incluímos áudio ou mídia oficial de personagens. As ilustrações e a identidade
visual foram fornecidas pelo mantenedor para uso no aplicativo e na documentação.

## Candidato macOS ARM64 — revisão de distribuição ainda aberta

A implementação própria permanece MIT; isso não determina a licença aplicável à
combinação de dependências do executável. A wheel oficial OpenCV 4.14.0.94 do candidato anterior
usa Cocoa/AVFoundation e inclui FFmpeg, x264/x265 e outras bibliotecas nativas.
O próprio libavcodec declara GPL version 3 or later, com --enable-gpl e
--enable-version3. O aviso LGPL genérico da wheel não cobre sozinho esta build.
Precisam ser revisados os fontes correspondentes, receitas/patches e obrigações
de redistribuição da combinação. Não inferir conformidade só pela coleta de avisos.
O auxiliar GPL-2.0-only permanece separado e não inclui essas bibliotecas.

O ambiente de build local usou Tcl/Tk 9.1.0 e libtommath 1.3.0 em cópias locais
no ambiente virtual; seus avisos correspondentes acompanham o candidato.
Não houve recompilação nem alteração do MediaPipe. Sua declaração de métricas
permanece uma pendência de verificação de rede; não prometemos ausência de telemetria.

### Origem dos binários conferida em 27/10/2026

A wheel oficial `opencv_contrib_python-4.14.0.94-cp37-abi3-macosx_13_0_arm64.whl`
foi obtida pela URL do PyPI e conferida por tamanho e SHA-256. As 93 dylibs
coincidem, por hash, com o inventário recebido do Mac. Portanto a origem oficial
não elimina a pendência de GPLv3 descrita acima; o binário efetivo precisa de revisão.

Uma alternativa técnica em avaliação é compilar a mesma versão do OpenCV sem
FFmpeg/GStreamer/HighGUI, preservando captura AVFoundation ou V4L2 e o suporte
JPEG/MJPEG necessário às webcams. Essa variante ainda precisa ser compilada e
validada nativamente, com inventário e avisos próprios. Não removemos bibliotecas
da wheel atual e não alteramos automaticamente a licença dos nossos fontes.

Fontes oficiais: [configuração OpenCV](https://docs.opencv.org/4.x/db/d05/tutorial_config_reference.html),
[compilação das wheels](https://github.com/opencv/opencv-python) e
[licenças do FFmpeg 7.1.1](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/LICENSE.md).


## Candidato OpenCV próprio — macOS ARM64, 27/10/2026

O candidato enxuto usa opencv-contrib-python 4.14.0.94 compilado do sdist oficial
SHA256 f2e58020b9f54d68b49553a161327ae1bbc47da68e147231d444c915ee4cab4c.
A proveniência identifica o artefato próprio; não confundir com a wheel oficial
acima. O perfil e patch ficam em packaging/opencv-minimal-*; instruções em
OPENCV_ENXUTO_MAC.md. Sem FFmpeg/GStreamer/HighGUI/Qt/GTK. AVFoundation e JPEG
continuam habilitados. O linker incorpora codecs/HALs permissivos com seus avisos
em packaging/notices/opencv-minimal, reproduzidos no aplicativo e pacote de licenças.
This software is based in part on the work of the Independent JPEG Group.

A revisão e a retirada dessas dependências do OpenCV não encerram as obrigações
das outras bibliotecas ou do auxiliar GPL independente. distribution_ready=false;
testes físicos do novo candidato e verificação de rede do MediaPipe pendentes.

## Tentativa experimental MediaPipe para Mac Intel

A receita local usa o código C API do MediaPipe 1.1.1, commit `50505c8312c7eacb1bd411cecdc4cc9fd08d53cb`, e preserva os arquivos Python, LICENSE e demais avisos da wheel oficial da mesma versão. A biblioteca nativa é compilada para x86_64 e a wheel modificada recebe a build tag `1fdcintel`; não é uma wheel Intel oficial do fornecedor. O perfil e a proveniência identificam os insumos e hashes. A compilação Intel está sendo tentada no CI, ainda sem aprovação de todos os testes; a revisão completa das dependências C/C++ e fontes correspondentes permanece pendente. Nenhum pacote foi autorizado para distribuição por esta receita. Consulte [MAC_INTEL.md](MAC_INTEL.md).
