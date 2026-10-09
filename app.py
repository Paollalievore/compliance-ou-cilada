
"""
=============================================================
  COMPLIANCE OU CILADA — Versão Final
  Identidade Visual Camil + Respostas Anônimas + Render
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
#  CORES DA IDENTIDADE VISUAL CAMIL
# ═══════════════════════════════════════════════
# Verde Compliance:  #8DC63F
# Laranja Cilada:    #F7941D
# Azul Camil escuro: #003087
# Azul Camil médio:  #0072CE
# Fundo:             #FFFFFF


# ═══════════════════════════════════════════════
#  BANCO DE DADOS
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
            ds_boa_pratica       TEXT,
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
        CREATE TABLE IF NOT EXISTS respostas (
            id_resposta           INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pergunta           TEXT NOT NULL,
            id_campanha           TEXT,
            cd_tema               TEXT,
            cd_subtema            TEXT,
            ds_resposta_escolhida TEXT NOT NULL CHECK(ds_resposta_escolhida IN ('compliance','cilada')),
            ds_resposta_correta   TEXT NOT NULL,
            fl_acertou            INTEGER NOT NULL,
            dt_resposta           DATETIME DEFAULT CURRENT_TIMESTAMP,
            ds_canal_origem       TEXT DEFAULT 'email',
            ds_ip_origem          TEXT,
            ds_user_agent         TEXT,
            ds_sensor_id          TEXT DEFAULT 'COMPLIANCE_OU_CILADA',
            FOREIGN KEY (id_pergunta) REFERENCES perguntas(id_pergunta)
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_pergunta ON respostas(id_pergunta)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_campanha ON respostas(id_campanha)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_tema     ON respostas(cd_tema)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_data     ON respostas(dt_resposta)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_resp_sensor   ON respostas(ds_sensor_id)")

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
#  SEED — Dados iniciais
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
        ("T09.01", "T09", "Troca de informações com concorrentes"),
        ("T09.02", "T09", "Combinação de preços"),
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

    # PERGUNTA 1 — Brinde do fornecedor (Compliance)
    c.execute("""
        INSERT INTO perguntas (id_pergunta, id_campanha, cd_tema, cd_subtema,
                               ds_cenario, ds_resposta_correta,
                               ds_explicacao_acerto, ds_explicacao_erro,
                               ds_boa_pratica,
                               ds_fonte_normativa, ds_nivel_dificuldade,
                               ds_tags, dt_envio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Q001", "C2026-01", "T03", "T03.01",
        "Um fornecedor da sua área te envia uma caixa de chocolates no valor de "
        "130 reais como agradecimento pela parceria. No momento do oferecimento, "
        "ele não participa de nenhuma concorrência ou negociação.",
        "compliance",
        "O recebimento de brindes de baixo valor pode ser permitido, desde que "
        "não exista uma situação que possa comprometer a imparcialidade da relação, "
        "como uma concorrência ou negociação em andamento com o fornecedor.",
        "O recebimento de brindes de baixo valor pode ser permitido, desde que "
        "não exista uma situação que possa comprometer a imparcialidade da relação, "
        "como uma concorrência ou negociação em andamento com o fornecedor.",
        "Antes de aceitar, pense no contexto. O valor está dentro da política? "
        "O fornecedor está fora de uma concorrência? O presente pode influenciar "
        "ou parecer influenciar uma decisão?",
        "Código de Conduta — Política de Brindes e Hospitalidades",
        "facil",
        "brindes,fornecedor,presente,chocolates",
        "2026-10-14"
    ))

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
#  ROTA PRINCIPAL — Registro + Feedback (anônimo)
# ═══════════════════════════════════════════════

