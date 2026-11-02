import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

APP_TITLE = "AssistTech"
DATA_FILE = "assisttech.json"

st.set_page_config(page_title="AssistTech | Barat im Demais", page_icon="📱", layout="wide")

# -------------------------
# Dados e persistência
# -------------------------
def load_services():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get("servicos"), list):
                return data["servicos"]
        except Exception:
            st.error("Não foi possível ler assisttech.json. Confira se o arquivo é um JSON válido.")
    return []

def save_services():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(servicos, f, ensure_ascii=False, indent=2)

def next_os():
    nums = []
    for s in servicos:
        try:
            nums.append(int(s.get("os", 0)))
        except (ValueError, TypeError):
            pass
    return max(nums, default=0) + 1

def money(value):
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def normalize_service(s, index=0):
    return {
        "os": s.get("os", index + 1),
        "cliente": str(s.get("cliente", "")),
        "contato": str(s.get("contato", "")),
        "aparelho": str(s.get("aparelho", "")),
        "defeito": str(s.get("defeito", "")),
        "servico_realizado": str(s.get("servico_realizado", "")),
        "valor": float(s.get("valor", 0) or 0),
        "status": str(s.get("status", "Em manutenção")),
        "data": str(s.get("data", datetime.now().strftime("%d/%m/%Y"))),
        "historico": s.get("historico", []) if isinstance(s.get("historico", []), list) else [],
    }

if "servicos" not in st.session_state:
    st.session_state.servicos = [normalize_service(s, i) for i, s in enumerate(load_services())]
servicos = st.session_state.servicos

# -------------------------
# Sidebar
# -------------------------
st.sidebar.markdown("# 📱 AssistTech")
st.sidebar.caption("Sistema de assistência técnica")
page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Cadastrar OS", "Ordens de serviço", "Buscar OS", "Histórico", "Importar / Exportar"]
)
st.sidebar.markdown("---")
st.sidebar.caption("BARATIM DEMAIS")

# -------------------------
# Dashboard
# -------------------------
if page == "Dashboard":
    st.title("📊 Dashboard")
    total = len(servicos)
    manut = sum(s["status"] == "Em manutenção" for s in servicos)
    prontos = sum(s["status"] == "Pronto" for s in servicos)
    retirados = sum(s["status"] == "Retirado" for s in servicos)
    valor_total = sum(float(s.get("valor", 0)) for s in servicos)
    valor_retirados = sum(float(s.get("valor", 0)) for s in servicos if s["status"] == "Retirado")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📱 Aparelhos", total)
    c2.metric("🔧 Em manutenção", manut)
    c3.metric("✅ Prontos", prontos)
    c4.metric("📦 Retirados", retirados)

    c5, c6 = st.columns(2)
    c5.metric("💰 Valor total dos serviços", money(valor_total))
    c6.metric("💵 Valor dos serviços retirados", money(valor_retirados))

    if servicos:
        df = pd.DataFrame({
            "Status": ["Em manutenção", "Pronto", "Retirado"],
            "Quantidade": [manut, prontos, retirados]
        })
        st.subheader("Aparelhos por status")
        fig, ax = plt.subplots(figsize=(8, 3.8))
        bars = ax.bar(df["Status"], df["Quantidade"], color=["#FF9800", "#4CAF50", "#2196F3"])
        ax.bar_label(bars, padding=3, fontweight="bold")
        ax.set_ylabel("Quantidade")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_ylim(0, max(df["Quantidade"].tolist() + [1]) * 1.25)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Valor dos serviços por status")
        values = [
            sum(float(s.get("valor", 0)) for s in servicos if s["status"] == "Em manutenção"),
            sum(float(s.get("valor", 0)) for s in servicos if s["status"] == "Pronto"),
            sum(float(s.get("valor", 0)) for s in servicos if s["status"] == "Retirado"),
        ]
        fig2, ax2 = plt.subplots(figsize=(8, 3.8))
        bars2 = ax2.barh(["Em manutenção", "Prontos", "Retirados"], values,
                          color=["#FF9800", "#4CAF50", "#2196F3"])
        ax2.set_xlabel("Valor (R$)")
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        for bar, val in zip(bars2, values):
            ax2.text(val, bar.get_y() + bar.get_height()/2, " " + money(val), va="center")
        ax2.set_xlim(0, max(values + [1]) * 1.5)
        st.pyplot(fig2)
        plt.close(fig2)
    else:
        st.info("Ainda não há ordens cadastradas. Use **Cadastrar OS** para começar.")

