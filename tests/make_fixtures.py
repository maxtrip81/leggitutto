"""Crea documenti di prova (con intestazioni, numeri di pagina e note) usando LibreOffice."""

import subprocess
import sys
from pathlib import Path

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "fixtures")
OUT.mkdir(parents=True, exist_ok=True)

LOREM = ("Il viaggio di Marco cominciò in una mattina di nebbia, quando la città era ancora "
         "addormentata e le strade sembravano disegnate a matita. Portava con sé una valigia "
         "leggera e un quaderno pieno di appunti, scritti con una grafia minuta e ostinata. ")

paras = []
for chapter in range(1, 4):
    paras.append(f'<text:h text:outline-level="1">Capitolo {chapter}. La partenza numero {chapter}</text:h>')
    for i in range(9):
        note = ""
        if i % 3 == 1:
            note = (f'<text:note text:id="n{chapter}{i}" text:note-class="footnote"><text:note-citation>{chapter}{i}</text:note-citation>'
                    f'<text:note-body><text:p text:style-name="Footnote">Questa è una nota a piè di pagina del capitolo {chapter}, paragrafo {i}.</text:p></text:note-body></text:note>')
        paras.append(f'<text:p text:style-name="Standard">{LOREM * 2}Fine del paragrafo {chapter}.{i}{note} e ultima frase del paragrafo.</text:p>')
    paras.append('<table:table table:name="T"><table:table-column table:number-columns-repeated="2"/>'
                 '<table:table-row><table:table-cell><text:p>Città</text:p></table:table-cell><table:table-cell><text:p>Abitanti</text:p></table:table-cell></table:table-row>'
                 '<table:table-row><table:table-cell><text:p>Roma</text:p></table:table-cell><table:table-cell><text:p>2.700.000</text:p></table:table-cell></table:table-row>'
                 '<table:table-row><table:table-cell><text:p>Milano</text:p></table:table-cell><table:table-cell><text:p>1.300.000</text:p></table:table-cell></table:table-row>'
                 '</table:table>')

FODT = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
<office:styles>
 <style:style style:name="Standard" style:family="paragraph"><style:paragraph-properties fo:text-align="justify" fo:text-indent="0.5cm"/><style:text-properties fo:font-size="12pt"/></style:style>
 <style:style style:name="Footnote" style:family="paragraph"><style:text-properties fo:font-size="9pt"/></style:style>
</office:styles>
<office:automatic-styles>
 <style:page-layout style:name="pm1"><style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" fo:margin-top="1.5cm" fo:margin-bottom="1.5cm" fo:margin-left="2.5cm" fo:margin-right="2.5cm"/>
 <style:header-style><style:header-footer-properties fo:min-height="0.6cm" fo:margin-bottom="0.5cm"/></style:header-style>
 <style:footer-style><style:header-footer-properties fo:min-height="0.6cm" fo:margin-top="0.5cm"/></style:footer-style></style:page-layout>
</office:automatic-styles>
<office:master-styles><style:master-page style:name="Standard" style:page-layout-name="pm1">
 <style:header><text:p>Il romanzo di prova — Editore Immaginario</text:p></style:header>
 <style:footer><text:p>Pagina <text:page-number text:select-page="current">1</text:page-number> di <text:page-count>9</text:page-count></text:p></style:footer>
</style:master-page></office:master-styles>
<office:body><office:text>
<text:h text:outline-level="1">Il romanzo di prova</text:h>
<text:list><text:list-item><text:p>Primo punto dell'elenco</text:p></text:list-item><text:list-item><text:p>Secondo punto dell'elenco</text:p></text:list-item></text:list>
{"".join(paras)}
</office:text></office:body></office:document>'''

src = OUT / "romanzo.fodt"
src.write_text(FODT, encoding="utf-8")
for fmt in ["pdf", "docx", "odt", "rtf", "doc", "epub", "html", "pptx:Impress MS PowerPoint 2007 XML"]:
    if fmt.startswith("pptx"):
        continue
    subprocess.run(["soffice", "--headless", "--convert-to", fmt, "--outdir", str(OUT), str(src)], capture_output=True, timeout=180)
print(sorted(p.name for p in OUT.iterdir()))
