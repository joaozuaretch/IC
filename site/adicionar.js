// Página "Adicionar conteúdo": grava reuniões e PDFs direto no repositório pelo GitHub,
// num único commit na main. O push dispara o workflow que republica o site.
// O acesso usa um token do GitHub guardado só neste navegador, cifrado com a sua senha.
"use strict";

const REPO = "joaozuaretch/IC";
const RAMO = "main";
const API = "https://api.github.com/repos/" + REPO;
const CHAVE = "ic-token-cifrado";

const $ = (s) => document.querySelector(s);
let token = null;
let conteudo = null;   // conteudo.json atual
let caminhos = null;   // todos os arquivos do repositório

// ------------------------------------------------------------ cifra do token

const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));
const unb64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

async function chaveDaSenha(senha, sal) {
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(senha), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", salt: sal, iterations: 250000, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}

async function guardaToken(tk, senha) {
  const sal = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const cifrado = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await chaveDaSenha(senha, sal), new TextEncoder().encode(tk));
  localStorage.setItem(CHAVE, JSON.stringify({ sal: b64(sal), iv: b64(iv), dado: b64(cifrado) }));
}

async function abreToken(senha) {
  const { sal, iv, dado } = JSON.parse(localStorage.getItem(CHAVE));
  const claro = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(iv) }, await chaveDaSenha(senha, unb64(sal)), unb64(dado));
  return new TextDecoder().decode(claro);
}

// ------------------------------------------------------------ GitHub

async function gh(caminho, opcoes = {}) {
  const resp = await fetch(caminho.startsWith("http") ? caminho : API + caminho, {
    ...opcoes,
    headers: { Authorization: "Bearer " + token, Accept: "application/vnd.github+json", ...(opcoes.headers || {}) },
  });
  if (!resp.ok) {
    let msg = resp.status + " " + resp.statusText;
    try { msg += ": " + (await resp.json()).message; } catch (_) { /* sem corpo */ }
    throw new Error(msg);
  }
  return resp.status === 204 ? null : resp.json();
}

const textoB64 = (s) => b64(new TextEncoder().encode(s));

function arquivoB64(arquivo) {
  return new Promise((ok, erro) => {
    const leitor = new FileReader();
    leitor.onload = () => ok(leitor.result.split(",")[1]);
    leitor.onerror = () => erro(leitor.error);
    leitor.readAsDataURL(arquivo);
  });
}

async function carregaRepositorio() {
  const ref = await gh(`/git/ref/heads/${RAMO}`);
  const arvore = await gh(`/git/trees/${ref.object.sha}?recursive=1`);
  caminhos = new Set(arvore.tree.map((t) => t.path));
  const json = await gh(`/contents/conteudo.json?ref=${RAMO}`);
  conteudo = JSON.parse(new TextDecoder().decode(unb64(json.content.replace(/\n/g, ""))));
}

// Grava todos os arquivos num único commit. arquivos: [{caminho, base64}]
async function commit(mensagem, arquivos) {
  const ref = await gh(`/git/ref/heads/${RAMO}`);
  const pai = await gh(`/git/commits/${ref.object.sha}`);
  const tree = [];
  for (const a of arquivos) {
    status(`Enviando ${a.caminho}…`);
    const blob = await gh("/git/blobs", { method: "POST", body: JSON.stringify({ content: a.base64, encoding: "base64" }) });
    tree.push({ path: a.caminho, mode: "100644", type: "blob", sha: blob.sha });
  }
  const novaArvore = await gh("/git/trees", { method: "POST", body: JSON.stringify({ base_tree: pai.tree.sha, tree }) });
  const novo = await gh("/git/commits", { method: "POST", body: JSON.stringify({ message: mensagem, tree: novaArvore.sha, parents: [pai.sha] }) });
  await gh(`/git/refs/heads/${RAMO}`, { method: "PATCH", body: JSON.stringify({ sha: novo.sha }) });
  return novo;
}

// ------------------------------------------------------------ interface

function status(msg, tipo = "") {
  const el = $("#status");
  el.textContent = msg;
  el.className = "status " + tipo;
}

function mostra(id) {
  for (const s of ["#configurar", "#entrar", "#painel"]) $(s).hidden = s !== id;
}

