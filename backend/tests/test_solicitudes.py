"""Importación de PDF ya digitales y solicitudes de copia con ocultamiento real (DATOS DEMO)."""

import io

import pypdfium2 as pdfium
from PIL import Image
from reportlab.pdfgen import canvas

from arriera.procesamiento import documentos as proc
from arriera.providers.llm import LLMAnthropic
from tests import ia_simulada
from tests.paginas_demo import pagina_con_texto
from tests.test_documentos import INFORME, SOLICITUD, SOLICITUD_2
from tests.test_microformas import _entrar


def _pdf_de(paginas: list[bytes]) -> bytes:
    """PDF escaneado de prueba: cada página es una imagen (como lo exporta otro gestor o un escáner)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for jpeg in paginas:
        im = Image.open(io.BytesIO(jpeg))
        c.setPageSize((595, 595 * im.height / im.width))
        from reportlab.lib.utils import ImageReader

        c.drawImage(ImageReader(io.BytesIO(jpeg)), 0, 0, 595, 595 * im.height / im.width)
        c.showPage()
    c.save()
    return buf.getvalue()


def test_importa_pdf_y_atiende_una_solicitud_con_ocultamiento(cliente, monkeypatch):
    monkeypatch.setattr(proc, "proveedor_llm", lambda: LLMAnthropic("k-demo", transporte=ia_simulada.transporte()))
    c = cliente
    _entrar(c, "captura@demo.arriera.tech")
    code = c.post("/captura/lotes", json={"caja": "C-0046", "origen": "importacion"}).json()["code"]
    pdf = _pdf_de([pagina_con_texto(SOLICITUD), pagina_con_texto(SOLICITUD_2), pagina_con_texto(INFORME)])

    r = c.post(f"/captura/lotes/{code}/importar", files={"archivo": ("expediente.pdf", pdf, "application/pdf")})
    assert r.status_code == 201, r.text
    assert r.json()["paginas"] == [1, 2, 3]
    # El mismo PDF otra vez no duplica páginas.
    r = c.post(f"/captura/lotes/{code}/importar", files={"archivo": ("copia.pdf", pdf, "application/pdf")})
    assert r.json()["duplicado"] is True
    # Un archivo que no es PDF ni imagen se rechaza con un mensaje claro.
    r = c.post(f"/captura/lotes/{code}/importar", files={"archivo": ("x.txt", b"hola", "text/plain")})
    assert r.status_code == 415
    lote = c.get(f"/captura/lotes/{code}").json()
    assert lote["recibidas"] == 3 and lote["estado"] in ("procesado", "procesando")
    assert c.post(f"/captura/lotes/{code}/cerrar").status_code == 200
    lote = c.get(f"/captura/lotes/{code}").json()
    assert lote["ia"]["estado"] == "listo" and lote["ia"]["documentos"] == 2

    # Archivo recibe una solicitud de copia de historia clínica de la asociada (por DNI).
    _entrar(c, "archivo@demo.arriera.tech")
    tipos = c.get("/solicitudes/tipos").json()
    assert {t["key"] for t in tipos["tipos"]} == {"copia", "copia_hc", "acceso_datos", "constancia"}
    r = c.post(
        "/solicitudes",
        json={
            "tipo": "copia_hc",
            "solicitante": "Rosa Huamán Quispe",
            "documento": "41234518",
            "relacion": "titular",
        },
    )
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["numero"].startswith("S-") and s["estado"] == "recibida" and s["documento"].endswith("518")
    assert "41234518" not in r.text  # el DNI no vuelve completo
    assert s["dias_habiles"] == tipos["tipos"][1]["plazo_dias"]
    # Sugiere los documentos de la misma persona por su DNI.
    assert len(s["sugeridos"]) >= 1
    informe = next(d for d in c.get("/documentos", params={"lote": code}).json() if d["tipo"] == "informe_medico")
    sol = next(d for d in s["sugeridos"] if d["tipo"] == "solicitud_subsidio")
    # Búsqueda de documentos por DNI exacto.
    assert any(d["id"] == sol["id"] for d in c.get("/documentos", params={"q": "41234518"}).json())

    for did in (sol["id"], informe["id"]):
        s = c.post(f"/solicitudes/{s['id']}/documentos", json={"documento_id": did}).json()
    assert s["estado"] == "en_busqueda" and len(s["items"]) == 2
    assert c.post(f"/solicitudes/{s['id']}/estado", json={"estado": "entregada"}).status_code == 409

    s = c.post(f"/solicitudes/{s['id']}/copia", json={"ocultamiento": "dni_y_sensibles"}).json()
    assert s["estado"] == "lista" and s["copia"]["paginas"] == 3 and len(s["copia"]["sha256"]) == 64
    r = c.get(f"/solicitudes/{s['id']}/copia.pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    doc = pdfium.PdfDocument(r.content)
    assert len(doc) == 3
    # Ocultamiento real: el PDF no tiene capa de texto; ni el DNI ni el diagnóstico se pueden extraer.
    texto = "".join(doc[i].get_textpage().get_text_bounded() for i in range(len(doc)))
    assert "41234518" not in texto and "lumbalgia" not in texto
    # Y sobre la imagen hay una caja negra donde estaba el DNI.
    img = doc[0].render(scale=1).to_pil().convert("L")
    assert min(img.getdata()) == 0

    s = c.post(
        f"/solicitudes/{s['id']}/estado", json={"estado": "entregada", "nota": "Entregada en mesa de partes"}
    ).json()
    assert s["estado"] == "entregada" and s["dias_habiles"] is None
    assert [h["accion"] for h in s["historial"]][:1] == ["recibida"]
    assert c.post(f"/solicitudes/{s['id']}/documentos", json={"documento_id": informe["id"]}).status_code == 409

    # La copia de un documento N3 aparece en el panel de accesos a datos sensibles.
    _entrar(c, "auditoria@demo.arriera.tech")
    panel = c.get("/cumplimiento/accesos-sensibles").json()
    assert any(a["accion"] == "Emitió una copia" for a in panel["accesos"])
    # El rol de consulta no atiende solicitudes.
    _entrar(c, "validacion@demo.arriera.tech")
    assert c.get("/solicitudes").status_code == 403
