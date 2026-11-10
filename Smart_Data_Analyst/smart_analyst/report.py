
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from xml.sax.saxutils import escape
from .core import profile,insights
def pdf_report(df,name):
    p=profile(df); b=BytesIO(); doc=SimpleDocTemplate(b,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm)
    s=getSampleStyleSheet(); s.add(ParagraphStyle(name="HeroX",parent=s["Title"],textColor=colors.HexColor("#263B70"),fontSize=23,leading=28))
    story=[Paragraph("SMART DATA ANALYST",s["HeroX"]),Paragraph("Automated exploratory analysis · "+escape(str(name)),s["Normal"]),Spacer(1,12),Paragraph("Dataset overview",s["Heading2"])]
    rows=[["Metric","Value"],["Rows",f"{p['rows']:,}"],["Columns",str(p["columns"])],["Missing cells",f"{p['missing']:,} ({p['missing_pct']}%)"],["Duplicate rows",str(p["duplicates"])],["Quality index",f"{p['quality']}/100 (project heuristic)"]]
    t=Table(rows,colWidths=[65*mm,75*mm]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#263B70")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.lightgrey),("PADDING",(0,0),(-1,-1),7)])); story += [t,Spacer(1,12),Paragraph("Automated observations",s["Heading2"])]
    for level,title,body in insights(df,p): story += [Paragraph("<b>"+escape(title)+"</b><br/>"+escape(body),s["BodyText"]),Spacer(1,7)]
    story += [Spacer(1,8),Paragraph("Column profile",s["Heading2"])]
    tab=[["Column","Type","Missing %","Unique"]]+[[str(x["Column"])[:27],x["Type"],str(x["Missing %"]),str(x["Unique"])] for x in p["schema"][:45]]
    t=Table(tab,repeatRows=1,colWidths=[65*mm,32*mm,28*mm,25*mm]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#263B70")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.3,colors.lightgrey),("FONTSIZE",(0,0),(-1,-1),8),("PADDING",(0,0),(-1,-1),5)])); story.append(t)
    story += [Spacer(1,12),Paragraph("Interpretation note",s["Heading2"]),Paragraph("This is an automated exploratory summary. Patterns are descriptive, not causal. Review inferred types and domain-specific validity before making decisions.",s["BodyText"])]
    doc.build(story); return b.getvalue()
