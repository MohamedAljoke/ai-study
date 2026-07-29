# Teste1

Só as linhas com `>` viram narração. Todo o resto é anotação minha, a máquina ignora.
Os marcadores valem a partir da primeira palavra do parágrafo seguinte.

    <!-- cena: terminal id=play-demo nota="uma partida curta jogada na mão" -->
    <!-- cena: codigo id=parse-position arquivo=projects/battleships/internal/game/position.go linhas=12-28 -->
    <!-- cena: manim id=density-mapa classe=HeatMap dados=build/density.json turnos=1-12 -->
    <!-- cena: card id=fechamento titulo="Cinco coisas" -->
    <!-- cena: tela id=web-demo nota="site e terminal lado a lado" -->
    <!-- short: inicio id=uma-linha titulo="Uma linha, 15 tiros a menos" -->
    <!-- short: fim id=uma-linha -->

`id` é kebab-case e único no vídeo — ele vira o nome do arquivo que eu largo em
`assets/<id>.<ext>` depois de produzir a cena. `arquivo=` é relativo à raiz do repositório;
`dados=` e `nota=` são recado meu e saem na folha de pedidos como estão.

Apagar tudo daqui pra cima antes de gravar.

## O gancho

<!-- cena: tela id=abertura -->

> Primeira frase. Ela precisa se sustentar sozinha nos primeiros dez segundos.
teste de script
## O problema

> Texto que eu leio em voz alta, do jeito que eu falo.

## A solução

> Continua.

## O fecho

> Última frase.
