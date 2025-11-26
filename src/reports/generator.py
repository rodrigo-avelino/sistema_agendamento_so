import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from src.config.settings import RELATORIOS_DIR

def gerar_relatorio_pdf(consultas: list, medicos: list) -> str:
    """
    [SO - OPERAÇÃO DE I/O BINÁRIA]
    Gera um arquivo PDF escrevendo bytes diretamente em um stream.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"relatorio_consultas_{timestamp}.pdf"
    filepath = os.path.join(RELATORIOS_DIR, filename)

    # [SO - BUFFER DE MEMÓRIA]
    # O canvas funciona como um buffer em memória RAM onde desenhamos o documento.
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # ... (Lógica de desenho do PDF) ...
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Relatório do Sistema - {timestamp}")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Total de Consultas Agendadas: {len(consultas)}")
    c.line(50, height - 80, width - 50, height - 80)

    y = height - 100
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "DATA/HORA")
    c.drawString(200, y, "MÉDICO")
    c.drawString(400, y, "PACIENTE")
    
    y -= 20
    c.setFont("Helvetica", 10)

    mapa_medicos = {m['id']: m['nome'] for m in medicos}

    for consulta in consultas:
        if y < 50:
            c.showPage() # Paginação (Gerenciamento de Buffer)
            y = height - 50
        
        data_fmt = consulta['data_hora'].replace("T", " ")
        nome_medico = mapa_medicos.get(consulta['medico_id'], f"ID {consulta['medico_id']}")
        
        c.drawString(50, y, data_fmt)
        c.drawString(200, y, f"Dr(a). {nome_medico}")
        c.drawString(400, y, consulta.get('paciente', 'N/A'))
        y -= 15

    # [SO - FLUSH TO DISK]
    # O método save() realiza a descarga (flush) do buffer da memória para o disco físico.
    c.save()
    
    return filename