@app.route("/compliance-ou-cilada")
def responder():
    id_pergunta = request.args.get("pergunta", "").strip()
    resposta    = request.args.get("resposta", "").strip().lower()

    if not id_pergunta or not resposta:
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

    resposta_correta = pergunta["ds_resposta_correta"]
    acertou = (resposta == resposta_correta)

    c.execute("""
        INSERT INTO respostas
            (id_pergunta, id_campanha, cd_tema, cd_subtema,
             ds_resposta_escolhida, ds_resposta_correta, fl_acertou,
             ds_canal_origem, ds_ip_origem, ds_user_agent, ds_sensor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_pergunta,
        pergunta["id_campanha"],
        pergunta["cd_tema"],
        pergunta["cd_subtema"],
        resposta,
        resposta_correta,
        1 if acertou else 0,
        "email",
        request.remote_addr,
        request.headers.get("User-Agent", ""),
        SENSOR_ID
    ))
    conn.commit()
    conn.close()

    explicacao = pergunta["ds_explicacao_acerto"] if acertou else pergunta["ds_explicacao_erro"]
    boa_pratica = pergunta["ds_boa_pratica"] or ""

    return render_feedback(
        acertou=acertou,
        resposta_usuario=resposta,
        resposta_correta=resposta_correta,
        cenario=pergunta["ds_cenario"],
        explicacao=explicacao,
        boa_pratica=boa_pratica
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
            COUNT(*)                                                AS total_respostas,
            SUM(CASE WHEN fl_acertou = 1 THEN 1 ELSE 0 END)       AS total_acertos,
            SUM(CASE WHEN fl_acertou = 0 THEN 1 ELSE 0 END)       AS total_erros,
            ROUND(AVG(fl_acertou) * 100, 1)                        AS taxa_acerto_pct
        FROM respostas
    """)
    geral = dict(c.fetchone())

    c.execute("""
        SELECT
            r.id_pergunta,
            r.id_campanha,
            r.cd_tema,
            t.ds_tema,
            p.ds_nivel_dificuldade,
            COUNT(*)                                                                      AS total_respostas,
            SUM(CASE WHEN r.ds_resposta_escolhida = 'compliance' THEN 1 ELSE 0 END)      AS cliques_compliance,
            SUM(CASE WHEN r.ds_resposta_escolhida = 'cilada'     THEN 1 ELSE 0 END)      AS cliques_cilada,
            SUM(CASE WHEN r.fl_acertou = 1 THEN 1 ELSE 0 END)                            AS acertos,
            SUM(CASE WHEN r.fl_acertou = 0 THEN 1 ELSE 0 END)                            AS erros,
            ROUND(AVG(r.fl_acertou) * 100, 1)                                             AS taxa_acerto_pct
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
            ROUND(AVG(r.fl_acertou) * 100, 1) AS taxa_acerto_pct
        FROM respostas r
        LEFT JOIN campanhas ca ON r.id_campanha = ca.id_campanha
        GROUP BY r.id_campanha
        ORDER BY ca.dt_inicio
    """)
    por_campanha = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({"sensor_id": SENSOR_ID, "gerado_em": datetime.now().isoformat(), "por_campanha": por_campanha})


# ═══════════════════════════════════════════════
#  EXPORTAÇÃO CSV
# ═══════════════════════════════════════════════

@app.route("/api/exportar")
def exportar_csv():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT
            r.ds_sensor_id, r.id_resposta, r.id_pergunta, r.id_campanha,
            r.cd_tema, t.ds_tema, r.cd_subtema, st.ds_subtema,
            p.ds_nivel_dificuldade, p.ds_fonte_normativa,
            r.ds_resposta_escolhida, r.ds_resposta_correta,
            CASE WHEN r.fl_acertou = 1 THEN 'Acertou' ELSE 'Errou' END AS resultado,
            r.dt_resposta, r.ds_canal_origem
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
        headers={"Content-Disposition": "attachment; filename=compliance_ou_cilada_export.csv"}
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
                                   ds_boa_pratica,
                                   ds_fonte_normativa, ds_nivel_dificuldade,
                                   ds_tags, dt_envio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id_pergunta"], data.get("id_campanha"), data["cd_tema"],
            data.get("cd_subtema"), data["ds_cenario"], data["ds_resposta_correta"],
            data["ds_explicacao_acerto"], data["ds_explicacao_erro"],
            data.get("ds_boa_pratica"),
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


