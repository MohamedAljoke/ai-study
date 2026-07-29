// A página. Ela não decide nada: pede o estado ao servidor e desenha o que voltou.
// Toda regra ("qual é o próximo passo", "essa cena falta?") já veio pronta do Python.

const $ = (id) => document.getElementById(id);
const criar = (tag, classe, texto) => {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
};

let video = null;   // o número do vídeo aberto
let dados = null;   // o último estado que o servidor mandou
let rodando = false;

// --- conversa com o servidor ---

async function pedir(rota, opcoes) {
  const resposta = await fetch(rota, opcoes);
  const corpo = await resposta.json();
  if (!resposta.ok) throw new Error(corpo.erro || `falhou: ${rota}`);
  return corpo;
}

async function enviarArquivo(rota, arquivo) {
  const corpo = new FormData();
  corpo.append("arquivo", arquivo);
  return pedir(rota, { method: "POST", body: corpo });
}

async function recarregar() {
  dados = await pedir(`/api/videos/${video}`);
  desenhar();
}

// --- cabeçalho ---

function desenharEtapas() {
  const lista = $("etapas");
  lista.replaceChildren();
  for (const etapa of dados.etapas) {
    const li = criar("li", `${etapa.estado} ${etapa.proxima ? "proxima" : ""}`);
    li.append(criar("span", "rotulo", etapa.rotulo), criar("span", "estado", etapa.estado));
    if (etapa.detalhe) li.append(criar("span", "detalhe", etapa.detalhe));
    lista.append(li);
  }
  $("proximo").replaceChildren("próximo: ", criar("b", null, dados.proximo));
}

// --- roteiro ---

function desenharRoteiro() {
  const script = dados.script;
  if ($("script").value !== script.texto && document.activeElement !== $("script")) {
    $("script").value = script.texto;
  }
  $("erro-roteiro").hidden = !script.erro;
  $("erro-roteiro").textContent = script.erro;

  const p = script.previa;
  $("previa-numeros").textContent = p
    ? `${p.palavras} palavras · ~${p.duracao} de leitura`
    : "";
  $("previa-narracao").textContent = p ? p.narracao : "";

  const linhas = (alvo, itens, formatar) => {
    $(alvo).replaceChildren(...itens.map((item) => {
      const li = criar("li");
      formatar(li, item);
      return li;
    }));
  };
  linhas("previa-cenas", p ? p.cenas : [], (li, c) =>
    li.append(criar("code", null, c.id), ` ${c.tipo} · linha ${c.linha}`));
  linhas("previa-shorts", p ? p.shorts : [], (li, s) =>
    li.append(criar("code", null, s.id), ` ${s.titulo}`));
  linhas("previa-avisos", p ? p.avisos : [], (li, a) =>
    li.textContent = `⚠ linha ${a.linha}: ${a.texto}`);
}

async function salvarScript() {
  try {
    dados.script = await pedir(`/api/videos/${video}/script`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ texto: $("script").value, assinatura: dados.script.assinatura }),
    });
    $("salvo").textContent = "salvo";
    setTimeout(() => ($("salvo").textContent = ""), 2000);
    await recarregar();
  } catch (erro) {
    $("erro-roteiro").hidden = false;
    $("erro-roteiro").textContent = erro.message;
  }
}

// --- áudio ---

function desenharAudio() {
  const midia = dados.midia;
  const tocador = $("tocador-audio");
  tocador.hidden = !midia.audio;
  if (midia.audio) tocador.src = `${midia.audio}?v=${Date.now()}`;
  $("estado-audio").textContent = !midia.audio
    ? "nenhum áudio ainda — dá pra usar o dublê pra testar o pipeline sem gravar"
    : midia.duble
      ? "⚠ rodando com dublê: voz sintética, não publicável"
      : "narration.wav no lugar";
}

// --- cenas ---

function previaDoAsset(cena) {
  const imagem = /\.(png|jpe?g|gif)$/i.test(cena.arquivo);
  const e = criar(imagem ? "img" : "video", "previa-asset");
  e.src = cena.midia;
  if (!imagem) { e.muted = true; e.preload = "metadata"; }
  return e;
}

function cartaoDaCena(cena) {
  const cartao = criar("div", `cena ${cena.falta ? "falta" : "pronta"}`);

  const cabeca = criar("div", "cabeca-cena");
  cabeca.append(
    criar("span", "id", cena.id),
    criar("span", "tipo", cena.tipo),
    criar("span", "duracao", `${cena.duracao.toFixed(1)}s`),
  );
  cartao.append(cabeca, criar("div", "marcas", `${cena.inicio} → ${cena.fim}`));

  const params = Object.entries(cena.params);
  if (params.length) {
    const caixa = criar("div", "params");
    for (const [chave, valor] of params) caixa.append(criar("code", null, `${chave}=${valor}`));
    cartao.append(caixa);
  }
  if (cena.fala) cartao.append(criar("p", "fala", cena.fala));

  if (cena.falta) {
    const alvo = criar("div", "soltar");
    alvo.append(criar("strong", null, `largue o arquivo de ${cena.id}`));
    alvo.append(criar("span", "nota", cena.congela
      ? `por enquanto o vídeo congela o quadro de ${cena.congela}`
      : "por enquanto o vídeo mostra uma cartela com o id"));
    ligarSoltura(alvo, (arquivo) => subirAsset(cena.id, arquivo));
    cartao.append(alvo);
  } else {
    cartao.append(previaDoAsset(cena));
    const pronto = criar("div", "pronto");
    pronto.append(criar("span", null, `✓ ${cena.arquivo}`));
    const apagar = criar("button", "apagar", "trocar");
    apagar.onclick = async () => {
      await pedir(`/api/videos/${video}/assets/${cena.id}`, { method: "DELETE" });
      recarregar();
    };
    pronto.append(apagar);
    cartao.append(pronto);
  }
  return cartao;
}

