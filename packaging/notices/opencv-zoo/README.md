# Modelos OpenCV Zoo — perfil Mac Intel

Origem oficial fixada: https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models

Os pesos ONNX são redistribuídos sem alteração. URLs e SHA-256 estão em
`teleport_cam/opencv_models.py`. O aplicativo não baixa pesos em execução.

- `palm_detection_mediapipe`: Apache-2.0; texto upstream em `APACHE-2.0.txt`.
- `handpose_estimation_mediapipe`: Apache-2.0; `HAND-LICENSE.txt` preserva o texto upstream.
- `human_segmentation_pphumanseg`: Apache-2.0, Copyright (c) 2021 PaddlePaddle Authors;
  texto e declaração upstream em `PERSON-LICENSE.txt`.
- `face_detection_yunet`: MIT, Copyright (c) 2020 Shiqi Yu;
  texto e declaração upstream em `YUNET-MIT.txt`.

As convenções de entrada, âncoras e transformação da região da mão foram
consultadas nos exemplos oficiais `mp_palmdet.py`, `mp_handpose.py`,
`pphumanseg.py` e `yunet.py` desse commit. O adaptador em `vision_opencv.py`
é uma implementação própria: gera as âncoras, faz NMS em x/y/largura/altura,
usa uma transformação afim com preenchimento e devolve os pontos no quadro original.
Não redistribuímos os exemplos Python completos nem alteramos a licença dos modelos.

O OpenCV Intel acrescenta DNN e objdetect ao perfil mínimo; compila o Protobuf
incluído no sdist oficial, sem regenerar os arquivos .proto nem buscar Protobuf
no sistema. `PROTOBUF.txt` preserva a licença BSD upstream. O texto geral
`opencv-minimal/README.md` descreve o perfil ARM/Linux anterior: Intel não inclui
KleidiCV/Carotene ARM nem IPP; o inventário nativo do candidato define o link efetivo.
