import hashlib
import io

import httpx
import pypdfium2 as pdfium

from arriera.providers.ocr import OCRAzure, OCRTesseract, detectar_idioma
from tests.conftest import CLAVE, ingresar_con_2fa
from tests.paginas_demo import pagina_con_texto

SOLICITUD = [
    "Solicitud de subsidio por enfermedad",
    "Fondo de ayuda mutua · Expediente 2018-0412",
    "Asociada: Rosa Huamán Quispe (ficticia)",
    "Fecha de la solicitud: 14 de marzo de 2018",
    "Monto solicitado: S/ 1,250.00 para la atención",
    "Adjunta la boleta de pago y el informe del médico",
    "Firma de la asociada y sello de mesa de partes",
    "Sin préstamo pendiente con el fondo",
]
ENGLISH = [
    "Medical certificate for the member",
    "This letter confirms that the patient was seen",
    "at the clinic and that the treatment is ongoing",
    "Please contact the office for any question",
    "The document is part of the demo archive",
]


def test_tesseract_lee_texto_y_detecta_idioma():
    r = OCRTesseract("spa+eng").analizar(pagina_con_texto(SOLICITUD, foto=False))
    assert "subsidio" in r.texto.lower()
    assert r.idioma == "es"
    assert r.confianza and r.confianza > 0.6
    p = next(p for p in r.palabras if p.texto.lower().startswith("subsidio"))
    assert 0 < p.x0 < p.x1 < 1 and 0 < p.y0 < p.y1 < 1
    assert detectar_idioma(" ".join(ENGLISH).lower()) == "en"


def test_azure_contrato_con_respuesta_simulada():
    respuesta = {
        "status": "succeeded",
        "analyzeResult": {
            "content": "Informe médico del asociado",
            "pages": [
                {
                    "width": 1000,
                    "height": 2000,
                    "words": [
                        {
                            "content": "Informe",
                            "polygon": [100, 200, 300, 200, 300, 240, 100, 240],
                            "confidence": 0.99,
                        },
                        {
                            "content": "médico",
                            "polygon": [320, 200, 480, 200, 480, 240, 320, 240],
                            "confidence": 0.9,
                        },
                    ],
                }
            ],
            "languages": [{"locale": "es", "spans": [{"offset": 0, "length": 27}], "confidence": 0.9}],
            "styles": [{"isHandwritten": True, "spans": [{"offset": 8, "length": 6}], "confidence": 0.8}],
        },
    }

    def manejar(req: httpx.Request) -> httpx.Response:
        assert req.headers["Ocp-Apim-Subscription-Key"] == "llave-demo"
        if req.method == "POST":
            assert "prebuilt-read:analyze" in str(req.url)
            return httpx.Response(202, headers={"Operation-Location": "https://azure.demo/op/1"})
        return httpx.Response(200, json=respuesta)

    ocr = OCRAzure("https://azure.demo", "llave-demo", transporte=httpx.MockTransport(manejar))
    r = ocr.analizar(b"jpeg")
    assert r.texto.startswith("Informe") and r.idioma == "es"
    assert r.palabras[0].x0 == 0.1 and r.palabras[0].y1 == 0.12
    assert r.manuscrito == round(6 / 27, 3)
    assert r.costo_usd > 0 and r.proveedor == "azure"


def _subir(c, code, llave, datos):
    return c.post(
        f"/estacion/lotes/{code}/paginas",
        headers={"X-Station-Key": llave},
        files={"archivo": ("p.jpg", datos, "image/jpeg")},
        data={"sha256": hashlib.sha256(datos).hexdigest()},
    )


def test_ocr_busqueda_resaltado_y_pdf_buscable(cliente):
    # Captura: el operador crea un lote y un celular sube dos hojas (español e inglés).
    cliente.post("/auth/login", json={"email": "captura@demo.arriera.tech", "password": CLAVE})
    lote = cliente.post("/captura/lotes", json={"caja": "C-0046"}).json()["code"]
    token = cliente.post(f"/captura/lotes/{lote}/emparejar").json()["url"].split("t=")[1]
    llave = cliente.post("/estacion/emparejar", json={"token": token, "modelo": "Prueba"}).json()["llave"]
    assert _subir(cliente, lote, llave, pagina_con_texto(SOLICITUD)).status_code == 201
    assert _subir(cliente, lote, llave, pagina_con_texto(ENGLISH)).status_code == 201
    det = cliente.get(f"/captura/lotes/{lote}").json()
    assert [p["ocr"] for p in det["paginas"]] == ["ok", "ok"], det
    assert [p["idioma"] for p in det["paginas"]] == ["es", "en"]
    # El operador no busca en el contenido.
    assert cliente.get("/busqueda", params={"q": "subsidio"}).status_code == 403
    cliente.post("/auth/logout")

    # La archivera busca: raíces en español, sin tildes, y palabras en inglés.
    ingresar_con_2fa(cliente, "archivo@demo.arriera.tech")
    r = cliente.get("/busqueda", params={"q": "subsidios", "lote": lote}).json()
    assert r["total"] == 1, r
    res = r["resultados"][0]
    assert res["indice"] == 1 and res["caja"] == "C-0046"
    assert "\x02" in res["fragmento"] and "\x03" in res["fragmento"]
    assert cliente.get("/busqueda", params={"q": "huaman", "lote": lote}).json()["total"] == 1
    # «prestamos» el stemmer lo toma como verbo; el prefijo igual encuentra «préstamo».
    assert cliente.get("/busqueda", params={"q": "prestamos", "lote": lote}).json()["total"] == 1
    r_en = cliente.get("/busqueda", params={"q": "certificate", "lote": lote}).json()
    assert r_en["total"] == 1 and r_en["resultados"][0]["idioma"] == "en"
    assert {f["valor"] for f in r_en["facetas"]["idiomas"]} == {"en"}

    # Visor: la palabra buscada vuelve con su caja para resaltarla.
    v = cliente.get(f"/busqueda/paginas/{res['pagina_id']}", params={"q": "subsidio"}).json()
    assert len(v["resaltes"]) >= 1 and "Solicitud" in v["texto"]
    assert cliente.get(f"/busqueda/paginas/{res['pagina_id']}/imagen").content[:2] == b"\xff\xd8"

    # PDF buscable: el texto se puede extraer del PDF.
    pdf = cliente.get(f"/captura/lotes/{lote}/buscable.pdf")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    doc = pdfium.PdfDocument(io.BytesIO(pdf.content))
    assert len(doc) == 2
    assert "subsidio" in doc[0].get_textpage().get_text_range().lower()

    # Costo medido por mil páginas.
    s = cliente.get("/procesamiento/resumen").json()
    tess = next(p for p in s["proveedores"] if p["proveedor"] == "tesseract")
    assert tess["paginas"] >= 2 and tess["usd_por_mil"] == 0


def test_auditoria_no_ve_contenido(cliente):
    ingresar_con_2fa(cliente, "auditoria@demo.arriera.tech")
    assert cliente.get("/busqueda", params={"q": "subsidio"}).status_code == 403