# -------------------------
# Cadastro
# -------------------------
elif page == "Cadastrar OS":
    st.title("🧾 Cadastrar ordem de serviço")
    with st.form("form_cadastro", clear_on_submit=True):
        cliente = st.text_input("Nome do cliente *")
        contato = st.text_input("Contato / telefone")
        aparelho = st.text_input("Aparelho / modelo *")
        defeito = st.text_area("Defeito informado *")
        servico_realizado = st.text_area("Serviço realizado (opcional)")
        valor = st.number_input("Valor do serviço (R$)", min_value=0.0, step=10.0, format="%.2f")
        status = st.selectbox("Status", ["Em manutenção", "Pronto", "Retirado"])
        submitted = st.form_submit_button("Cadastrar OS", type="primary")
        if submitted:
            if not cliente.strip() or not aparelho.strip() or not defeito.strip():
                st.error("Preencha cliente, aparelho e defeito informado.")
            else:
                os_num = next_os()
                novo = {
                    "os": os_num,
                    "cliente": cliente.strip(),
                    "contato": contato.strip(),
                    "aparelho": aparelho.strip(),
                    "defeito": defeito.strip(),
                    "servico_realizado": servico_realizado.strip(),
                    "valor": float(valor),
                    "status": status,
                    "data": datetime.now().strftime("%d/%m/%Y"),
                    "historico": [{
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "status": status,
                        "observacao": "OS cadastrada"
                    }]
                }
                servicos.append(novo)
                save_services()
                st.success(f"OS {os_num} cadastrada com sucesso!")

