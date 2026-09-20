import pytest

from bcs import bethe_bloch as bb
from bcs.materials import MATERIALS


@pytest.mark.parametrize("material_key", list(MATERIALS.keys()))
def test_minimum_ionization_near_beta_gamma_3_to_4(material_key):
    material = MATERIALS[material_key]
    curve = bb.dedx_curve(material, beta_gamma_min=0.3, beta_gamma_max=1000, n_points=400)
    i_min = min(range(len(curve["dedx_mev_cm2_g"])), key=lambda i: curve["dedx_mev_cm2_g"][i])
    bg_min = curve["beta_gamma"][i_min]
    assert 2.0 <= bg_min <= 6.0, f"{material_key}: mínimo de ionização fora do esperado (βγ={bg_min:.2f})"


def test_h2_liquid_minimum_is_about_4_MeV_cm2_g():
    # Compatível com a Figura 3 do artigo (H2 líquido: mínimo ~ 4 MeV cm^2/g)
    material = MATERIALS["h2_liquid"]
    curve = bb.dedx_curve(material, 0.3, 1000, 400)
    dedx_min = min(curve["dedx_mev_cm2_g"])
    assert dedx_min == pytest.approx(4.0, rel=0.15)


def test_dedx_decreases_then_increases_with_beta_gamma():
    material = MATERIALS["h2_liquid"]
    curve = bb.dedx_curve(material, 0.3, 1000, 200)
    ys = curve["dedx_mev_cm2_g"]
    i_min = min(range(len(ys)), key=lambda i: ys[i])
    assert ys[0] > ys[i_min]        # cai antes do minimo
    assert ys[-1] > ys[i_min]       # sobe depois do minimo (regime relativistico)


def test_heavier_z_over_a_like_lead_has_lower_mass_stopping_power_at_minimum():
    # Pb tem Z/A menor que H2 -> poder de freamento MASSICO menor no minimo
    # (Figura 3 do artigo: a curva do Pb fica abaixo da do H2 liquido)
    h2 = bb.mass_stopping_power(3.5, 938.272, MATERIALS["h2_liquid"])
    pb = bb.mass_stopping_power(3.5, 938.272, MATERIALS["lead"])
    assert pb < h2
