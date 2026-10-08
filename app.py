
"""
=============================================================
  COMPLIANCE OU CILADA — Backend Íris-Ready
  Versão para produção (Render)
=============================================================
"""

from flask import Flask, request, render_template_string, jsonify, Response
from datetime import datetime
import sqlite3
import os
import io

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "compliance_ou_cilada.db")
SENSOR_ID = "COMPLIANCE_OU_CILADA"


# ═══════════════════════════════════════════════
#  BANCO DE DADOS — Inicialização Completa
# ═══════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS taxonomia_temas (
            cd_tema      TEXT PRIMARY KEY,
            ds_tema      TEXT NOT NULL,
            ds_descricao TEXT,
            fl_ativo     INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS taxonomia_subtemas (
            cd_subtema   TEXT PRIMARY KEY,
            cd_tema      TEXT NOT NULL,
            ds_subtema   TEXT NOT NULL,
            fl_ativo     INTEGER DEFAULT 1,
            FOREIGN KEY (cd_tema) REFERENCES taxonomia_temas(cd_tema)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS campanhas (
            id_campanha     TEXT PRIMARY KEY,
            ds_campanha     TEXT NOT NULL,
            dt_inicio       DATE,
            dt_fim          DATE,
            ds_publico_alvo TEXT,
            ds_objetivo     TEXT,
            fl_ativa        INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS perguntas (
            id_pergunta          TEXT PRIMARY KEY,
            id_campanha          TEXT,
            cd_tema              TEXT NOT NULL,
            cd_subtema           TEXT,
            ds_cenario           TEXT NOT NULL,
            ds_resposta_correta  TEXT NOT NULL CHECK(ds_resposta_correta IN ('compliance','cilada')),
            ds_explicacao_acerto TEXT NOT NULL,
            ds_explicacao_erro   TEXT NOT NULL,
            ds_fonte_normativa   TEXT,
            ds_nivel_dificuldade TEXT DEFAULT 'medio' CHECK(ds_nivel_dificuldade IN ('facil','medio','dificil')),
            ds_tags              TEXT,
            dt_envio             DATE,
            fl_ativa             INTEGER DEFAULT 1,
            FOREIGN KEY (id_campanha) REFERENCES campanhas(id_campanha),
            FOREIGN KEY (cd_tema) REFERENCES taxonomia_temas(cd_tema),
            FOREIGN KEY (cd_subtema) REFERENCES taxonomia_subtemas(cd_subtema)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS envios (
            id_envio         INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pergunta      TEXT NOT NULL,
            id_campanha      TEXT,
            ds_email_destino TEXT NOT NULL,
            ds_area          TEXT,
            ds_unidade       TEXT,
            ds_localidade    TEXT,
            ds_canal_envio   TEXT DEFAULT 'email',
            dt_envio         DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_pergunta) REFERENCES perguntas(id_pergunta),
            FOREIGN KEY (id_campanha) REFERENCES campanhas(id_campanha)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS respostas (
            id_resposta           INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pergunta           TEXT NOT NULL,
            id_campanha           TEXT,
            cd_tema               TEXT,
            cd_subtema            TEXT,
            ds_email_usuario      TEXT NOT NULL,
            ds_area               TEXT,
            ds_unidade            TEXT,
            ds_localidade         TEXT,
            ds_resposta_escolhida TEXT NOT NULL CHECK(ds_resposta_escolhida IN ('compliance','cilada')),
            ds_resposta_correta   TEXT NOT NULL,
            fl_acertou            INTEGER NOT NULL,
            dt_resposta           DATETIME DEFAULT CURRENT_TIMESTAMP,
            qt_tempo_resposta_seg INTEGER,
            ds_canal_origem       TEXT DEFAULT 'email',
            ds_ip_origem          TEXT,
            ds_user_agent         TEXT,
            ds_sensor_id          TEXT DEFAULT 'COMPLIANCE_OU_CILADA',
            FOREIGN KEY (id_pergunta) REFERENCES perguntas(id_pergunta)
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_pergunta  ON respostas(id_pergunta)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_campanha  ON respostas(id_campanha)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_tema      ON respostas(cd_tema)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_usuario   ON respostas(ds_email_usuario)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_data      ON respostas(dt_resposta)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_sensor    ON respostas(ds_sensor_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_envios_pergunta ON envios(id_pergunta)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_envios_email   ON envios(ds_email_destino)")

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
#  SEED — Dados de exemplo
# ═══════════════════════════════════════════════

def seed_dados():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM taxonomia_temas")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    temas = [
        ("T01", "Conflito de Interesses", "Situações de interesse dual ou conflitante"),
        ("T02", "Anticorrupção", "Suborno, propina, pagamento de facilitação"),
        ("T03", "Brindes e Hospitalidades", "Presentes, viagens, eventos, convites"),
        ("T04", "Relacionamento com Terceiros", "Fornecedores, parceiros, prestadores"),
        ("T05", "Proteção de Dados e Privacidade", "LGPD, dados pessoais, consentimento"),
        ("T06", "Informação Confidencial", "Sigilo, informação privilegiada"),
        ("T07", "Assédio e Discriminação", "Assédio moral, sexual, discriminação"),
        ("T08", "Fraude e Desvio", "Fraude contábil, desvio de recursos"),
        ("T09", "Concorrência e Antitruste", "Práticas anticoncorrenciais, cartel"),
        ("T10", "Meio Ambiente e Sustentabilidade", "Normas ambientais, resíduos"),
        ("T11", "Saúde e Segurança do Trabalho", "NRs, EPIs, segurança"),
        ("T12", "Registros e Controles Internos", "Documentação, aprovações, alçadas"),
        ("T13", "Uso de Recursos da Empresa", "Ativos, equipamentos, tempo"),
        ("T14", "Relações Governamentais", "Agentes públicos, licitações"),
        ("T15", "Canal de Ética e Não Retaliação", "Denúncias, proteção ao denunciante"),
        ("T16", "Conduta Digital", "Redes sociais, e-mail corporativo, TI"),
        ("T17", "Lavagem de Dinheiro", "PLD/FT, operações suspeitas"),
        ("T18", "Outro", "Temas não classificados nas categorias anteriores"),
    ]
    c.executemany("INSERT INTO taxonomia_temas (cd_tema, ds_tema, ds_descricao) VALUES (?,?,?)", temas)

    subtemas = [
        ("T01.01", "T01", "Relações familiares/pessoais com fornecedores"),
        ("T01.02", "T01", "Participação societária em concorrente/fornecedor"),
        ("T01.03", "T01", "Atividade paralela conflitante"),
        ("T03.01", "T03", "Recebimento de brindes acima do limite"),
        ("T03.02", "T03", "Oferecimento de hospitalidade a agente público"),
        ("T03.03", "T03", "Convites para eventos de fornecedores"),
        ("T02.01", "T02", "Pagamento de facilitação"),
        ("T02.02", "T02", "Doações e patrocínios com contrapartida indevida"),
        ("T05.01", "T05", "Compartilhamento indevido de dados pessoais"),
        ("T05.02", "T05", "Coleta sem consentimento"),
        ("T15.01", "T15", "Uso correto do canal de denúncias"),
        ("T15.02", "T15", "Proteção contra retaliação"),
    ]
    c.executemany("INSERT INTO taxonomia_subtemas (cd_subtema, cd_tema, ds_subtema) VALUES (?,?,?)", subtemas)

    c.execute("""
        INSERT INTO campanhas (id_campanha, ds_campanha, dt_inicio, dt_fim,
                               ds_publico_alvo, ds_objetivo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "C2026-01",
        "Compliance ou Cilada — Outubro 2026",
        "2026-10-07",
        "2026-10-31",
        "Todos os colaboradores",
        "Engajar colaboradores em temas de integridade e medir nível de conhecimento"
    ))

    c.execute("""
        INSERT INTO perguntas (id_pergunta, id_campanha, cd_tema, cd_subtema,
                               ds_cenario, ds_resposta_correta,
                               ds_explicacao_acerto, ds_explicacao_erro,
                               ds_fonte_normativa, ds_nivel_dificuldade,
                               ds_tags, dt_envio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Q001", "C2026-01", "T03", "T03.03",
        "Um fornecedor oferece ingressos VIP para um evento esportivo ao comprador "
        "da empresa, sem qualquer relação com negociações em andamento.",
        "cilada",
        "Correto! Aceitar presentes de fornecedores, mesmo sem negociação ativa, "
        "pode configurar conflito de interesses e viola o Código de Conduta da empresa. "
        "Sempre recuse e comunique ao Compliance.",
        "Atenção! Aceitar presentes de fornecedores, mesmo fora de negociações, "
        "pode configurar conflito de interesses. Segundo nosso Código de Conduta, "
        "presentes acima de R$100 devem ser recusados e reportados ao Compliance.",
        "Código de Conduta, seção 4.2 — Brindes e Hospitalidades",
        "facil",
        "brindes,fornecedor,evento,presente",
        "2026-10-14"
    ))

    c.execute("""
        INSERT INTO perguntas (id_pergunta, id_campanha, cd_tema, cd_subtema,
                               ds_cenario, ds_resposta_correta,
                               ds_explicacao_acerto, ds_explicacao_erro,
                               ds_fonte_normativa, ds_nivel_dificuldade,
                               ds_tags, dt_envio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Q002", "C2026-01", "T15", "T15.01",
        "Ao identificar uma transação suspeita no sistema financeiro, o colaborador "
        "reporta imediatamente ao canal de denúncias da empresa.",
        "compliance",
        "Parabéns! Reportar transações suspeitas é exatamente o que nosso programa "
        "de Compliance espera. Você está protegendo a empresa e agindo com integridade.",
        "Na verdade, reportar transações suspeitas ao canal de denúncias é a atitude "
        "correta! Isso faz parte do nosso programa de Compliance e é dever de todo "
        "colaborador. Fique atento às próximas situações!",
        "Política de Canal de Ética, seção 2.1",
        "medio",
        "canal,denuncia,transacao,financeiro",
        "2026-10-21"
    ))

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
#  ROTA PRINCIPAL — Registro + Feedback
# ═══════════════════════════════════════════════

@app.route("/compliance-ou-cilada")
def responder():
    id_pergunta = request.args.get("pergunta", "").strip()
    resposta    = request.args.get("resposta", "").strip().lower()
    usuario     = request.args.get("usuario", "").strip().lower()
    canal       = request.args.get("canal", "email").strip().lower()

    if not id_pergunta or not resposta or not usuario:
        return render_feedback(erro_sistema=True,
                               mensagem="Link inválido. Parâmetros ausentes."), 400

    if resposta not in ("compliance", "cilada"):
        return render_feedback(erro_sistema=True,
                               mensagem="Resposta inválida."), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM perguntas WHERE id_pergunta = ?", (id_pergunta,))
    pergunta = c.fetchone()

    if not pergunta:
        conn.close()
        return render_feedback(erro_sistema=True,
                               mensagem=f"Pergunta '{id_pergunta}' não encontrada."), 404

    c.execute("""
        SELECT id_resposta FROM respostas
        WHERE id_pergunta = ? AND ds_email_usuario = ?
    """, (id_pergunta, usuario))
    ja_respondeu = c.fetchone()

    resposta_correta = pergunta["ds_resposta_correta"]
    acertou = (resposta == resposta_correta)

    if not ja_respondeu:
        tempo_resposta = None
        c.execute("""
            SELECT dt_envio FROM envios
            WHERE id_pergunta = ? AND ds_email_destino = ?
            ORDER BY dt_envio DESC LIMIT 1
        """, (id_pergunta, usuario))
        envio = c.fetchone()
        if envio and envio["dt_envio"]:
            try:
                dt_envio = datetime.fromisoformat(envio["dt_envio"])
                tempo_resposta = int((datetime.now() - dt_envio).total_seconds())
            except (ValueError, TypeError):
                tempo_resposta = None

        area = unidade = localidade = None
        if envio:
            c.execute("""
                SELECT ds_area, ds_unidade, ds_localidade FROM envios
                WHERE id_pergunta = ? AND ds_email_destino = ?
                ORDER BY dt_envio DESC LIMIT 1
            """, (id_pergunta, usuario))
            dados_usuario = c.fetchone()
            if dados_usuario:
                area = dados_usuario["ds_area"]
                unidade = dados_usuario["ds_unidade"]
                localidade = dados_usuario["ds_localidade"]

        c.execute("""
            INSERT INTO respostas
                (id_pergunta, id_campanha, cd_tema, cd_subtema,
                 ds_email_usuario, ds_area, ds_unidade, ds_localidade,
                 ds_resposta_escolhida, ds_resposta_correta, fl_acertou,
                 qt_tempo_resposta_seg, ds_canal_origem,
                 ds_ip_origem, ds_user_agent, ds_sensor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_pergunta,
            pergunta["id_campanha"],
            pergunta["cd_tema"],
            pergunta["cd_subtema"],
            usuario,
            area,
            unidade,
            localidade,
            resposta,
            resposta_correta,
            1 if acertou else 0,
            tempo_resposta,
            canal,
            request.remote_addr,
            request.headers.get("User-Agent", ""),
            SENSOR_ID
        ))
        conn.commit()

    conn.close()

    explicacao = pergunta["ds_explicacao_acerto"] if acertou else pergunta["ds_explicacao_erro"]

    return render_feedback(
        acertou=acertou,
        resposta_usuario=resposta,
        resposta_correta=resposta_correta,
        cenario=pergunta["ds_cenario"],
        explicacao=explicacao,
        ja_respondeu=ja_respondeu is not None
    )


# ═══════════════════════════════════════════════
#  APIs DE INDICADORES
# ═══════════════════════════════════════════════

@app.route("/api/indicadores")
def indicadores_geral():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT
            COUNT(*)                                       AS total_respostas,
            SUM(CASE WHEN fl_acertou = 1 THEN 1 ELSE 0 END) AS total_acertos,
            SUM(CASE WHEN fl_acertou = 0 THEN 1 ELSE 0 END) AS total_erros,
            COUNT(DISTINCT ds_email_usuario)                AS participantes_unicos,
            ROUND(AVG(fl_acertou) * 100, 1)                 AS taxa_acerto_pct,
            ROUND(AVG(qt_tempo_resposta_seg), 0)            AS tempo_medio_resposta_seg
        FROM respostas
    """)
    geral = dict(c.fetchone())

    c.execute("SELECT COUNT(DISTINCT ds_email_destino) FROM envios")
    total_enviados = c.fetchone()[0]
    geral["total_enviados"] = total_enviados
    geral["taxa_participacao_pct"] = (
        round(geral["participantes_unicos"] / total_enviados * 100, 1)
        if total_enviados > 0 else None
    )

    c.execute("""
        SELECT
            r.id_pergunta, r.id_campanha, r.cd_tema, t.ds_tema,
            r.cd_subtema, p.ds_nivel_dificuldade,
            COUNT(*)                                                                      AS total_respostas,
            SUM(CASE WHEN r.ds_resposta_escolhida = 'compliance' THEN 1 ELSE 0 END)      AS cliques_compliance,
            SUM(CASE WHEN r.ds_resposta_escolhida = 'cilada'     THEN 1 ELSE 0 END)      AS cliques_cilada,
            SUM(CASE WHEN r.fl_acertou = 1 THEN 1 ELSE 0 END)                            AS acertos,
            SUM(CASE WHEN r.fl_acertou = 0 THEN 1 ELSE 0 END)                            AS erros,
            ROUND(AVG(r.fl_acertou) * 100, 1)                                             AS taxa_acerto_pct,
            ROUND(AVG(r.qt_tempo_resposta_seg), 0)                                        AS tempo_medio_seg
        FROM respostas r
        JOIN perguntas p ON r.id_pergunta = p.id_pergunta
        LEFT JOIN taxonomia_temas t ON r.cd_tema = t.cd_tema
        GROUP BY r.id_pergunta
        ORDER BY r.id_pergunta
    """)
    por_pergunta = [dict(row) for row in c.fetchall()]

    conn.close()
    return jsonify({
        "sensor_id": SENSOR_ID,
        "gerado_em": datetime.now().isoformat(),
        "resumo_geral": geral,
        "por_pergunta": por_pergunta
    })


@app.route("/api/indicadores/temas")
def indicadores_por_tema():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT r.cd_tema, t.ds_tema,
            COUNT(*) AS total_respostas,
            COUNT(DISTINCT r.ds_email_usuario) AS participantes,
            SUM(CASE WHEN r.fl_acertou = 1 THEN 1 ELSE 0 END) AS acertos,
            SUM(CASE WHEN r.fl_acertou = 0 THEN 1 ELSE 0 END) AS erros,
            ROUND(AVG(r.fl_acertou) * 100, 1) AS taxa_acerto_pct,
            COUNT(DISTINCT r.id_pergunta) AS perguntas_distintas
        FROM respostas r
        LEFT JOIN taxonomia_temas t ON r.cd_tema = t.cd_tema
        GROUP BY r.cd_tema
        ORDER BY taxa_acerto_pct ASC
    """)
    por_tema = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({"sensor_id": SENSOR_ID, "gerado_em": datetime.now().isoformat(), "por_tema": por_tema})


@app.route("/api/indicadores/campanhas")
def indicadores_por_campanha():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT r.id_campanha, ca.ds_campanha,
            COUNT(*) AS total_respostas,
            COUNT(DISTINCT r.ds_email_usuario) AS participantes,
            ROUND(AVG(r.fl_acertou) * 100, 1) AS taxa_acerto_pct,
            ROUND(AVG(r.qt_tempo_resposta_seg), 0) AS tempo_medio_seg
        FROM respostas r
        LEFT JOIN campanhas ca ON r.id_campanha = ca.id_campanha
        GROUP BY r.id_campanha
        ORDER BY ca.dt_inicio
    """)
    por_campanha = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({"sensor_id": SENSOR_ID, "gerado_em": datetime.now().isoformat(), "por_campanha": por_campanha})


@app.route("/api/indicadores/areas")
def indicadores_por_area():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT COALESCE(ds_area, 'Não informado') AS area,
            COUNT(*) AS total_respostas,
            COUNT(DISTINCT ds_email_usuario) AS participantes,
            ROUND(AVG(fl_acertou) * 100, 1) AS taxa_acerto_pct
        FROM respostas
        GROUP BY ds_area
        ORDER BY taxa_acerto_pct ASC
    """)
    por_area = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({"sensor_id": SENSOR_ID, "gerado_em": datetime.now().isoformat(), "por_area": por_area})


# ═══════════════════════════════════════════════
#  EXPORTAÇÃO ESTRUTURADA (Íris-ready)
# ═══════════════════════════════════════════════

@app.route("/api/exportar")
def exportar_csv():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT r.ds_sensor_id, r.id_resposta, r.id_pergunta, r.id_campanha,
            r.cd_tema, t.ds_tema, r.cd_subtema, st.ds_subtema,
            p.ds_nivel_dificuldade, p.ds_fonte_normativa,
            r.ds_email_usuario, r.ds_area, r.ds_unidade, r.ds_localidade,
            r.ds_resposta_escolhida, r.ds_resposta_correta,
            CASE WHEN r.fl_acertou = 1 THEN 'Acertou' ELSE 'Errou' END AS resultado,
            r.dt_resposta, r.qt_tempo_resposta_seg, r.ds_canal_origem
        FROM respostas r
        JOIN perguntas p ON r.id_pergunta = p.id_pergunta
        LEFT JOIN taxonomia_temas t ON r.cd_tema = t.cd_tema
        LEFT JOIN taxonomia_subtemas st ON r.cd_subtema = st.cd_subtema
        ORDER BY r.dt_resposta DESC
    """)
    rows = c.fetchall()
    headers = [desc[0] for desc in c.description]
    conn.close()

    output = io.StringIO()
    output.write(";".join(headers) + "\n")
    for row in rows:
        output.write(";".join(str(v) if v is not None else "" for v in row) + "\n")

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=compliance_ou_cilada_iris_export.csv"}
    )


# ═══════════════════════════════════════════════
#  ADMIN — Cadastro via API
# ═══════════════════════════════════════════════

@app.route("/api/perguntas", methods=["POST"])
def cadastrar_pergunta():
    data = request.get_json()
    obrigatorios = ["id_pergunta", "cd_tema", "ds_cenario",
                    "ds_resposta_correta", "ds_explicacao_acerto", "ds_explicacao_erro"]
    for campo in obrigatorios:
        if campo not in data or not data[campo]:
            return jsonify({"erro": f"Campo obrigatório ausente: {campo}"}), 400

    if data["ds_resposta_correta"] not in ("compliance", "cilada"):
        return jsonify({"erro": "ds_resposta_correta deve ser 'compliance' ou 'cilada'"}), 400

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO perguntas (id_pergunta, id_campanha, cd_tema, cd_subtema,
                                   ds_cenario, ds_resposta_correta,
                                   ds_explicacao_acerto, ds_explicacao_erro,
                                   ds_fonte_normativa, ds_nivel_dificuldade,
                                   ds_tags, dt_envio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id_pergunta"], data.get("id_campanha"), data["cd_tema"],
            data.get("cd_subtema"), data["ds_cenario"], data["ds_resposta_correta"],
            data["ds_explicacao_acerto"], data["ds_explicacao_erro"],
            data.get("ds_fonte_normativa"), data.get("ds_nivel_dificuldade", "medio"),
            data.get("ds_tags"), data.get("dt_envio", datetime.now().strftime("%Y-%m-%d"))
        ))
        conn.commit()
        return jsonify({"sucesso": True, "id_pergunta": data["id_pergunta"]}), 201
    except sqlite3.IntegrityError as e:
        return jsonify({"erro": str(e)}), 409
    finally:
        conn.close()


@app.route("/api/perguntas", methods=["GET"])
def listar_perguntas():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.*, t.ds_tema, st.ds_subtema
        FROM perguntas p
        LEFT JOIN taxonomia_temas t ON p.cd_tema = t.cd_tema
        LEFT JOIN taxonomia_subtemas st ON p.cd_subtema = st.cd_subtema
        ORDER BY p.dt_envio DESC
    """)
    perguntas = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(perguntas)


@app.route("/api/campanhas", methods=["POST"])
def cadastrar_campanha():
    data = request.get_json()
    for campo in ["id_campanha", "ds_campanha"]:
        if campo not in data or not data[campo]:
            return jsonify({"erro": f"Campo obrigatório ausente: {campo}"}), 400
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO campanhas (id_campanha, ds_campanha, dt_inicio, dt_fim,
                                   ds_publico_alvo, ds_objetivo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["id_campanha"], data["ds_campanha"], data.get("dt_inicio"),
            data.get("dt_fim"), data.get("ds_publico_alvo"), data.get("ds_objetivo")
        ))
        conn.commit()
        return jsonify({"sucesso": True}), 201
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Campanha já existe."}), 409
    finally:
        conn.close()


