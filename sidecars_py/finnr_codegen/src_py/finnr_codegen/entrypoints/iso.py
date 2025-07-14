from __future__ import annotations

from templatey import RenderEnvironment
from templatey.prebaked.loaders import CompanionFileLoader

from finnr_codegen._types import REPO_ROOT
from finnr_codegen.data_fusion import fuse_src_data
from finnr_codegen.templates import CurrencyTemplate
from finnr_codegen.templates import IsoCurrenciesModuleTemplate

templatey_loader = CompanionFileLoader()
templatey_env = RenderEnvironment(
    env_functions=(),
    template_loader=templatey_loader)


def codegen_iso_module():
    dest_path = REPO_ROOT / 'src_py/finnr/iso.py'

    unsorted_src_data = fuse_src_data()
    sorted_alpha3s = sorted(unsorted_src_data)
    sorted_currencies = [
        unsorted_src_data[alpha3] for alpha3 in sorted_alpha3s]

    module_text = templatey_env.render_sync(
        IsoCurrenciesModuleTemplate(
            currencies=[
                CurrencyTemplate.from_currency(currency)
                for currency in sorted_currencies]))

    dest_path.write_text(module_text, encoding='utf-8')


if __name__ == '__main__':
    codegen_iso_module()
