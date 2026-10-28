# OpenCV próprio: revisão Mac ARM64 e receita Linux

Este software é baseado em parte no trabalho do Independent JPEG Group.
This software is based in part on the work of the Independent JPEG Group.

OpenCV 4.14.0.94, compilação própria experimental. Os avisos genéricos do sdist
foram preservados; suas referências a FFmpeg/Qt não significam que estejam ativos.
A evidência do linker, inventário Mach-O e registro de backends identifica este build.

Bibliotecas estáticas do link real: OpenCV core/imgproc/imgcodecs/videoio,
libjpeg-turbo 3.1.2 (IJG/BSD/zlib), libpng 1.6.57 (libpng), zlib (zlib),
Carotene/tegra_hal (BSD-3-Clause) e KleidiCV 26.03 (Apache-2.0).
OpenCV incorpora ainda SoftFloat (BSD-3-Clause); inclui-se também aviso Flatbuffers
(Apache-2.0). Os frameworks dinâmicos restantes do OpenCV pertencem ao macOS.
FFmpeg, GStreamer, HighGUI, Qt, GTK, AVIF, WebP, TIFF, OpenEXR, OpenJPEG,
Jasper, JPEGXL, ITT, OpenCL e LAPACK foram desativados na receita.
Não foram apagadas bibliotecas de uma wheel oficial pronta.

As condições destes componentes permitem redistribuição binária com seus avisos,
atribuições e textos de licença; não exigem um pacote de fontes correspondentes
para este recorte permissivo. Mantêm-se a fonte oficial identificada por hash,
o patch de alterações e a receita de compilação. Apache-2.0: alterações documentadas
em opencv-minimal-source.patch (tipagem para módulos opcionais e privacidade dos
caminhos de build); sem alterações nos codecs/HALs. Não usar nomes de contribuidores
como endosso. Preservar todos estes avisos em cada distribuição.

Esta revisão é do recorte OpenCV; não encerra a revisão do aplicativo completo.
O auxiliar independente PyVirtualCam permanece GPL-2.0-only e acompanha fontes
correspondentes em artefato separado. MediaPipe/rede, demais bibliotecas e testes
físicos deste candidato continuam pendentes. distribution_ready=false.

Extensão Linux da candidata 0.5.0-beta.1: mesmos fontes verificados, codecs
JPEG/PNG/zlib estáticos e V4L2. KleidiCV e IPP são desligados nesse perfil;
Carotene pode ser usado no ARM64, com o aviso BSD já preservado. A compilação,
o inventário e os autotestes precisam confirmar essa seleção antes de liberação.
