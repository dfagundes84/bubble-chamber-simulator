import pytest

from bcs import particles as pdb
from bcs.reactions import CASCADE_REACTIONS


@pytest.mark.parametrize("reaction", CASCADE_REACTIONS, ids=lambda r: r.id)
def test_cascade_reaction_conserves_quantum_numbers(reaction):
    beam, target = pdb.get(reaction.beam), pdb.get(reaction.target)
    products = [pdb.get(s) for s in reaction.products]

    dQ = (beam.charge + target.charge) - sum(p.charge for p in products)
    dB = (beam.baryon_number + target.baryon_number) - sum(p.baryon_number for p in products)
    dS = (beam.strangeness + target.strangeness) - sum(p.strangeness for p in products)

    assert dQ == 0, f"{reaction.label}: carga não conservada"
    assert dB == 0, f"{reaction.label}: número bariônico não conservado"
    assert dS == 0, f"{reaction.label}: estranheza não conservada (interação forte)"


@pytest.mark.parametrize("particle", pdb.PARTICLES.values(), ids=lambda p: p.symbol)
def test_decay_channels_conserve_charge_and_baryon_number(particle):
    for channel in particle.decays:
        daughters = [pdb.get(s) for s in channel.daughters]
        dQ = particle.charge - sum(d.charge for d in daughters)
        dB = particle.baryon_number - sum(d.baryon_number for d in daughters)
        assert dQ == 0, f"{particle.symbol} -> {channel.daughters}: carga não conservada"
        assert dB == 0, f"{particle.symbol} -> {channel.daughters}: número bariônico não conservado"


@pytest.mark.parametrize("particle", pdb.PARTICLES.values(), ids=lambda p: p.symbol)
def test_branching_ratios_sum_close_to_one(particle):
    # canais muito raros (< ~1%) foram deliberadamente omitidos da tabela
    # (ver bcs/particles.py); a amostragem em bcs/event.py normaliza pela
    # soma real, então uma pequena folga aqui é esperada e inofensiva.
    if not particle.decays:
        return
    total = sum(ch.branching_ratio for ch in particle.decays)
    assert total == pytest.approx(1.0, abs=0.01)


@pytest.mark.parametrize("particle", pdb.PARTICLES.values(), ids=lambda p: p.symbol)
def test_decay_is_kinematically_allowed(particle):
    for channel in particle.decays:
        if not channel.daughters:
            continue
        daughter_mass_sum = sum(pdb.get(s).mass_mev for s in channel.daughters)
        assert daughter_mass_sum <= particle.mass_mev + 1e-6, (
            f"{particle.symbol} -> {channel.daughters}: soma das massas das filhas "
            f"excede a massa da mãe"
        )