function desenharCenas() {
  const placar = dados.placar;
  $("placar").replaceChildren(
    `${placar.prontas} de ${placar.total} cenas`,
    ...(placar.faltando ? [" — faltam ", criar("b", null, placar.restante), " de vídeo"] : []),
  );
  $("cenas").replaceChildren(...dados.cenas.map(cartaoDaCena));

  const video_mp4 = dados.midia.video || dados.midia.rascunho;
  $("tocador-video").hidden = !video_mp4;
  if (video_mp4) $("tocador-video").src = `${video_mp4}?v=${Date.now()}`;
}

async function subirAsset(id, arquivo) {
  await enviarArquivo(`/api/videos/${video}/assets/${id}`, arquivo);
  await recarregar();
}

// --- soltar arquivo ---

function ligarSoltura(alvo, aoSoltar) {
  const escolher = () => {
    const entrada = criar("input");
    entrada.type = "file";
    entrada.onchange = () => entrada.files[0] && aoSoltar(entrada.files[0]);
    entrada.click();
  };
  alvo.onclick = escolher;
  alvo.ondragover = (e) => { e.preventDefault(); alvo.classList.add("por-cima"); };
  alvo.ondragleave = () => alvo.classList.remove("por-cima");
  alvo.ondrop = (e) => {
    e.preventDefault();
    alvo.classList.remove("por-cima");
    const arquivo = e.dataTransfer.files[0];
    if (arquivo) aoSoltar(arquivo).catch(mostrarErro);
  };
}

function mostrarErro(erro) {
  abrirLog();
  $("log").textContent += `\n${erro.message}\n`;
}

// --- rodar etapa, com o log escorrendo ---

function abrirLog() { $("gaveta").classList.remove("fechada"); }

function travarBotoes(travado) {
  rodando = travado;
  document.querySelectorAll("[data-comando]").forEach((b) => (b.disabled = travado));
  $("giro").hidden = !travado;
}

async function rodar(comando, flags) {
  if (rodando) return;
  abrirLog();
  $("log").textContent = "";
  $("titulo-log").textContent = `studio ${comando} ${video}`;
  travarBotoes(true);
  try {
    const tarefa = await pedir("/api/tarefas", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ comando, numero: video, flags }),
    });
    await seguirLog(tarefa.id);
  } catch (erro) {
    mostrarErro(erro);
  } finally {
    travarBotoes(false);
    await recarregar();
  }
}

function seguirLog(id) {
  return new Promise((resolver) => {
    const fonte = new EventSource(`/api/tarefas/${id}/log`);
    fonte.onmessage = (evento) => {
      const dado = JSON.parse(evento.data);
      if (dado.fim !== undefined) {
        $("titulo-log").textContent += dado.fim === 0 ? " — pronto" : ` — falhou (${dado.fim})`;
        fonte.close();
        resolver();
        return;
      }
      $("log").textContent += `${dado.linha}\n`;
      $("log").scrollTop = $("log").scrollHeight;
    };
    fonte.onerror = () => { fonte.close(); resolver(); };
  });
}

// --- ligar tudo ---

function desenhar() {
  desenharEtapas();
  desenharRoteiro();
  desenharAudio();
  desenharCenas();
}

function ligarAbas() {
  document.querySelectorAll(".abas button").forEach((botao) => {
    botao.onclick = () => {
      document.querySelectorAll(".abas button").forEach((b) => b.classList.remove("ativa"));
      document.querySelectorAll(".aba").forEach((s) => s.classList.remove("ativa"));
      botao.classList.add("ativa");
      $(`aba-${botao.dataset.aba}`).classList.add("ativa");
    };
  });
}

async function comecar() {
  ligarAbas();
  $("alternar-log").onclick = () => $("gaveta").classList.toggle("fechada");
  $("gaveta").classList.add("fechada");
  $("salvar").onclick = salvarScript;
  document.querySelectorAll("[data-comando]").forEach((botao) => {
    botao.onclick = () => rodar(botao.dataset.comando, botao.dataset.flags?.split(" ") || []);
  });
  ligarSoltura($("alvo-audio"), async (arquivo) => {
    await enviarArquivo(`/api/videos/${video}/audio`, arquivo);
    await recarregar();
  });

  const videos = await pedir("/api/videos");
  $("videos").replaceChildren(...videos.map((v) => {
    const opcao = criar("option", null, v.nome);
    opcao.value = v.numero;
    return opcao;
  }));
  $("videos").onchange = () => {
    video = $("videos").value;
    location.hash = video;
    recarregar();
  };

  if (!videos.length) return;
  // `studio ui 01` abre já no vídeo 01
  const pedido = location.hash.replace("#", "");
  video = videos.some((v) => v.numero === pedido) ? pedido : videos[0].numero;
  $("videos").value = video;
  await recarregar();
}

comecar().catch(mostrarErro);
