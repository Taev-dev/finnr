from __future__ import annotations

from finnr.currency import CurrencySet
from finnr.iso import mint


class TestMint:
    """Performs a few spot checks on the codegen'd iso module.
    """

    def test_is_currency_set(self):
        """The ISO mint must be a currency set instance."""
        assert isinstance(mint, CurrencySet)

    def test_eur(self):
        """EUR must be retrievable by both its alpha and numeric codes.
        """
        eur_alpha = mint.get(code='EUR')
        eur_num = mint.get(code=978)

        assert eur_alpha is eur_num
        assert eur_alpha is not None
        assert isinstance(eur_alpha.name, str)
        assert 'euro' in eur_alpha.name.lower()
        assert eur_alpha.minor_unit_denominator == 100

    def test_usd(self):
        """USD must be retrievable by both its alpha and numeric codes.
        """
        usd_alpha = mint.get(code='USD')
        usd_num = mint.get(code=840)

        assert usd_alpha is usd_num
        assert usd_alpha is not None
        assert isinstance(usd_alpha.name, str)
        assert 'dollar' in usd_alpha.name.lower()
        assert usd_alpha.minor_unit_denominator == 100