# ═══════════════════════════════════════════════
#  TEMPLATE HTML — Identidade Visual Camil
#  Baseado no PPT "Compliance ou Cilada"
# ═══════════════════════════════════════════════

def render_feedback(erro_sistema=False, mensagem="", acertou=None,
                    resposta_usuario="", resposta_correta="",
                    cenario="", explicacao="", boa_pratica=""):

    TEMPLATE = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Compliance ou Cilada — Integridade Camil</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: 'Montserrat', 'Segoe UI', system-ui, sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                background-color: #f0f4f8;
            }

            .card {
                background: #ffffff;
                border-radius: 24px;
                padding: 0;
                max-width: 640px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.12);
                overflow: hidden;
                animation: slideUp 0.6s ease-out;
            }

            @keyframes slideUp {
                from { opacity: 0; transform: translateY(40px); }
                to   { opacity: 1; transform: translateY(0); }
            }

            /* ── HEADER ── */
            .header {
                background: #003087;
                padding: 28px 40px;
                text-align: center;
            }

            .logo-integridade {
                font-size: 11px;
                font-weight: 700;
                color: #93c5fd;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 16px;
            }

            .titulo-campanha {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                flex-wrap: wrap;
            }

            .tag-compliance {
                background: #8DC63F;
                color: #000000;
                font-size: 22px;
                font-weight: 900;
                padding: 6px 18px;
                border-radius: 6px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .tag-ou {
                background: #003087;
                border: 2px solid #93c5fd;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 4px 12px;
                border-radius: 20px;
            }

            .tag-cilada {
                background: #F7941D;
                color: #000000;
                font-size: 22px;
                font-weight: 900;
                padding: 6px 18px;
                border-radius: 6px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .tagline {
                color: #bfdbfe;
                font-size: 13px;
                margin-top: 12px;
                font-weight: 400;
            }
            .tagline strong {
                font-weight: 700;
                color: #ffffff;
            }

            /* ── RESULTADO ── */
            .resultado-banner {
                padding: 20px 40px;
                text-align: center;
                font-size: 20px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }

            .resultado-acertou {
                background: #d4edda;
                color: #155724;
            }

            .resultado-errou {
                background: #f8d7da;
                color: #721c24;
            }

            .resultado-erro-sistema {
                background: #e0e7ff;
                color: #3730a3;
            }

            /* ── CONTEÚDO ── */
            .conteudo {
                padding: 28px 40px 32px;
            }

            .resposta-info {
                display: flex;
                justify-content: center;
                gap: 24px;
                margin-bottom: 20px;
                font-size: 13px;
                color: #6b7280;
            }
            .resposta-info span {
                display: flex;
                align-items: center;
                gap: 6px;
            }
            .dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
            }
            .dot-sua     { background: #0072CE; }
            .dot-correta { background: #8DC63F; }

            .badge-resposta {
                display: inline-block;
                padding: 8px 24px;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 24px;
            }
            .badge-compliance {
                background: #8DC63F;
                color: #000000;
            }
            .badge-cilada {
                background: #F7941D;
                color: #000000;
            }

            .cenario-box {
                background: #f8f9fa;
                border-left: 4px solid #003087;
                padding: 16px 20px;
                border-radius: 0 8px 8px 0;
                margin-bottom: 20px;
            }
            .cenario-label {
                font-size: 11px;
                font-weight: 700;
                color: #003087;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 6px;
            }
            .cenario-texto {
                font-size: 14px;
                color: #374151;
                line-height: 1.7;
            }

            .explicacao-box {
                padding: 18px 20px;
                border-radius: 10px;
                margin-bottom: 16px;
                font-size: 14px;
                color: #1f2937;
                line-height: 1.7;
            }
            .explicacao-acertou {
                background: #ecfdf5;
                border: 1px solid #a7f3d0;
            }
            .explicacao-errou {
                background: #fef2f2;
                border: 1px solid #fecaca;
            }

            .boa-pratica-box {
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 10px;
                padding: 18px 20px;
                margin-bottom: 16px;
            }
            .boa-pratica-label {
                font-size: 11px;
                font-weight: 700;
                color: #0072CE;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 6px;
            }
            .boa-pratica-texto {
                font-size: 14px;
                color: #1e40af;
                line-height: 1.7;
            }

            /* ── FOOTER ── */
            .footer {
                background: #f9fafb;
                padding: 16px 40px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
            }
            .footer p {
                font-size: 11px;
                color: #9ca3af;
            }
            .footer .programa {
                font-weight: 700;
                color: #003087;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="card">

            <!-- HEADER -->
            <div class="header">
                <div class="logo-integridade">✦ Integridade Camil</div>
                <div class="titulo-campanha">
                    <span class="tag-compliance">COMPLIANCE</span>
                    <span class="tag-ou">ou</span>
                    <span class="tag-cilada">CILADA?</span>
                </div>
                <div class="tagline">Antes de decidir, <strong>pergunte.</strong></div>
            </div>

            {% if erro_sistema %}
                <!-- ERRO DO SISTEMA -->
                <div class="resultado-banner resultado-erro-sistema">
                    ⚠️ Ops!
                </div>
                <div class="conteudo" style="text-align:center;">
                    <p style="color:#4b5563; font-size:15px;">{{ mensagem }}</p>
                </div>

            {% else %}
                <!-- RESULTADO -->
                {% if acertou %}
                    <div class="resultado-banner resultado-acertou">
                        ✅ Você Acertou!
                    </div>
                {% else %}
                    <div class="resultado-banner resultado-errou">
                        ❌ Você Errou
                    </div>
                {% endif %}

                <div class="conteudo">

                    <!-- Sua resposta vs Correta -->
                    <div class="resposta-info">
                        <span>
                            <span class="dot dot-sua"></span>
                            Sua resposta: <strong>{{ resposta_usuario|capitalize }}</strong>
                        </span>
                        <span>
                            <span class="dot dot-correta"></span>
                            Correta: <strong>{{ resposta_correta|capitalize }}</strong>
                        </span>
                    </div>

                    <!-- Badge da resposta correta -->
                    <div style="text-align:center; margin-bottom:24px;">
                        <span class="badge-resposta badge-{{ resposta_correta }}">
                            É {{ resposta_correta|upper }}
                        </span>
                    </div>

                    <!-- Cenário -->
                    <div class="cenario-box">
                        <div class="cenario-label">📋 Cenário</div>
                        <div class="cenario-texto">{{ cenario }}</div>
                    </div>

                    <!-- Explicação -->
                    <div class="explicacao-box {% if acertou %}explicacao-acertou{% else %}explicacao-errou{% endif %}">
                        {{ explicacao }}
                    </div>

                    <!-- Boa Prática -->
                    {% if boa_pratica %}
                    <div class="boa-pratica-box">
                        <div class="boa-pratica-label">💡 Boa prática</div>
                        <div class="boa-pratica-texto">{{ boa_pratica }}</div>
                    </div>
                    {% endif %}

                </div>
            {% endif %}

            <!-- FOOTER -->
            <div class="footer">
                <p class="programa">Programa de Integridade e Compliance Camil</p>
                <p>{{ now }}</p>
            </div>

        </div>
    </body>
    </html>
    """

    return render_template_string(
        TEMPLATE,
        erro_sistema=erro_sistema, mensagem=mensagem, acertou=acertou,
        resposta_usuario=resposta_usuario, resposta_correta=resposta_correta,
        cenario=cenario, explicacao=explicacao, boa_pratica=boa_pratica,
        now=datetime.now().strftime("%d/%m/%Y %H:%M")
    )


# ═══════════════════════════════════════════════
#  INICIALIZAÇÃO
# ═══════════════════════════════════════════════

init_db()
seed_dados()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

