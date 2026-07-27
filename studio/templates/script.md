# {{TITULO}}

Só as linhas com `>` viram narração. Todo o resto é anotação minha, a máquina ignora.
Os marcadores valem a partir da primeira palavra do parágrafo seguinte.

    <!-- cena: terminal id=play-demo fonte=tapes/play.tape -->
    <!-- cena: codigo id=parse-position arquivo=battleships/internal/game/position.go linhas=12-28 -->
    <!-- cena: manim id=density-mapa classe=HeatMap dados=build/density.json turnos=1-12 -->
    <!-- cena: card id=fechamento titulo="Cinco coisas" -->
    <!-- cena: tela id=web-demo nota="gravação minha" -->
    <!-- short: inicio id=uma-linha titulo="Uma linha, 15 tiros a menos" -->
    <!-- short: fim id=uma-linha -->

`fonte=` e `dados=` são relativos à pasta do vídeo; `arquivo=` é relativo à raiz do repositório.
`id` é kebab-case e único no vídeo — ele vira nome de arquivo.

Apagar tudo daqui pra cima antes de gravar.

## O gancho

<!-- cena: tela id=abertura -->

> Primeira frase. Ela precisa se sustentar sozinha nos primeiros dez segundos.

## O problema

> Texto que eu leio em voz alta, do jeito que eu falo.

## A solução

> Continua.

## O fecho

> Última frase.