const nomeLimpo = (nome) => nome.normalize("NFC").replace(/[\\/:*?"<>|]+/g, "_").trim();

function preencheMateriais() {
  const lista = $("#materiais");
  lista.innerHTML = "";
  const itens = [...conteudo.apresentacoes, ...conteudo.notas].reverse();
  for (const d of itens) {
    const rotulo = document.createElement("label");
    rotulo.className = "check";
    const caixa = document.createElement("input");
    caixa.type = "checkbox";
    caixa.value = d.arquivo;
    rotulo.append(caixa, " " + d.titulo);
    lista.append(rotulo);
  }
}

function trocaTipo() {
  const tipo = $("input[name=tipo]:checked").value;
  for (const el of document.querySelectorAll("[data-tipo]")) {
    el.hidden = !el.dataset.tipo.split(" ").includes(tipo);
  }
}

async function entra() {
  status("Conferindo o acesso ao repositório…");
  await carregaRepositorio();
  preencheMateriais();
  $("#data").value = new Date().toLocaleDateString("sv-SE");
  mostra("#painel");
  trocaTipo();
  status("");
}

async function envia(evento) {
  evento.preventDefault();
  const botao = $("#enviar");
  botao.disabled = true;
  try {
    await carregaRepositorio();
    const tipo = $("input[name=tipo]:checked").value;
    const arquivos = [];
    let mensagem;

    if (tipo === "reuniao") {
      const data = $("#data").value;
      const texto = $("#texto").value.trim();
      if (!data || !texto) throw new Error("Preencha a data e o texto da reunião.");
      const anotacoes = $("#anotacoes").files[0];
      const pasta = anotacoes ? `Reuniões/Reunião ${data}/` : "Reuniões/";
      const md = `${pasta}Reunião ${data}.md`;
      if (caminhos.has(md) || caminhos.has(`Reuniões/Reunião ${data}.md`) || caminhos.has(`Reuniões/Reunião ${data}/Reunião ${data}.md`)) {
        if (!confirm(`Já existe uma reunião de ${data}. Substituir?`)) throw new Error("Envio cancelado.");
      }
      let corpo = texto + "\n";
      if (anotacoes) {
        const nome = `Anotações_Reunião_${data}.pdf`;
        arquivos.push({ caminho: pasta + nome, base64: await arquivoB64(anotacoes) });
        corpo += `\n![[${nome}]]\n`;
      }
      const usados = [...document.querySelectorAll("#materiais input:checked")].map((c) => c.value);
      usados.push(...$("#outros").value.split("\n").map((l) => l.trim()).filter(Boolean));
      if (usados.length) corpo += "\n***Conteúdos usados :\n" + usados.map((u) => `- [[${u}]]`).join("\n") + "\n";
      arquivos.push({ caminho: md, base64: textoB64(corpo) });
      const tema = $("#tema").value.trim();
      if (tema) conteudo.temas_das_reunioes[data] = tema;
      mensagem = `Adiciona a reunião de ${data}`;
    } else {
      const pdf = $("#pdf").files[0];
      const titulo = $("#titulo").value.trim();
      if (!pdf || !titulo) throw new Error("Escolha o PDF e escreva o título.");
      const pasta = tipo === "apresentacao" ? "Apresentações/" : "PDF's de conteúdo/";
      const lista = { apresentacao: conteudo.apresentacoes, nota: conteudo.notas, trabalho: conteudo.trabalhos }[tipo];
      const nome = nomeLimpo(pdf.name);
      const existente = lista.find((d) => d.arquivo === nome);
      if (caminhos.has(pasta + nome) && !confirm(`Já existe ${nome}. Substituir?`)) throw new Error("Envio cancelado.");
      arquivos.push({ caminho: pasta + nome, base64: await arquivoB64(pdf) });
      const item = { arquivo: nome, titulo, descricao: $("#descricao").value.trim() };
      const fonte = $("#fonte").files[0];
      if (tipo === "apresentacao" && fonte) {
        item.fonte = nomeLimpo(fonte.name);
        arquivos.push({ caminho: pasta + item.fonte, base64: await arquivoB64(fonte) });
      }
      if (existente) Object.assign(existente, item); else lista.push(item);
      mensagem = `Adiciona ${{ apresentacao: "a apresentação", nota: "a nota", trabalho: "o trabalho" }[tipo]} ${titulo}`;
    }

    arquivos.push({ caminho: "conteudo.json", base64: textoB64(JSON.stringify(conteudo, null, 2) + "\n") });
    await commit(mensagem, arquivos);
    $("#formulario").reset();
    $("#data").value = new Date().toLocaleDateString("sv-SE");
    trocaTipo();
    status("Enviado! O site é atualizado em cerca de 1 minuto. Recarregue a página do site depois disso.", "ok");
  } catch (e) {
    status("Não foi possível enviar: " + e.message, "erro");
  } finally {
    botao.disabled = false;
  }
}

// ------------------------------------------------------------ início

document.addEventListener("DOMContentLoaded", () => {
  let salvo = null;
  try { salvo = localStorage.getItem(CHAVE); } catch (_) { /* armazenamento bloqueado */ }
  mostra(salvo ? "#entrar" : "#configurar");

  $("#form-configurar").addEventListener("submit", async (e) => {
    e.preventDefault();
    const senha = $("#nova-senha").value;
    if (senha !== $("#confirma-senha").value) return status("As senhas não conferem.", "erro");
    token = $("#token").value.trim();
    try {
      const repo = await gh("");
      if (!repo.permissions || !repo.permissions.push) throw new Error("este token não pode gravar no repositório.");
      await guardaToken(token, senha);
      await entra();
    } catch (err) {
      token = null;
      status("Token não aceito: " + err.message, "erro");
    }
  });

  $("#form-entrar").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      token = await abreToken($("#senha").value);
    } catch (_) {
      return status("Senha incorreta.", "erro");
    }
    try { await entra(); } catch (err) { status("Erro ao acessar o GitHub: " + err.message + ". Se o token expirou, use “Trocar token”.", "erro"); }
  });

  for (const b of document.querySelectorAll(".esquecer")) {
    b.addEventListener("click", () => {
      if (!confirm("Apagar o token guardado neste navegador?")) return;
      localStorage.removeItem(CHAVE);
      token = null;
      mostra("#configurar");
      status("");
    });
  }
  for (const r of document.querySelectorAll("input[name=tipo]")) r.addEventListener("change", trocaTipo);
  $("#formulario").addEventListener("submit", envia);
});
