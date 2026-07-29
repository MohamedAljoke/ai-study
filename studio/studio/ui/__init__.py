"""A interface local do pipeline. Ver docs/sprint-06-ui.md.

`studio/ui/` é **casca**, na mesma categoria de `comandos/`: pode chamar comando, mas não
decide nada de pipeline. Em que passo o vídeo está é `comandos/status.etapas`; quem fornece
cada cena é `comandos/pedidos.levantar`. Se a página souber responder isso sozinha, ela vai
discordar do terminal — o único jeito deste sprint dar errado.
"""
