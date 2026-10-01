from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    source_id: str
    title: str
    publisher: str
    landing_page: str
    geography: str
    native_frequency: str
    caveat: str


SOURCES = {
    "isp_rj_municipal": Source(
        source_id="isp_rj_municipal",
        title="Estatísticas de Segurança Pública — série mensal municipal",
        publisher="Instituto de Segurança Pública do Estado do Rio de Janeiro (ISP-RJ)",
        landing_page="https://www.ispdados.rj.gov.br/estatistica.html",
        geography="Municípios do estado do Rio de Janeiro",
        native_frequency="Mensal",
        caveat=(
            "Registros administrativos policiais. A contagem depende do registro, classificação e "
            "revisão policial; não mede toda a incidência criminal. Não generalizar ao Brasil."
        ),
    ),
    "isp_rj_femicide_cisp": Source(
        source_id="isp_rj_femicide_cisp",
        title="Feminicídio — série mensal por circunscrição policial",
        publisher="Instituto de Segurança Pública do Estado do Rio de Janeiro (ISP-RJ)",
        landing_page="https://www.ispdados.rj.gov.br/CrimesVida.html",
        geography="Município × CISP (circunscrição integrada de segurança pública), RJ",
        native_frequency="Mensal",
        caveat=(
            "A unidade territorial é a CISP no município informado pelo ISP; não é a coordenada do "
            "fato nem necessariamente comparável a limites de outras fontes. "
            "Registros podem ser revistos."
        ),
    ),
}
