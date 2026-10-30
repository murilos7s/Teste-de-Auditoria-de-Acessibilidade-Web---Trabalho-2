import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def carregar_json(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Ficheiro {caminho_arquivo} não encontrado.")
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)

def extrair_falhas(dados_json):
    violacoes = []
    
    # Suporte para formato Lighthouse
    if 'audits' in dados_json:
        audits = dados_json.get('audits', {})
        for key, audit in audits.items():
            # Filtra auditorias reprovadas (score == 0 ou scoreFalse)
            if audit.get('score') is not None and audit.get('score') < 1:
                detalhes = audit.get('details', {})
                items = detalhes.get('items', [])
                
                elementos = []
                for item in items:
                    node = item.get('node', {})
                    selector = node.get('selector', '')
                    snippet = node.get('snippet', '')
                    if selector:
                        elementos.append(selector)
                    elif snippet:
                        elementos.append(snippet)
                
                # Mapeamento de severidade
                impacto = "critical" if audit.get('scoreDisplayMode') == 'binary' else "moderate"
                
                violacoes.append({
                    'id': audit.get('id', key),
                    'impacto': impacto,
                    'descricao': audit.get('title', ''),
                    'ajuda': audit.get('description', ''),
                    'wcag': ['WCAG 2.1 (A/AA)'],
                    'elementos': elementos if elementos else ["Elemento na página"]
                })
                
    # Suporte para formato Axe
    elif 'violations' in dados_json:
        for item in dados_json.get('violations', []):
            elementos = []
            for node in item.get('nodes', []):
                target = node.get('target', [])
                if target:
                    elementos.append(", ".join(target))
                    
            violacoes.append({
                'id': item.get('id', 'N/A'),
                'impacto': item.get('impact', 'minor').lower(),
                'descricao': item.get('help', ''),
                'ajuda': item.get('description', ''),
                'wcag': [tag for tag in item.get('tags', []) if 'wcag' in tag],
                'elementos': elementos
            })
            
    return violacoes

def exibir_resumo_terminal(violacoes):
    print("=" * 60)
    print("RESUMO DA AUDITORIA DE ACESSIBILIDADE WEB")
    print("=" * 60)
    print(f"Total de falhas encontradas: {len(violacoes)}\n")
    
    for idx, v in enumerate(violacoes, 1):
        print(f"[{idx}] Regra: {v['id']} | Impacto: {v['impacto'].upper()}")
        print(f"    Descrição : {v['descricao']}")
        print(f"    Elementos : {'; '.join(v['elementos'][:3])}")
        print("-" * 60)

def gerar_relatorio_pdf(violacoes, caminho_pdf="relatorio_acessibilidade.pdf"):
    doc = SimpleDocTemplate(caminho_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#1A365D')
    )
    story.append(Paragraph("Relatório de Auditoria de Acessibilidade - TechInclusiva", title_style))
    story.append(Paragraph("Mapeamento de Conformidade WCAG 2.1 (Níveis A e AA)", styles['Normal']))
    story.append(Spacer(1, 15))
    
    dados_tabela = [["Severidade", "Regra", "Descrição da Falha", "Elementos Afetados"]]
    
    for v in violacoes:
        impacto = v['impacto'].capitalize()
        regra = f"<b>{v['id']}</b>"
        descricao = v['descricao']
        elementos = "<br/>".join(v['elementos'][:3]) if v['elementos'] else "N/A"
        
        dados_tabela.append([
            Paragraph(impacto, styles['Normal']),
            Paragraph(regra, styles['Normal']),
            Paragraph(descricao, styles['Normal']),
            Paragraph(f"<code>{elementos}</code>", styles['Normal'])
        ])
        
    tabela = Table(dados_tabela, colWidths=[75, 110, 185, 150])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(tabela)
    doc.build(story)
    print(f"\n[+] Relatório PDF gerado com sucesso: {caminho_pdf}")

if __name__ == "__main__":
    ARQUIVO_JSON = "resultado_axe.json"
    try:
        dados = carregar_json(ARQUIVO_JSON)
        falhas = extrair_falhas(dados)
        exibir_resumo_terminal(falhas)

    except Exception as e:
        print(f"Erro ao processar relatório: {e}")