@app.route("/api/taxonomia/temas", methods=["GET"])
def listar_temas():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM taxonomia_temas WHERE fl_ativo = 1 ORDER BY cd_tema")
    temas = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(temas)


@app.route("/api/taxonomia/subtemas", methods=["GET"])
def listar_subtemas():
    cd_tema = request.args.get("tema")
    conn = get_db()
    c = conn.cursor()
    if cd_tema:
        c.execute("SELECT * FROM taxonomia_subtemas WHERE cd_tema = ? AND fl_ativo = 1", (cd_tema,))
    else:
        c.execute("SELECT * FROM taxonomia_subtemas WHERE fl_ativo = 1 ORDER BY cd_subtema")
    subtemas = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(subtemas)


@app.route("/api/envios", methods=["POST"])
def registrar_envios():
    data = request.get_json()
    if not data.get("id_pergunta") or not data.get("destinatarios"):
        return jsonify({"erro": "id_pergunta e destinatarios são obrigatórios"}), 400
    conn = get_db()
    c = conn.cursor()
    count = 0
    for dest in data["destinatarios"]:
        c.execute("""
            INSERT INTO envios (id_pergunta, id_campanha, ds_email_destino,
                                ds_area, ds_unidade, ds_localidade, ds_canal_envio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id_pergunta"], data.get("id_campanha"), dest["email"],
            dest.get("area"), dest.get("unidade"), dest.get("localidade"),
            dest.get("canal", "email")
        ))
        count += 1
    conn.commit()
    conn.close()
    return jsonify({"sucesso": True, "envios_registrados": count}), 201


# ═══════════════════════════════════════════════
#  TEMPLATE HTML — Página de Feedback
# ═══════════════════════════════════════════════

def render_feedback(erro_sistema=False, mensagem="", acertou=None,
                    resposta_usuario="", resposta_correta="",
                    cenario="", explicacao="", ja_respondeu=False):

    TEMPLATE = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Compliance ou Cilada</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                min-height: 100vh; display: flex; align-items: center;
                justify-content: center; padding: 20px;
                {% if erro_sistema %}
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                {% elif acertou %}
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                {% else %}
                    background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
                {% endif %}
            }
            .card {
                background: white; border-radius: 20px; padding: 48px 40px;
                max-width: 600px; width: 100%;
                box-shadow: 0 25px 60px rgba(0,0,0,0.3); text-align: center;
                animation: slideUp 0.6s ease-out;
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(40px); }
                to   { opacity: 1; transform: translateY(0); }
            }
            .icon { width: 80px; height: 80px; border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                margin: 0 auto 24px; font-size: 40px; }
            .icon-acerto  { background: #d1fae5; }
            .icon-erro    { background: #fee2e2; }
            .icon-sistema { background: #e0e7ff; }
            .titulo { font-size: 28px; font-weight: 700; margin-bottom: 8px;
                {% if erro_sistema %} color: #4338ca;
                {% elif acertou %} color: #065f46;
                {% else %} color: #991b1b; {% endif %} }
            .subtitulo { font-size: 15px; color: #6b7280; margin-bottom: 28px; }
            .badge { display: inline-block; padding: 6px 16px; border-radius: 20px;
                font-size: 13px; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.05em; margin-bottom: 24px; }
            .badge-compliance { background: #dbeafe; color: #1e40af; }
            .badge-cilada     { background: #fef3c7; color: #92400e; }
            .cenario { background: #f9fafb; border-left: 4px solid #d1d5db;
                padding: 16px 20px; border-radius: 0 8px 8px 0;
                text-align: left; font-size: 14px; color: #374151;
                line-height: 1.6; margin-bottom: 24px; }
            .explicacao { text-align: left; font-size: 15px; color: #1f2937;
                line-height: 1.7; padding: 20px; border-radius: 12px; margin-bottom: 24px;
                {% if acertou %} background: #ecfdf5; border: 1px solid #a7f3d0;
                {% else %} background: #fef2f2; border: 1px solid #fecaca; {% endif %} }
            .explicacao-titulo { font-weight: 700; font-size: 13px; text-transform: uppercase;
                letter-spacing: 0.05em; margin-bottom: 8px;
                {% if acertou %} color: #065f46; {% else %} color: #991b1b; {% endif %} }
            .resposta-info { display: flex; justify-content: center; gap: 24px;
                margin-bottom: 24px; font-size: 13px; color: #6b7280; }
            .resposta-info span { display: flex; align-items: center; gap: 6px; }
            .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
            .dot-sua     { background: #6366f1; }
            .dot-correta { background: #10b981; }
            .aviso-duplicata { background: #fffbeb; border: 1px solid #fde68a; color: #92400e;
                padding: 10px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; }
            .footer { font-size: 12px; color: #9ca3af; margin-top: 16px; }
            .logo { font-size: 18px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 32px; }
            .logo-compliance { color: #2563eb; }
            .logo-ou         { color: #9ca3af; font-weight: 400; }
            .logo-cilada     { color: #dc2626; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">
                <span class="logo-compliance">COMPLIANCE</span>
                <span class="logo-ou"> ou </span>
                <span class="logo-cilada">CILADA</span>
            </div>
            {% if erro_sistema %}
                <div class="icon icon-sistema">⚠️</div>
                <div class="titulo">Ops!</div>
                <p style="color:#4b5563; margin-top:12px;">{{ mensagem }}</p>
            {% else %}
                {% if ja_respondeu %}
                    <div class="aviso-duplicata">
                        ⚠️ Você já respondeu esta pergunta anteriormente.
                    </div>
                {% endif %}
                {% if acertou %}
                    <div class="icon icon-acerto">✅</div>
                    <div class="titulo">Você acertou!</div>
                    <div class="subtitulo">Excelente! Você conhece bem as práticas de Compliance.</div>
                {% else %}
                    <div class="icon icon-erro">❌</div>
                    <div class="titulo">Você errou!</div>
                    <div class="subtitulo">Fique atento! Veja a explicação abaixo.</div>
                {% endif %}
                <div class="resposta-info">
                    <span><span class="dot dot-sua"></span>
                        Sua resposta: <strong>{{ resposta_usuario|capitalize }}</strong></span>
                    <span><span class="dot dot-correta"></span>
                        Correta: <strong>{{ resposta_correta|capitalize }}</strong></span>
                </div>
                <span class="badge badge-{{ resposta_correta }}">
                    A resposta é: {{ resposta_correta|upper }}
                </span>
                <div class="cenario"><strong>Cenário:</strong> {{ cenario }}</div>
                <div class="explicacao">
                    <div class="explicacao-titulo">
                        {% if acertou %}✅ Por que está certo{% else %}❌ Por que está errado{% endif %}
                    </div>
                    {{ explicacao }}
                </div>
            {% endif %}
            <div class="footer">Programa de Compliance • {{ now }}</div>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        TEMPLATE,
        erro_sistema=erro_sistema, mensagem=mensagem, acertou=acertou,
        resposta_usuario=resposta_usuario, resposta_correta=resposta_correta,
        cenario=cenario, explicacao=explicacao, ja_respondeu=ja_respondeu,
        now=datetime.now().strftime("%d/%m/%Y %H:%M")
    )


# ═══════════════════════════════════════════════
#  INICIALIZAÇÃO — Versão Render (produção)
# ═══════════════════════════════════════════════

# Inicializa o banco ao importar o módulo (necessário para gunicorn)
init_db()
seed_dados()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

