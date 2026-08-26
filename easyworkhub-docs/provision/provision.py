#!/usr/bin/env python3
"""
Provisionamento da arquitetura de projetos do EasyWorkHub via API pública.

Idempotente: rodar duas vezes produz o mesmo resultado (não duplica nada).
Conservador: nunca apaga nada — estados/etiquetas fora do padrão são apenas
reportados no final.

Uso:
  python3 provision.py arquitetura.yaml \
      --base-url https://plane.easyworkhub.com.br \
      --workspace grupo-espacial-motel \
      --token plane_api_xxx \
      [--dry-run]
"""

import argparse
import sys
import time

try:
    import requests
    import yaml
except ImportError:
    sys.exit("Dependências: pip3 install requests pyyaml")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("arquivo", help="arquitetura.yaml")
    p.add_argument("--base-url", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--token", required=True)
    p.add_argument("--dry-run", action="store_true", help="mostra o plano sem aplicar")
    return p.parse_args()


class Api:
    def __init__(self, base_url, workspace, token, dry_run):
        self.base = f"{base_url.rstrip('/')}/api/v1/workspaces/{workspace}"
        self.s = requests.Session()
        self.s.headers["X-Api-Key"] = token
        self.dry = dry_run

    def _req(self, method, path, **kw):
        # rate limit da API: 60/min — pausa curta entre escritas
        r = self.s.request(method, f"{self.base}{path}", timeout=30, **kw)
        if r.status_code == 429:
            time.sleep(61)
            r = self.s.request(method, f"{self.base}{path}", timeout=30, **kw)
        if r.status_code >= 400:
            sys.exit(f"ERRO {r.status_code} em {method} {path}: {r.text[:300]}")
        return r.json() if r.text else {}

    def listar(self, path):
        """Percorre paginação por cursor e devolve todos os resultados."""
        out, cursor = [], None
        while True:
            q = f"?per_page=100&cursor={cursor}" if cursor else "?per_page=100"
            data = self._req("GET", f"{path}{q}")
            if isinstance(data, list):
                return data
            out.extend(data.get("results", []))
            if not data.get("next_page_results"):
                return out
            cursor = data.get("next_cursor")

    def criar(self, path, payload, rotulo):
        if self.dry:
            print(f"  [dry-run] criaria {rotulo}")
            return None
        r = self._req("POST", path, json=payload)
        time.sleep(1.1)
        print(f"  ✓ criado: {rotulo}")
        return r

    def alterar(self, path, payload, rotulo):
        if self.dry:
            print(f"  [dry-run] alteraria {rotulo}")
            return None
        r = self._req("PATCH", path, json=payload)
        time.sleep(1.1)
        print(f"  ✓ alterado: {rotulo}")
        return r


def achatar_etiquetas(grupos):
    """Projetos referenciam listas de grupos (âncoras YAML); achata e deduplica."""
    vistos, out = set(), []
    for grupo in grupos or []:
        for e in grupo:
            if e["nome"] not in vistos:
                vistos.add(e["nome"])
                out.append(e)
    return out


def provisionar_projeto(api, cfg, estados_padrao):
    nome = cfg["nome"]
    print(f"\n── {nome} ──")

    # 1. projeto ------------------------------------------------------------
    existentes = {p["name"]: p for p in api.listar("/projects/")}
    if nome in existentes:
        proj = existentes[nome]
        print(f"  · projeto já existe (id {proj['id'][:8]}…)")
    else:
        proj = api.criar(
            "/projects/",
            {
                "name": nome,
                "identifier": cfg["identificador"],
                "description": cfg.get("descricao", ""),
            },
            f"projeto {nome}",
        )
    # A API pública NÃO expõe o campo `network` (privacidade) — nem no create
    # nem no update. Projetos privados exigem ajuste manual (UI) ou Django shell:
    #   Project.objects.filter(identifier="XXX").update(network=0)
    if cfg.get("network", 2) == 0 and proj and proj.get("network") != 0:
        print(f"  ⚠ PRIVACIDADE: '{nome}' deve ser PRIVADO — a API não permite; "
              "ajustar na UI ou via shell (ver comentário no código)")
        if proj is None:  # dry-run: sem id, não dá para seguir nos filhos
            print("  [dry-run] (estados e etiquetas seriam ajustados em seguida)")
            return
    pid = proj["id"]

    # 2. estados ------------------------------------------------------------
    atuais = api.listar(f"/projects/{pid}/states/")
    por_nome = {s["name"]: s for s in atuais}
    for alvo in estados_padrao:
        if alvo["nome"] in por_nome:
            continue
        origem = alvo.get("renomeia_de")
        if origem and origem in por_nome and por_nome[origem]["group"] == alvo["grupo"]:
            api.alterar(
                f"/projects/{pid}/states/{por_nome[origem]['id']}/",
                {"name": alvo["nome"], "color": alvo["cor"]},
                f"estado {origem} → {alvo['nome']}",
            )
            por_nome[alvo["nome"]] = por_nome.pop(origem)
        else:
            novo = api.criar(
                f"/projects/{pid}/states/",
                {"name": alvo["nome"], "group": alvo["grupo"], "color": alvo["cor"]},
                f"estado {alvo['nome']}",
            )
            if novo:
                por_nome[alvo["nome"]] = novo

    nomes_alvo = {e["nome"] for e in estados_padrao}
    sobras = [n for n in por_nome if n not in nomes_alvo]
    if sobras:
        print(f"  ⚠ estados fora do padrão (não removidos): {sobras}")

    # 3. etiquetas ----------------------------------------------------------
    etiquetas = achatar_etiquetas(cfg.get("etiquetas"))
    if etiquetas:
        atuais = {l["name"] for l in api.listar(f"/projects/{pid}/labels/")}
        for e in etiquetas:
            if e["nome"] not in atuais:
                api.criar(
                    f"/projects/{pid}/labels/",
                    {"name": e["nome"], "color": e["cor"]},
                    f"etiqueta {e['nome']}",
                )

    # 4. recursos do projeto ------------------------------------------------
    # Visualizações sempre ativas (brief §7); ciclos/módulos desligados por
    # padrão (brief §24: evitar interfaces com campos demais); intake só onde
    # a arquitetura pedir (brief §11).
    desejado = {
        "issue_views_view": cfg.get("visualizacoes", True),
        "cycle_view": cfg.get("ciclos", False),
        "module_view": cfg.get("modulos", False),
        "intake_view": cfg.get("intake", False),
    }
    diferencas = {k: v for k, v in desejado.items() if proj.get(k) != v}
    if diferencas:
        api.alterar(f"/projects/{pid}/", diferencas,
                    f"recursos {sorted(diferencas)}")
    else:
        print("  · recursos já corretos")


def main():
    args = parse_args()
    with open(args.arquivo, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    api = Api(args.base_url, args.workspace, args.token, args.dry_run)
    print(f"Workspace: {args.workspace} @ {args.base_url}"
          + (" [DRY-RUN]" if args.dry_run else ""))

    for projeto in cfg["projetos"]:
        provisionar_projeto(api, projeto, cfg["estados_padrao"])

    print("\nConcluído." + (" Nada foi alterado (dry-run)." if args.dry_run else ""))


if __name__ == "__main__":
    main()