# -------------------------
# PDF
# -------------------------
def build_pdf(s):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFillColorRGB(0.07, 0.23, 0.44)
    pdf.rect(0, height - 4*cm, width, 4*cm, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(2*cm, height - 1.8*cm, "AssistTech")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(2*cm, height - 2.5*cm, "Ordem de Serviço - Assistência Técnica")

    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(2*cm, height - 5*cm, f"ORDEM DE SERVIÇO Nº {s.get('os', '')}")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2*cm, height - 6*cm, "DADOS DO CLIENTE")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(2*cm, height - 6.8*cm, f"Cliente: {s.get('cliente', '')}")
    pdf.drawString(2*cm, height - 7.5*cm, f"Contato: {s.get('contato', '')}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2*cm, height - 8.5*cm, "DADOS DO APARELHO")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(2*cm, height - 9.3*cm, f"Aparelho: {s.get('aparelho', '')}")
    pdf.drawString(2*cm, height - 10*cm, f"Defeito informado: {s.get('defeito', '')[:95]}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2*cm, height - 11*cm, "INFORMAÇÕES DO SERVIÇO")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(2*cm, height - 11.8*cm, f"Serviço realizado: {s.get('servico_realizado', 'Não informado')[:95]}")
    pdf.drawString(2*cm, height - 12.5*cm, f"Status: {s.get('status', '')}")
    pdf.drawString(2*cm, height - 13.2*cm, f"Valor: {money(s.get('valor', 0))}")
    pdf.drawString(2*cm, height - 13.9*cm, f"Data: {s.get('data', '')}")

    pdf.line(2*cm, height - 15.3*cm, 9*cm, height - 15.3*cm)
    pdf.line(11*cm, height - 15.3*cm, 18*cm, height - 15.3*cm)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(2*cm, height - 15.8*cm, "Assinatura do cliente")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(14.5*cm, height - 15*cm, "BARATIM DEMAIS")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(11*cm, height - 15.8*cm, "Assinatura da empresa")

    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawCentredString(width/2, 1.5*cm, "AssistTech - Obrigado pela confiança!")
    pdf.save()
    buffer.seek(0)
    return buffer

# -------------------------
# Listagem / edição / status / PDF
# -------------------------
elif page == "Ordens de serviço":
    st.title("📋 Ordens de serviço")
    if not servicos:
        st.info("Nenhuma OS cadastrada.")
    else:
        for i, s in enumerate(servicos):
            with st.expander(f"OS {s.get('os')} — {s.get('cliente')} — {s.get('aparelho')} ({s.get('status')})"):
                st.write(f"**Contato:** {s.get('contato', '')}")
                st.write(f"**Defeito:** {s.get('defeito', '')}")
                st.write(f"**Serviço realizado:** {s.get('servico_realizado', '')}")
                st.write(f"**Valor:** {money(s.get('valor', 0))}")
                left, right = st.columns(2)
                with left:
                    novo_status = st.selectbox(
                        "Atualizar status",
                        ["Em manutenção", "Pronto", "Retirado"],
                        index=["Em manutenção", "Pronto", "Retirado"].index(s.get("status", "Em manutenção")),
                        key=f"status_{i}"
                    )
                    obs_status = st.text_input("Observação do histórico", key=f"obs_status_{i}")
                    if st.button("Salvar status", key=f"save_status_{i}"):
                        old_status = s.get("status", "")
                        s["status"] = novo_status
                        s.setdefault("historico", []).append({
                            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "status": novo_status,
                            "observacao": obs_status or f"Status alterado de {old_status} para {novo_status}"
                        })
                        save_services()
                        st.success("Status atualizado.")
                        st.rerun()
                with right:
                    with st.form(f"edit_{i}"):
                        e_cliente = st.text_input("Cliente", value=s.get("cliente", ""))
                        e_contato = st.text_input("Contato", value=s.get("contato", ""))
                        e_aparelho = st.text_input("Aparelho", value=s.get("aparelho", ""))
                        e_defeito = st.text_area("Defeito", value=s.get("defeito", ""))
                        e_servico = st.text_area("Serviço realizado", value=s.get("servico_realizado", ""))
                        e_valor = st.number_input("Valor (R$)", min_value=0.0, value=float(s.get("valor", 0)), step=10.0, key=f"valor_{i}")
                        save_edit = st.form_submit_button("Salvar alterações")
                        if save_edit:
                            s.update({
                                "cliente": e_cliente.strip(),
                                "contato": e_contato.strip(),
                                "aparelho": e_aparelho.strip(),
                                "defeito": e_defeito.strip(),
                                "servico_realizado": e_servico.strip(),
                                "valor": float(e_valor)
                            })
                            s.setdefault("historico", []).append({
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "status": s.get("status", ""),
                                "observacao": "Dados da OS editados"
                            })
                            save_services()
                            st.success("OS atualizada.")
                            st.rerun()
                pdf_bytes = build_pdf(s)
                st.download_button(
                    "📄 Baixar PDF da OS",
                    data=pdf_bytes,
                    file_name=f"OS_{s.get('os')}_AssistTech.pdf",
                    mime="application/pdf",
                    key=f"pdf_{i}"
                )

# -------------------------
# Busca
# -------------------------
elif page == "Buscar OS":
    st.title("🔎 Buscar ordens")
    termo = st.text_input("Pesquisar por cliente, contato, aparelho, defeito ou número da OS")
    if termo.strip():
        q = termo.lower().strip()
        encontrados = []
        for s in servicos:
            campos = [s.get(k, "") for k in ["os", "cliente", "contato", "aparelho", "defeito", "status"]]
            if any(q in str(c).lower() for c in campos):
                encontrados.append(s)
        if encontrados:
            df = pd.DataFrame(encontrados)
            cols = [c for c in ["os", "data", "cliente", "contato", "aparelho", "defeito", "valor", "status"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma ordem encontrada.")

# -------------------------
# Histórico
# -------------------------
elif page == "Histórico":
    st.title("🕘 Histórico de manutenção")
    if not servicos:
        st.info("Nenhuma OS cadastrada.")
    else:
        labels = [f"OS {s.get('os')} — {s.get('cliente')} — {s.get('aparelho')}" for s in servicos]
        idx = st.selectbox("Selecione a ordem", range(len(servicos)), format_func=lambda x: labels[x])
        s = servicos[idx]
        st.subheader(f"OS {s.get('os')} — {s.get('cliente')}")
        historico = s.get("historico", [])
        if historico:
            st.dataframe(pd.DataFrame(historico), use_container_width=True, hide_index=True)
        else:
            st.info("Essa OS ainda não possui histórico registrado.")
        nova_obs = st.text_area("Adicionar observação ao histórico")
        if st.button("Registrar observação"):
            s.setdefault("historico", []).append({
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "status": s.get("status", ""),
                "observacao": nova_obs.strip()
            })
            save_services()
            st.success("Observação registrada.")
            st.rerun()

# -------------------------
# Importar / exportar
# -------------------------
elif page == "Importar / Exportar":
    st.title("📦 Importar e exportar dados")
    st.write("Importe o arquivo `assisttech.json` exportado do Colab para trazer suas OS existentes.")
    uploaded = st.file_uploader("Selecionar arquivo JSON", type=["json"])
    if uploaded is not None:
        if st.button("Importar dados do arquivo", type="primary"):
            try:
                imported = json.load(uploaded)
                if isinstance(imported, dict):
                    imported = imported.get("servicos", [])
                if not isinstance(imported, list):
                    raise ValueError("O arquivo precisa conter uma lista de ordens.")
                normalized = [normalize_service(s, i) for i, s in enumerate(imported)]
                st.session_state.servicos = normalized
                servicos = st.session_state.servicos
                save_services()
                st.success(f"Importação concluída: {len(normalized)} ordem(ns) carregada(s).")
                st.rerun()
            except Exception as e:
                st.error(f"Falha na importação: {e}")

    json_data = json.dumps(servicos, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button(
        "⬇️ Exportar backup JSON",
        data=json_data,
        file_name="assisttech_backup.json",
        mime="application/json"
    )
    st.caption("Faça backups periódicos para proteger os dados do sistema.")
